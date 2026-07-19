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

empty = AdwConfig(allowed_authors=[])
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
check("slugify", git_ops.slugify("Fix the Login Redirect!!"), "fix-the-login-redirect")
check("slugify caps at 6 words", git_ops.slugify("a b c d e f g h"), "a-b-c-d-e-f")
check("slugify empty", git_ops.slugify("!!!"), "untitled")
check("bug branch", git_ops.branch_name("/plan_bug", 42, "abc12345", "Fix login"), "fix-42-abc12345-fix-login")
check("feature prefix", git_ops.branch_name("/plan_feature", 7, "d", "x").split("-")[0], "feat")
check("chore prefix", git_ops.branch_name("/plan_chore", 7, "d", "x").split("-")[0], "chore")

print()
if failures:
    print(f"❌ {len(failures)} FAILED: {failures}")
    sys.exit(1)
print("✅ all tests pass")
