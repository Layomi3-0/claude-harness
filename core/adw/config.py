"""ADW configuration, loaded from .claude/adw/adw.env.

Secrets live here rather than in harness.config because harness.config is a template
that gets copied around; adw.env is per-machine and git-excluded.
"""

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

from utils import adw_home

load_dotenv(adw_home() / "adw.env")


def _csv(name: str) -> List[str]:
    raw = os.getenv(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class AdwConfig:
    """Resolved ADW settings. Call `validate()` before trusting them."""

    allowed_authors: List[str] = field(default_factory=lambda: _csv("ADW_ALLOWED_AUTHORS"))
    trigger_phrase: str = os.getenv("ADW_TRIGGER_PHRASE", "adw").strip().lower()
    webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    port: int = int(os.getenv("ADW_PORT", "8001"))
    model: str = os.getenv("ADW_MODEL", "sonnet")
    anthropic_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_path: str = os.getenv("CLAUDE_CODE_PATH", "claude")
    github_pat: str = os.getenv("GITHUB_PAT", "")

    def is_authorized(self, login: str) -> bool:
        """Author allowlist check.

        An empty allowlist authorizes NOBODY, deliberately. The alternative default —
        empty means everyone — turns a misconfigured install into remote code execution
        on the host machine by anyone who can open an issue.
        """
        if not self.allowed_authors:
            return False
        return login.lower() in {author.lower() for author in self.allowed_authors}

    def validate(self) -> List[str]:
        """Return a list of fatal misconfigurations. Empty means good to run."""
        errors = []
        if not self.allowed_authors:
            errors.append(
                "ADW_ALLOWED_AUTHORS is empty — no one is authorized, so every trigger "
                "will be refused. Set it to your GitHub username."
            )
        if not self.webhook_secret:
            errors.append(
                "GITHUB_WEBHOOK_SECRET is unset — webhook signatures cannot be verified, "
                "so anyone who learns your tunnel URL could trigger runs. Generate one "
                "with `openssl rand -hex 32` and paste the same value into GitHub."
            )
        if not self.anthropic_key:
            errors.append("ANTHROPIC_API_KEY is unset — Claude Code cannot run headless.")
        return errors


config = AdwConfig()
