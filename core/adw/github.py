"""GitHub operations via the `gh` CLI.

Repo binding is automatic: everything derives from `git remote get-url origin`, so the
same ADW installation works in any repo without configuration.
"""

import json
import subprocess
import sys
from typing import Optional

from config import config
from data_types import GitHubIssue

ISSUE_FIELDS = "number,title,body,state,author,labels,comments,url,createdAt"


def _gh_env() -> Optional[dict]:
    """Env for gh calls. None means inherit the parent's (uses `gh auth login`)."""
    if not config.github_pat:
        return None
    import os

    return {"GH_TOKEN": config.github_pat, "PATH": os.environ.get("PATH", "")}


def _run_gh(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=check, env=_gh_env())
    except FileNotFoundError:
        print(
            "Error: GitHub CLI (gh) is not installed.\n"
            "  macOS: brew install gh\n"
            "  Linux: https://github.com/cli/cli#installation\n"
            "Then authenticate: gh auth login",
            file=sys.stderr,
        )
        sys.exit(1)


def get_repo_url() -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise ValueError("No git remote 'origin' found — run this inside a git repo with a remote.")
    return result.stdout.strip()


def extract_repo_path(url: str) -> str:
    """owner/repo from either https or ssh remote form."""
    path = url.strip()
    path = path.replace("https://github.com/", "").replace("git@github.com:", "")
    return path.removesuffix(".git")


def repo_path() -> str:
    return extract_repo_path(get_repo_url())


def fetch_issue(issue_number: int | str) -> GitHubIssue:
    result = _run_gh(
        ["gh", "issue", "view", str(issue_number), "-R", repo_path(), "--json", ISSUE_FIELDS],
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return GitHubIssue(**json.loads(result.stdout))


def comment_on_issue(issue_number: int | str, body: str) -> None:
    """Post progress back to the issue thread.

    The issue becomes the run log — the only surface where an unattended run reports
    what it is doing, so failures here are warned about but never fatal.
    """
    result = _run_gh(
        ["gh", "issue", "comment", str(issue_number), "-R", repo_path(), "--body", body],
        check=False,
    )
    if result.returncode != 0:
        print(f"Warning: could not comment on #{issue_number}: {result.stderr}", file=sys.stderr)


def add_label(issue_number: int | str, label: str) -> None:
    """Best-effort label. Silent if the label doesn't exist in the repo."""
    _run_gh(
        ["gh", "issue", "edit", str(issue_number), "-R", repo_path(), "--add-label", label],
        check=False,
    )


def format_comment(adw_id: str, agent: str, message: str) -> str:
    return f"`{adw_id}` **{agent}** — {message}"
