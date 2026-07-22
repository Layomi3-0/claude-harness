#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["python-dotenv", "pydantic"]
# ///
"""ADW pipeline: GitHub issue -> classify -> plan -> implement -> validate -> PR.

Usage: uv run adw_run.py <issue-number> [adw-id]

Each node is a fresh `claude -p` process. Progress is reported back to the issue
thread, which doubles as the run log for unattended runs.

The validation gate is the point of departure from tac-4: a PR is only opened if
/validate returns PASS. A failing run stops, says so on the issue, and leaves the
branch pushed for a human — rather than opening a PR whose plan claims "zero
regressions" that nothing ever checked.
"""

import os
import subprocess
import sys
from typing import Optional, Tuple

import git_ops
from agent import run_template
from config import config
from data_types import AgentTemplateRequest, GitHubIssue, IssueClass, ValidationResult
from github import add_label, comment_on_issue, fetch_issue, format_comment
from utils import make_adw_id, setup_logger

VALID_CLASSES = {"/plan_chore", "/plan_bug", "/plan_feature"}
SPECS_DIR = "specs"


def parse_verdict(raw: str) -> ValidationResult:
    """Extract PASS/FAIL from the validator's reply.

    The prompt asks for a single bare line, but models reliably add a summary
    sentence or a code fence anyway. Treating that as unparseable produces a FALSE
    NEGATIVE — a clean run reported as failed, with no PR — so the parser scans
    instead of assuming a shape.

    Scans from the END because a decisive verdict comes last when there is preamble.
    Only a line that IS the verdict counts; prose merely containing the word "pass"
    does not. Anything genuinely undecidable stays FAIL, since silently assuming
    success would defeat the gate.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(
            line for line in text.splitlines() if not line.strip().startswith("```")
        )

    lines = [line.strip().strip("*`") for line in text.splitlines() if line.strip()]

    for line in reversed(lines):
        head, _, detail = line.partition(":")
        head = head.strip().upper()
        if head == "PASS":
            return ValidationResult(verdict="PASS", detail=detail.strip())
        if head == "FAIL":
            return ValidationResult(verdict="FAIL", detail=detail.strip() or line)

    return ValidationResult(verdict="FAIL", detail=f"unparseable verdict: {raw[:300]}")


class Pipeline:
    def __init__(self, issue_number: int, adw_id: str):
        self.issue_number = issue_number
        self.adw_id = adw_id
        self.logger = setup_logger(adw_id, "adw_run")
        self.issue: Optional[GitHubIssue] = None

    # ── reporting ────────────────────────────────────────────────────────────
    def say(self, agent: str, message: str) -> None:
        self.logger.info(message)
        comment_on_issue(self.issue_number, format_comment(self.adw_id, agent, message))

    def abort(self, agent: str, message: str) -> None:
        # A failed run's worktree is kept deliberately — it is the only place a
        # human can inspect what the agent actually left behind.
        worktree = git_ops.active_worktree()
        if worktree:
            message += (
                f"\n\nWorktree kept for inspection: `{worktree}` "
                f"(remove with `git worktree remove --force {worktree}`)"
            )
        self.logger.error(message)
        comment_on_issue(self.issue_number, format_comment(self.adw_id, agent, f"❌ {message}"))
        sys.exit(1)

    def call(self, agent: str, command: str, args: list) -> str:
        request = AgentTemplateRequest(
            agent_name=agent, slash_command=command, args=args,
            adw_id=self.adw_id, model=config.model,
            working_dir=str(worktree) if (worktree := git_ops.active_worktree()) else None,
        )
        response = run_template(request, self.logger)
        if not response.success:
            self.abort(agent, f"{command} failed: {response.output[:500]}")
        return response.output.strip()

    # ── nodes ────────────────────────────────────────────────────────────────
    def authorize(self) -> None:
        """Defence in depth — the trigger checks this too, but adw_run is also
        runnable by hand, and an unauthorized manual run is still unsupervised tool
        use on this machine."""
        author = self.issue.author.login
        if not config.is_authorized(author):
            self.abort(
                "ops",
                f"@{author} is not in ADW_ALLOWED_AUTHORS — refusing to run. "
                "Add them to .claude/adw/adw.env if this is intended.",
            )
        self.logger.info(f"Authorized author: @{author}")

    def classify(self) -> IssueClass:
        raw = self.call("classifier", "/classify_issue", [self.issue.as_prompt()])
        command = raw.split()[0] if raw else ""
        if command not in VALID_CLASSES:
            self.abort("classifier", f"Could not classify issue (got: {raw[:200]!r})")
        self.say("classifier", f"✅ Classified as `{command}`")
        return command

    def worktree(self, issue_class: str) -> str:
        """Every run gets its own worktree cut from freshly-fetched origin/<base>,
        so runs never touch the user's checkout and can overlap with each other."""
        name = git_ops.branch_name(issue_class, self.issue_number, self.adw_id, self.issue.title)
        ok, detail = git_ops.create_worktree(name, self.adw_id)
        if not ok:
            self.abort("ops", detail)
        self.say(
            "ops",
            f"✅ Working on branch `{name}` in an isolated worktree "
            f"(`{detail}`, cut from fresh `origin/{git_ops.default_branch()}`)",
        )
        return name

    def setup_workspace(self) -> None:
        """A fresh worktree has nothing git-ignored: no node_modules, no build
        outputs. Without this step /validate fails on missing dependencies and the
        gate reports a false negative. The command is repo-specific, so it comes
        from ADW_WORKTREE_SETUP in adw.env; blank skips."""
        if not config.worktree_setup:
            return
        self.say("ops", f"📦 Preparing worktree: `{config.worktree_setup}`")
        env = os.environ.copy()
        # This repo's .npmrc resolves ${GITHUB_TOKEN} for the private registry.
        # Fall back to the configured PAT when launched from an env without it.
        if config.github_pat and not env.get("GITHUB_TOKEN"):
            env["GITHUB_TOKEN"] = config.github_pat
        try:
            result = subprocess.run(
                config.worktree_setup, shell=True, cwd=git_ops.workdir(),
                capture_output=True, text=True, env=env, timeout=1200,
            )
        except subprocess.TimeoutExpired:
            self.abort("ops", f"Worktree setup timed out after 20m: `{config.worktree_setup}`")
        if result.returncode != 0:
            self.abort(
                "ops",
                f"Worktree setup failed (`{config.worktree_setup}`):\n"
                f"```\n{(result.stderr or result.stdout)[-1200:]}\n```",
            )

    def plan(self, issue_class: str) -> str:
        # Snapshot first: the repo may already hold uncommitted specs from earlier
        # work, and only the file this run creates may be handed to /implement.
        before = git_ops.list_specs(SPECS_DIR)
        self.say("planner", "🧠 Building the plan…")
        self.call("planner", issue_class, [self.issue.as_prompt()])

        specs = git_ops.newly_created(before, git_ops.list_specs(SPECS_DIR))
        if not specs:
            self.abort(
                "planner",
                f"No new plan file appeared in {SPECS_DIR}/ — the planner reported "
                f"success but wrote nothing. See runs/{self.adw_id}/planner/.",
            )
        if len(specs) > 1:
            self.logger.warning(f"Multiple new specs {specs}; using {specs[0]}")

        plan_file = specs[0]
        self.say("planner", f"✅ Plan written: `{plan_file}`")
        git_ops.commit_all(f"docs: add plan for #{self.issue_number}\n\nADW-ID: {self.adw_id}")
        return plan_file

    def implement(self, plan_file: str) -> None:
        self.say("implementor", "🔨 Implementing the plan…")
        self.call("implementor", "/implement", [plan_file])
        if not git_ops.has_changes():
            self.logger.warning("Implementation produced no file changes")
        self.say("implementor", "✅ Implementation complete")

    def validate(self) -> ValidationResult:
        """The gate. /validate should answer PASS or FAIL:<reason>."""
        self.say("validator", "🧪 Running validation…")
        return parse_verdict(self.call("validator", "/validate", []))

    def open_pr(self, issue_class: str, branch: str, plan_file: str) -> Optional[str]:
        kind = git_ops.TYPE_BY_CLASS.get(issue_class, "chore")
        title = f"{kind}: #{self.issue_number} — {self.issue.title}"
        body = (
            f"Closes #{self.issue_number}\n\n"
            f"## Plan\n`{plan_file}`\n\n"
            f"## Validation\n✅ All validation commands passed (gated by `/validate`).\n\n"
            f"## Changes\n```\n{git_ops.diff_stat()}\n```\n\n"
            f"---\nADW run `{self.adw_id}` · transcripts in `.claude/adw/runs/{self.adw_id}/`\n"
            f"🤖 Generated with [Claude Code](https://claude.com/claude-code)"
        )
        url, detail = git_ops.create_pr(title, body)
        if not url:
            self.abort("ops", f"Could not create PR: {detail}")
        return url

    # ── orchestration ────────────────────────────────────────────────────────
    def run(self) -> None:
        self.issue = fetch_issue(self.issue_number)
        self.authorize()
        self.say("ops", f"🚀 ADW run `{self.adw_id}` starting")
        add_label(self.issue_number, "adw-running")

        issue_class = self.classify()
        branch = self.worktree(issue_class)
        self.setup_workspace()
        plan_file = self.plan(issue_class)
        self.implement(plan_file)

        result = self.validate()
        git_ops.commit_all(
            f"{git_ops.TYPE_BY_CLASS.get(issue_class, 'chore')}: "
            f"{self.issue.title} (#{self.issue_number})\n\nADW-ID: {self.adw_id}"
        )
        pushed, detail = git_ops.push(branch)
        if not pushed:
            self.abort("ops", f"Could not push branch: {detail}")

        if not result.passed:
            self.say(
                "validator",
                f"❌ **Validation failed — no PR opened.**\n\n```\n{result.detail[:1500]}\n```\n\n"
                f"Branch `{branch}` is pushed and the worktree is kept at "
                f"`{git_ops.workdir()}` for inspection. Review it, or comment "
                f"`{config.trigger_phrase}` to retry.",
            )
            add_label(self.issue_number, "adw-failed")
            sys.exit(1)

        self.say("validator", "✅ Validation passed")
        url = self.open_pr(issue_class, branch, plan_file)
        git_ops.remove_worktree()
        self.say("ops", f"🎉 Pull request opened: {url}")


def parse_args() -> Tuple[int, str]:
    if len(sys.argv) < 2:
        print("Usage: uv run adw_run.py <issue-number> [adw-id]", file=sys.stderr)
        sys.exit(1)
    return int(sys.argv[1]), (sys.argv[2] if len(sys.argv) > 2 else make_adw_id())


def main() -> None:
    errors = config.validate()
    if errors:
        print("ADW configuration errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    issue_number, adw_id = parse_args()
    Pipeline(issue_number, adw_id).run()


if __name__ == "__main__":
    main()
