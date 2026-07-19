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
        self.logger.error(message)
        comment_on_issue(self.issue_number, format_comment(self.adw_id, agent, f"❌ {message}"))
        sys.exit(1)

    def call(self, agent: str, command: str, args: list) -> str:
        request = AgentTemplateRequest(
            agent_name=agent, slash_command=command, args=args,
            adw_id=self.adw_id, model=config.model,
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

    def branch(self, issue_class: str) -> str:
        name = git_ops.branch_name(issue_class, self.issue_number, self.adw_id, self.issue.title)
        ok, detail = git_ops.create_branch(name)
        if not ok:
            self.abort("ops", detail)
        self.say("ops", f"✅ Working on branch `{name}`")
        return name

    def plan(self, issue_class: str) -> str:
        self.say("planner", "🧠 Building the plan…")
        self.call("planner", issue_class, [self.issue.as_prompt()])

        specs = git_ops.new_files_in(SPECS_DIR)
        if not specs:
            self.abort("planner", f"No new plan file appeared in {SPECS_DIR}/")
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
        """The gate. /validate returns a bare PASS or FAIL:<reason>."""
        self.say("validator", "🧪 Running validation…")
        raw = self.call("validator", "/validate", [])
        verdict, _, detail = raw.partition(":")
        verdict = verdict.strip().upper()

        if verdict not in {"PASS", "FAIL"}:
            # An unparseable verdict is treated as failure. Assuming PASS here would
            # defeat the entire purpose of having a gate.
            return ValidationResult(verdict="FAIL", detail=f"unparseable verdict: {raw[:300]}")
        return ValidationResult(verdict=verdict, detail=detail.strip())

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
        branch = self.branch(issue_class)
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
                f"Branch `{branch}` is pushed. Review it, or comment "
                f"`{config.trigger_phrase}` to retry.",
            )
            add_label(self.issue_number, "adw-failed")
            sys.exit(1)

        self.say("validator", "✅ Validation passed")
        url = self.open_pr(issue_class, branch, plan_file)
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
