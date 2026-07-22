#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["python-dotenv", "pydantic", "fastapi", "uvicorn"]
# ///
"""Regression tests for the ADW system.

Usage: uv run test_adw.py

Every case below the SECURITY section is a bug that reached a real repository and
broke a real run. They are encoded here so they cannot come back quietly. The unit
tests written before first execution passed while all four of these were live —
which is the argument for running the thing, not just testing it.
"""

import hashlib
import hmac
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import adw_run
import git_ops
import trigger_webhook
from config import AdwConfig

failures: list[str] = []


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  ✅ {label}")
    else:
        print(f"  ❌ {label}: got {actual!r}, expected {expected!r}")
        failures.append(label)


# ── SECURITY GATES ──────────────────────────────────────────────────────────
print("\nauthor allowlist")
cfg = AdwConfig(allowed_authors=["Layomi3-0", "TrustedDev"])
check("allowlisted author", cfg.is_authorized("Layomi3-0"), True)
check("case-insensitive", cfg.is_authorized("layomi3-0"), True)
check("stranger refused", cfg.is_authorized("attacker"), False)
check("empty login refused", cfg.is_authorized(""), False)

# Every field is set explicitly: AdwConfig's defaults are evaluated from the
# environment at import time, so an installed adw.env would otherwise decide what
# this test asserts — and the missing-secret case would become unreachable exactly
# on the machines where it matters.
empty = AdwConfig(allowed_authors=[], webhook_secret="")
check("empty allowlist refuses owner (fail-closed)", empty.is_authorized("Layomi3-0"), False)
check("validate flags empty allowlist", any("ALLOWED_AUTHORS" in e for e in empty.validate()), True)
check("validate flags missing secret", any("WEBHOOK_SECRET" in e for e in empty.validate()), True)
check(
    "validate does NOT require an API key (subscription auth is normal)",
    any("ANTHROPIC" in e for e in empty.validate()),
    False,
)

print("\nwebhook signature")
SECRET = "test-secret-abc123"
trigger_webhook.config.webhook_secret = SECRET
body = b'{"action":"opened","issue":{"number":42}}'
good = "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()

check("valid signature accepted", trigger_webhook.signature_valid(body, good), True)
check("tampered body rejected", trigger_webhook.signature_valid(b'{"evil":1}', good), False)
check("missing header rejected", trigger_webhook.signature_valid(body, ""), False)
check("sha1 downgrade rejected", trigger_webhook.signature_valid(body, "sha1=deadbeef"), False)
check(
    "unprefixed digest rejected",
    trigger_webhook.signature_valid(body, hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()),
    False,
)

print("\nevent routing")
trigger_webhook.config.trigger_phrase = "adw"
opened = {"action": "opened", "issue": {"number": 1, "user": {"login": "alice"}}}
check("issue opened fires", trigger_webhook.should_trigger("issues", opened)[:2], (True, "alice"))
check("issue closed ignored", trigger_webhook.should_trigger("issues", {"action": "closed", "issue": {}})[0], False)

comment = {"action": "created", "issue": {"number": 1}, "comment": {"body": " ADW ", "user": {"login": "bob"}}}
check("trigger phrase fires (trim+case)", trigger_webhook.should_trigger("issue_comment", comment)[:2], (True, "bob"))

chatter = {"action": "created", "issue": {"number": 1}, "comment": {"body": "Try again please", "user": {"login": "bob"}}}
check("ordinary comment ignored", trigger_webhook.should_trigger("issue_comment", chatter)[0], False)

# ── REGRESSIONS: bugs that broke real runs ──────────────────────────────────
print("\nverdict parsing  (run 2b1e2450: clean run reported as FAIL, no PR opened)")
V = adw_run.parse_verdict
check("summary line then PASS  ← THE REAL FAILURE", V("All five commands exit clean.\n\nPASS").verdict, "PASS")
check("bare PASS", V("PASS").verdict, "PASS")
check("fenced PASS", V("```\nPASS\n```").verdict, "PASS")
check("bolded PASS", V("**PASS**").verdict, "PASS")
check("FAIL with detail", V("FAIL: 3 tests failing").verdict, "FAIL")
check("FAIL detail preserved", V("FAIL: 3 tests failing").detail, "3 tests failing")
check("FAIL after preamble", V("Ran everything.\nFAIL: npm test exited 1").verdict, "FAIL")
check("prose containing 'pass' must NOT pass", V("the tests all pass nicely").verdict, "FAIL")
check("later FAIL beats earlier PASS", V("PASS\nFAIL: typecheck broke").verdict, "FAIL")
check("empty is FAIL", V("").verdict, "FAIL")
check("garbage is FAIL", V("¯\\_(ツ)_/¯").verdict, "FAIL")

