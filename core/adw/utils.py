"""Shared utilities: run IDs and per-run logging."""

import logging
import os
import sys
import uuid
from pathlib import Path


def make_adw_id() -> str:
    """Short run ID. Threads through logs, branch name, commit, PR, and issue comments
    so a run is traceable end to end from any one of them."""
    return str(uuid.uuid4())[:8]


def adw_home() -> Path:
    """Directory holding this ADW installation (.claude/adw)."""
    return Path(__file__).resolve().parent


def repo_root() -> Path:
    """The target repository root — two levels up from .claude/adw."""
    return adw_home().parent.parent


def run_dir(adw_id: str, agent_name: str = "") -> Path:
    """Per-run artifact directory: .claude/adw/runs/{adw_id}/{agent_name}/

    Kept under .claude/ so it inherits the harness's git exclusion and never appears
    in the target repo's `git status`.
    """
    base = adw_home() / "runs" / adw_id
    if agent_name:
        base = base / agent_name
    base.mkdir(parents=True, exist_ok=True)
    return base


def setup_logger(adw_id: str, name: str = "adw") -> logging.Logger:
    """Logger writing DEBUG to file and INFO to console.

    The file half matters most: when a run fails at 3am unattended, the transcript in
    runs/{adw_id}/ is the only account of what happened.
    """
    log_file = run_dir(adw_id) / f"{name}.log"

    logger = logging.getLogger(f"adw_{adw_id}_{name}")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console)
    logger.info(f"ADW {adw_id} — logging to {log_file}")
    return logger


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
