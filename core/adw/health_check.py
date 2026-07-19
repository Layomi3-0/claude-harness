#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["python-dotenv", "pydantic"]
# ///
"""Preflight for the ADW system. Run before your first trigger.

Usage: uv run health_check.py
"""

import shutil
import subprocess
import sys

from config import config
from utils import adw_home, repo_root

OK, WARN, BAD = "✅", "⚠️ ", "❌"


def check_binary(name: str, install_hint: str) -> bool:
    if shutil.which(name):
        return True
    print(f"{BAD} {name} not found — {install_hint}")
    return False


def check_gh_auth() -> bool:
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if result.returncode == 0:
        return True
    print(f"{BAD} gh is not authenticated — run: gh auth login")
    return False


def check_repo() -> bool:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True, cwd=repo_root()
    )
    if result.returncode != 0:
        print(f"{BAD} no git remote 'origin' in {repo_root()}")
        return False
    print(f"{OK} repo: {result.stdout.strip()}")
    return True


def check_commands() -> bool:
    """The pipeline invokes these slash commands; a missing one fails mid-run."""
    required = ["classify_issue", "validate", "implement", "plan_chore", "plan_bug", "plan_feature"]
    commands_dir = adw_home().parent / "commands"
    missing = [name for name in required if not (commands_dir / f"{name}.md").exists()]
    if missing:
        print(f"{BAD} missing slash commands in {commands_dir}: {', '.join(missing)}")
        return False
    print(f"{OK} all {len(required)} required slash commands present")
    return True


def check_project_md() -> bool:
    if (adw_home().parent / "PROJECT.md").exists():
        print(f"{OK} .claude/PROJECT.md present")
        return True
    print(f"{WARN} no .claude/PROJECT.md — run /make_relevant first, or agents will")
    print("    rediscover the repo on every node and /validate won't know the commands")
    return True  # warning, not fatal


def main() -> None:
    print("ADW health check\n")
    results = [
        check_binary("claude", "https://docs.anthropic.com/en/docs/claude-code"),
        check_binary("gh", "brew install gh"),
        check_binary("uv", "curl -LsSf https://astral.sh/uv/install.sh | sh"),
        check_gh_auth(),
        check_repo(),
        check_commands(),
        check_project_md(),
    ]

    errors = config.validate()
    for error in errors:
        print(f"{BAD} {error}")

    if not config.webhook_secret:
        print(f"{WARN} without a webhook secret, do NOT expose the tunnel publicly")

    print()
    if all(results) and not errors:
        print(f"{OK} ADW is ready. Start with: uv run trigger_webhook.py")
        sys.exit(0)
    print(f"{BAD} ADW is not ready — fix the items above.")
    sys.exit(1)


if __name__ == "__main__":
    main()