print("\nspec discovery  (git collapses a wholly-untracked dir to '?? specs/')")
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "specs").mkdir()
    (root / "specs" / "old.md").write_text("pre-existing, uncommitted")

    original = git_ops.repo_root
    git_ops.repo_root = lambda: root
    try:
        before = git_ops.list_specs("specs")
        check("sees a pre-existing untracked spec", before, {"specs/old.md"})

        (root / "specs" / "new.md").write_text("written by this run")
        after = git_ops.list_specs("specs")
        check("returns only the NEW spec, not the old one", git_ops.newly_created(before, after), ["specs/new.md"])
        check("never returns a bare directory", any(p.endswith("/") for p in after), False)
        check("missing dir is empty, not an error", git_ops.list_specs("nope"), set())
    finally:
        git_ops.repo_root = original

print("\nbranch naming")
git_ops.config.branch_prefix = ""
check("slugify", git_ops.slugify("Fix the Login Redirect!!"), "fix-the-login-redirect")
check("slugify caps at 6 words", git_ops.slugify("a b c d e f g h"), "a-b-c-d-e-f")
check("slugify empty", git_ops.slugify("!!!"), "untitled")
check("bug branch", git_ops.branch_name("/plan_bug", 42, "abc12345", "Fix login"), "fix-42-abc12345-fix-login")
check("feature prefix", git_ops.branch_name("/plan_feature", 7, "d", "x").split("-")[0], "feat")
check("chore prefix", git_ops.branch_name("/plan_chore", 7, "d", "x").split("-")[0], "chore")

git_ops.config.branch_prefix = "lkupo/"
check(
    "repo-required branch prefix is applied",
    git_ops.branch_name("/plan_bug", 42, "abc12345", "Fix login"),
    "lkupo/fix-42-abc12345-fix-login",
)
git_ops.config.branch_prefix = ""

print("\nworktree base  (runs must be cut from fresh origin/<base>, isolated from the user's tree)")
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "repo"
    root.mkdir()
    original = git_ops.repo_root
    original_wt_root = git_ops.config.worktree_root
    git_ops.repo_root = lambda: root
    git_ops.config.worktree_root = str(Path(tmp) / "worktrees")
    try:
        import subprocess as sp

        # A real origin, because create_worktree fetches before branching — without
        # a remote it would fail for a reason no real repo has.
        origin = Path(tmp) / "origin.git"
        sp.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
        sp.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
        sp.run(["git", "config", "user.email", "t@t.t"], cwd=root, check=True)
        sp.run(["git", "config", "user.name", "t"], cwd=root, check=True)
        (root / "f.txt").write_text("base")
        sp.run(["git", "add", "-A"], cwd=root, check=True)
        sp.run(["git", "commit", "-qm", "init"], cwd=root, check=True)
        sp.run(["git", "remote", "add", "origin", str(origin)], cwd=root, check=True)
        sp.run(["git", "push", "-q", "-u", "origin", "main"], cwd=root, check=True)

        ok, wt_path = git_ops.create_worktree("chore-1-aaa-clean-tree", "aaa")
        check("worktree is created", ok, True)
        check("worktree has the base commit", (Path(wt_path) / "f.txt").exists(), True)
        check("workdir switches to the worktree", str(git_ops.workdir()), wt_path)
        git_ops.remove_worktree()
        check("remove_worktree resets workdir to repo root", git_ops.workdir(), root)
        check("remove_worktree deletes the directory", Path(wt_path).exists(), False)

        # THE POINT of worktrees: a dirty main checkout neither blocks the run
        # (old create_branch refused) nor leaks into it (old `git add -A` swept
        # uncommitted edits into the PR).
        (root / "stray.txt").write_text("unrelated work in progress")
        ok, wt_path = git_ops.create_worktree("chore-2-bbb-dirty-tree", "bbb")
        check("dirty main tree: run is NOT blocked", ok, True)
        check("dirty main tree: stray file does NOT leak in", (Path(wt_path) / "stray.txt").exists(), False)

        # origin moves ahead → the NEXT run must see the new commit (the fetch is
        # what makes "fresh from main" true, not just origin/<base> from cache).
        clone2 = Path(tmp) / "clone2"
        sp.run(["git", "clone", "-q", str(origin), str(clone2)], check=True)
        sp.run(["git", "config", "user.email", "t@t.t"], cwd=clone2, check=True)
        sp.run(["git", "config", "user.name", "t"], cwd=clone2, check=True)
        (clone2 / "newer.txt").write_text("landed on origin after our last fetch")
        sp.run(["git", "add", "-A"], cwd=clone2, check=True)
        sp.run(["git", "commit", "-qm", "newer"], cwd=clone2, check=True)
        sp.run(["git", "push", "-q"], cwd=clone2, check=True)

        ok, wt_path = git_ops.create_worktree("chore-3-ccc-fresh-base", "ccc")
        check("new origin commit is fetched into the base", ok and (Path(wt_path) / "newer.txt").exists(), True)
    finally:
        git_ops.repo_root = original
        git_ops.config.worktree_root = original_wt_root
        git_ops.set_workdir(None)

print()
if failures:
    print(f"❌ {len(failures)} FAILED: {failures}")
    sys.exit(1)
print("✅ all tests pass")
