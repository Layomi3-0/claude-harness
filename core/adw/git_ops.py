"""Deterministic git and PR operations.

tac-4 delegates branch naming, commit messages, and locating the new plan file to
agents. Those are mechanical transforms with a single right answer, so here they are
plain code: fewer LLM calls, no parsing of prose, and no flaky step between the ones
that genuinely need judgment.
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from config import config
from utils import repo_root

TYPE_BY_CLASS = {"/plan_chore": "chore", "/plan_bug": "fix", "/plan_feature": "feat"}

# The run's isolated worktree, once created. None means "no worktree yet" —
# before the worktree node, and in tests.
_workdir: Optional[Path] = None


def workdir() -> Path:
    """Where git commands and pipeline agents operate: the run's worktree once
    created, the repo root before that."""
    return _workdir or repo_root()


def active_worktree() -> Optional[Path]:
    return _workdir


def set_workdir(path: Optional[Path]) -> None:
    global _workdir
    _workdir = path


def _git(*args: str, check: bool = True, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=check, cwd=cwd or workdir()
    )


def slugify(text: str, max_words: int = 6) -> str:
    words = re.sub(r"[^a-z0-9\s-]", "", text.lower()).split()
    return "-".join(words[:max_words]) or "untitled"


def branch_name(issue_class: str, issue_number: int, adw_id: str, title: str) -> str:
    """`{prefix}{type}-{issue}-{adw_id}-{slug}` — the ADW id embedded so any branch
    traces back to its run transcript.

    The prefix comes from ADW_BRANCH_PREFIX and is empty by default. Repos that
    require one (`lkupo/`, `team/`) reject a push without it, which would otherwise
    surface as a failed push at the very end of an otherwise successful run.
    """
    kind = TYPE_BY_CLASS.get(issue_class, "chore")
    return f"{config.branch_prefix}{kind}-{issue_number}-{adw_id}-{slugify(title)}"


def default_branch() -> str:
    result = _git("symbolic-ref", "refs/remotes/origin/HEAD", check=False)
    if result.returncode == 0:
        return result.stdout.strip().rsplit("/", 1)[-1]
    return "main"


def worktree_root() -> Path:
    """Parent directory for run worktrees. A SIBLING of the repo, deliberately:
    a full checkout nested inside the working tree would be scanned by Metro,
    watchman, and Turbo, and would tempt `git add -A` accidents."""
    if config.worktree_root:
        return Path(config.worktree_root).expanduser()
    return repo_root().parent / f"{repo_root().name}-adw-worktrees"


# Copied into every fresh worktree. `.claude/` is git-excluded, so a worktree cut
# from origin/<base> has NO slash commands and NO PROJECT.md — and the pipeline's
# agents need both (/implement reads commands, /validate reads PROJECT.md).
HARNESS_FILES = (".claude/commands", ".claude/PROJECT.md")


def _copy_harness_files(worktree: Path) -> None:
    """Copied rather than symlinked, so a run is immune to edits made in the main
    checkout while it is in flight. Never copies .claude/adw — that would hand the
    agent adw.env's secrets."""
    for rel in HARNESS_FILES:
        src, dst = repo_root() / rel, worktree / rel
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)


def create_worktree(branch: str, adw_id: str) -> Tuple[bool, str]:
    """Cut `branch` from freshly-fetched origin/<base> in the run's OWN worktree.

    Replaces the old create_branch, which did `checkout main && pull` in the user's
    working tree — that required a clean tree, moved the user's HEAD out from under
    them, and made concurrent runs impossible. A worktree gives every run an
    isolated copy based on origin/<base>, so the user's checkout (dirty or not)
    can neither block a run nor leak into its PR.

    Every step is still checked: a wrong base is not a warning, it invalidates the
    whole run. The fetch is what makes "fresh" true — origin/<base> without it is
    just whatever this machine last happened to see.
    """
    base = default_branch()
    path = worktree_root() / adw_id
    path.parent.mkdir(parents=True, exist_ok=True)

    steps = (
        ("fetch", "origin", base),
        ("worktree", "prune"),  # clear stale registrations from hand-deleted dirs
        ("worktree", "add", "--no-track", "-b", branch, str(path), f"origin/{base}"),
    )
    for args in steps:
        result = _git(*args, check=False, cwd=repo_root())
        if result.returncode != 0:
            return False, (
                f"`git {' '.join(args)}` failed, so the run would not be based on "
                f"an up-to-date {base}:\n{result.stderr.strip()}"
            )

    _copy_harness_files(path)
    set_workdir(path)
    return True, str(path)


def remove_worktree() -> None:
    """Cleanup after a SUCCESSFUL run. Failed runs keep their worktree on purpose —
    it is the only place a human can inspect exactly what the agent left behind.
    The branch survives removal; it is already pushed."""
    path = _workdir
    if path is None:
        return
    set_workdir(None)
    _git("worktree", "remove", "--force", str(path), check=False, cwd=repo_root())


def has_changes() -> bool:
    return bool(_git("status", "--porcelain", check=False).stdout.strip())


def list_specs(directory: str) -> set:
    """Every .md file under `directory`, tracked or not, as repo-relative paths.

    Read from the filesystem rather than `git status`, deliberately. Git collapses a
    wholly-untracked directory to a single `?? specs/` entry, so status parsing hands
    back a directory instead of a file — and it cannot distinguish a spec written by
    this run from one that was already sitting there uncommitted.
    """
    base = workdir() / directory
    if not base.is_dir():
        return set()
    return {str(p.relative_to(workdir())) for p in base.rglob("*.md")}


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
        cwd=workdir(),
    )
    if result.returncode != 0:
        return None, result.stderr
    return result.stdout.strip().splitlines()[-1], "created"


def diff_stat(base: Optional[str] = None) -> str:
    ref = f"origin/{base or default_branch()}...HEAD"
    return _git("diff", ref, "--stat", check=False).stdout.strip()
