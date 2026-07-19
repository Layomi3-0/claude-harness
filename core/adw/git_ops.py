"""Deterministic git and PR operations.

tac-4 delegates branch naming, commit messages, and locating the new plan file to
agents. Those are mechanical transforms with a single right answer, so here they are
plain code: fewer LLM calls, no parsing of prose, and no flaky step between the ones
that genuinely need judgment.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from utils import repo_root

TYPE_BY_CLASS = {"/plan_chore": "chore", "/plan_bug": "fix", "/plan_feature": "feat"}


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=check, cwd=repo_root()
    )


def slugify(text: str, max_words: int = 6) -> str:
    words = re.sub(r"[^a-z0-9\s-]", "", text.lower()).split()
    return "-".join(words[:max_words]) or "untitled"


def branch_name(issue_class: str, issue_number: int, adw_id: str, title: str) -> str:
    """`{type}-{issue}-{adw_id}-{slug}` — the ADW id embedded so any branch traces
    back to its run transcript."""
    return f"{TYPE_BY_CLASS.get(issue_class, 'chore')}-{issue_number}-{adw_id}-{slugify(title)}"


def default_branch() -> str:
    result = _git("symbolic-ref", "refs/remotes/origin/HEAD", check=False)
    if result.returncode == 0:
        return result.stdout.strip().rsplit("/", 1)[-1]
    return "main"


def create_branch(name: str) -> Tuple[bool, str]:
    base = default_branch()
    for args in (("checkout", base), ("pull", "--ff-only"), ("checkout", "-b", name)):
        result = _git(*args, check=False)
        if result.returncode != 0 and args[0] == "checkout" and "-b" in args:
            return False, f"Could not create branch {name}: {result.stderr}"
    return True, name


def has_changes() -> bool:
    return bool(_git("status", "--porcelain", check=False).stdout.strip())


def list_specs(directory: str) -> set:
    """Every .md file under `directory`, tracked or not, as repo-relative paths.

    Read from the filesystem rather than `git status`, deliberately. Git collapses a
    wholly-untracked directory to a single `?? specs/` entry, so status parsing hands
    back a directory instead of a file — and it cannot distinguish a spec written by
    this run from one that was already sitting there uncommitted.
    """
    base = repo_root() / directory
    if not base.is_dir():
        return set()
    return {str(p.relative_to(repo_root())) for p in base.rglob("*.md")}


def newly_created(before: set, after: set) -> List[str]:
    """Specs that appeared between two snapshots. Sorted for deterministic choice."""
    return sorted(after - before)


def commit_all(message: str) -> Tuple[bool, str]:
    if not has_changes():
        return False, "nothing to commit"
    _git("add", "-A")
    result = _git("commit", "-m", message, check=False)
    if result.returncode != 0:
        return False, result.stderr
    return True, message


def push(branch: str) -> Tuple[bool, str]:
    result = _git("push", "-u", "origin", branch, check=False)
    return result.returncode == 0, result.stderr or "pushed"


def create_pr(title: str, body: str, base: Optional[str] = None) -> Tuple[Optional[str], str]:
    result = subprocess.run(
        ["gh", "pr", "create", "--base", base or default_branch(), "--title", title, "--body", body],
        capture_output=True,
        text=True,
        cwd=repo_root(),
    )
    if result.returncode != 0:
        return None, result.stderr
    return result.stdout.strip().splitlines()[-1], "created"


def diff_stat(base: Optional[str] = None) -> str:
    ref = f"origin/{base or default_branch()}...HEAD"
    return _git("diff", ref, "--stat", check=False).stdout.strip()
