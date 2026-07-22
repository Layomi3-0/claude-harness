"""Ask-and-resume: let a blocked implementor ask the requester on the issue.

The pipeline is headless — each node is a one-shot `claude -p` with nobody on the
other end. Before this module, an implementor that hit a genuinely human-only
decision would ask its question into the void; the pipeline read the question as
the node's final output, logged "implementation complete", validated an empty
diff (trivially green), and opened a spec-only PR. Real case: issue #357 / PR #358.

The contract now:

  1. /implement instructs the agent: if blocked on a human-only decision, end
     with a line `ADW_QUESTION: <question>` (see commands/implement.md).
  2. The pipeline detects that sentinel, posts the question as a comment on the
     issue, saves `runs/<adw_id>/state.json` with phase "awaiting_answer", keeps
     the worktree, and exits cleanly (label: adw-waiting).
  3. The requester replies in a normal comment, then comments the trigger phrase.
  4. The triggered run finds the saved state for its issue, re-attaches to the
     same worktree/branch, folds the reply into the plan file (committed, so the
     spec records the decision), and continues implement -> validate -> PR.

State lives in the run dir (git-excluded with the rest of .claude/), one file per
asking run; a later resume marks it "resumed" so stale states can't re-trigger.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from utils import adw_home, run_dir

QUESTION_SENTINEL = "ADW_QUESTION:"

# An ADW progress comment: "`a1b2c3d4` **agent** — message" (github.format_comment).
_ADW_COMMENT_RE = re.compile(r"^`[0-9a-f]{8}` \*\*\w+\*\*")

_AWAITING = "awaiting_answer"


def extract_question(output: str) -> Optional[str]:
    """The implementor's blocking question, or None if it implemented.

    Everything from the FIRST sentinel to the end counts as the question — models
    asked for "one clear question" still write multi-line ones, and truncating at
    a newline would post half a question to the issue.
    """
    idx = output.find(QUESTION_SENTINEL)
    if idx == -1:
        return None
    question = output[idx + len(QUESTION_SENTINEL):].strip()
    return question or None


# ── state files ──────────────────────────────────────────────────────────────
def _state_file(adw_id: str) -> Path:
    return run_dir(adw_id) / "state.json"


def save_awaiting(
    adw_id: str,
    issue_number: int,
    issue_class: str,
    branch: str,
    plan_file: str,
    worktree: str,
    question: str,
) -> None:
    _state_file(adw_id).write_text(
        json.dumps(
            {
                "adw_id": adw_id,
                "issue": issue_number,
                "issue_class": issue_class,
                "branch": branch,
                "plan_file": plan_file,
                "worktree": worktree,
                "question": question,
                "phase": _AWAITING,
                "asked_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )


def find_awaiting(issue_number: int) -> Optional[dict]:
    """Newest awaiting-answer state for this issue, across all runs. Newest wins
    so a re-ask (a resumed run that asked a second question) supersedes the first."""
    runs = adw_home() / "runs"
    if not runs.is_dir():
        return None
    states = []
    for f in runs.glob("*/state.json"):
        try:
            state = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if state.get("issue") == issue_number and state.get("phase") == _AWAITING:
            states.append(state)
    if not states:
        return None
    return max(states, key=lambda s: s.get("asked_at", ""))


def mark_resumed(state: dict, resumed_by: str) -> None:
    state = dict(state, phase="resumed", resumed_by=resumed_by)
    _state_file(state["adw_id"]).write_text(json.dumps(state, indent=2))


# ── answer gathering ─────────────────────────────────────────────────────────
def is_adw_comment(body: str) -> bool:
    return bool(_ADW_COMMENT_RE.match(body.strip()))


def answers_since(
    comments: list,
    asked_at: str,
    is_authorized: Callable[[str], bool],
    trigger_phrase: str,
) -> List[Tuple[str, str]]:
    """(login, body) for every comment that counts as an answer: posted after the
    question, by an allowlisted human, not ADW's own progress format, and not the
    bare trigger phrase (that comment means "resume", it isn't content)."""
    asked = datetime.fromisoformat(asked_at)
    answers: List[Tuple[str, str]] = []
    for comment in comments:
        created = getattr(comment, "created_at", None)
        author = getattr(comment, "author", None)
        login = author.login if author else ""
        body = (comment.body or "").strip()
        if created is None or created <= asked:
            continue
        if not is_authorized(login):
            continue
        if body.lower() == trigger_phrase.lower():
            continue
        if is_adw_comment(body):
            continue
        answers.append((login, body))
    return answers


def decisions_section(question: str, answers: List[Tuple[str, str]], adw_id: str) -> str:
    """Markdown appended to the plan file on resume — the spec then RECORDS the
    requester's decision instead of the repo relying on issue-thread archaeology."""
    lines = [
        "",
        f"## Requester decisions (ADW resume `{adw_id}`)",
        "",
        f"**The implementor asked:** {question}",
        "",
    ]
    for login, body in answers:
        lines.append(f"**@{login} answered:** {body}")
        lines.append("")
    lines.append("Implement according to these answers; they override any conflicting")
    lines.append("assumption elsewhere in this plan.")
    lines.append("")
    return "\n".join(lines)
