#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastapi", "uvicorn", "python-dotenv", "pydantic"]
# ///
"""GitHub webhook trigger for ADW.

Usage: uv run trigger_webhook.py

Fires a run when an authorized author opens an issue, or comments the trigger phrase
on one. Responds immediately and works in the background — GitHub abandons a webhook
delivery after 10 seconds, and an ADW run takes minutes.

TWO GATES stand between a GitHub event and unsupervised tool use on this machine:

  1. HMAC signature verification against GITHUB_WEBHOOK_SECRET — proves the request
     actually came from GitHub and not from anyone who discovered the tunnel URL.
  2. Author allowlist — proves the human behind the event is one you trust.

Both are mandatory. The pipeline runs Claude Code with --dangerously-skip-permissions
because unattended runs cannot answer permission prompts, so these checks are the
entire security boundary.
"""

import hashlib
import hmac
import os
import subprocess
import sys

import uvicorn
from fastapi import FastAPI, Request, Response

from config import config
from utils import adw_home, make_adw_id, repo_root

app = FastAPI(title="ADW Webhook Trigger")


def signature_valid(body: bytes, signature: str) -> bool:
    """Constant-time HMAC-SHA256 check of GitHub's X-Hub-Signature-256 header."""
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(config.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.removeprefix("sha256="))


def should_trigger(event: str, payload: dict) -> tuple[bool, str, str]:
    """Return (trigger?, author_login, reason)."""
    action = payload.get("action", "")
    issue = payload.get("issue", {})

    if event == "issues" and action == "opened":
        return True, issue.get("user", {}).get("login", ""), "issue opened"

    if event == "issue_comment" and action == "created":
        comment = payload.get("comment", {})
        body = comment.get("body", "").strip().lower()
        if body == config.trigger_phrase:
            return True, comment.get("user", {}).get("login", ""), "trigger phrase comment"

    return False, "", f"not a triggering event ({event}/{action})"


def launch(issue_number: int, adw_id: str) -> None:
    """Start the pipeline detached so the webhook can return inside GitHub's timeout."""
    subprocess.Popen(
        ["uv", "run", str(adw_home() / "adw_run.py"), str(issue_number), adw_id],
        cwd=repo_root(),
        env=os.environ.copy(),
    )


@app.post("/gh-webhook")
async def gh_webhook(request: Request, response: Response):
    body = await request.body()

    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature_valid(body, signature):
        print("REJECTED: bad or missing webhook signature", file=sys.stderr)
        response.status_code = 401
        return {"status": "rejected", "reason": "invalid signature"}

    payload = await request.json()
    event = request.headers.get("X-GitHub-Event", "")
    issue_number = payload.get("issue", {}).get("number")

    trigger, author, reason = should_trigger(event, payload)
    if not trigger or not issue_number:
        return {"status": "ignored", "reason": reason}

    if not config.is_authorized(author):
        print(f"REJECTED: @{author} not in ADW_ALLOWED_AUTHORS", file=sys.stderr)
        return {"status": "rejected", "reason": f"@{author} is not authorized"}

    adw_id = make_adw_id()
    print(f"Triggering ADW {adw_id} for #{issue_number} ({reason}, @{author})")
    launch(issue_number, adw_id)

    return {
        "status": "accepted",
        "issue": issue_number,
        "adw_id": adw_id,
        "logs": f".claude/adw/runs/{adw_id}/",
    }


@app.get("/health")
async def health():
    errors = config.validate()
    return {
        "status": "healthy" if not errors else "misconfigured",
        "errors": errors,
        "allowed_authors": len(config.allowed_authors),
    }


if __name__ == "__main__":
    errors = config.validate()
    if errors:
        print("Refusing to start — fix .claude/adw/adw.env:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    print(f"ADW webhook on :{config.port}  POST /gh-webhook  GET /health")
    print(f"Authorized authors: {', '.join(config.allowed_authors)}")
    uvicorn.run(app, host="127.0.0.1", port=config.port)
