"""ADW configuration, loaded from .claude/adw/adw.env.

Secrets live here rather than in harness.config because harness.config is a template
that gets copied around; adw.env is per-machine and git-excluded.
"""

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import dotenv_values, load_dotenv

from utils import adw_home

_ENV_FILE = adw_home() / "adw.env"
load_dotenv(_ENV_FILE)

# Values read from adw.env ONLY, ignoring the ambient environment. Needed for
# ANTHROPIC_API_KEY: load_dotenv never overrides an already-set variable, so a stale
# key exported from a shell profile would otherwise look like deliberate config.
_FILE_ONLY = dotenv_values(_ENV_FILE)


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
    # Prepended to every ADW branch, for repos whose hooks or rules require it.
    branch_prefix: str = os.getenv("ADW_BRANCH_PREFIX", "")
    # Where run worktrees live. Blank means a sibling of the repo:
    # ../<repo-name>-adw-worktrees/<adw_id>
    worktree_root: str = os.getenv("ADW_WORKTREE_ROOT", "")
    # Shell command run inside each fresh worktree before planning (dependency
    # install, codegen). Blank skips setup. Repo-specific by nature, so it lives
    # in adw.env rather than in code.
    worktree_setup: str = os.getenv("ADW_WORKTREE_SETUP", "")
    model: str = os.getenv("ADW_MODEL", "sonnet")
    # Blank means "use Claude Code's own auth" — normally a claude.ai subscription.
    # Deliberately file-only: see _FILE_ONLY above.
    anthropic_key: str = (_FILE_ONLY.get("ANTHROPIC_API_KEY") or "").strip()
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
        # ANTHROPIC_API_KEY is intentionally NOT required. Claude Code authenticates
        # with a claude.ai subscription by default; an API key is only for running as
        # a different identity. health_check.py probes real auth instead of guessing.
        return errors


config = AdwConfig()
