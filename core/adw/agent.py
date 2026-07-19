"""Claude Code headless invocation.

Every call spawns a FRESH `claude -p` process with no shared context. That is the whole
design: each node of the pipeline gets only what its prompt and the repo give it, so a
failure is reproducible from the recorded prompt alone.
"""

import json
import os
import subprocess
import sys
from typing import Optional, Tuple

from config import config
from data_types import AgentPromptResponse, AgentTemplateRequest
from utils import repo_root, run_dir


def check_claude_installed() -> Optional[str]:
    try:
        result = subprocess.run([config.claude_path, "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            return f"Claude Code CLI not runnable at: {config.claude_path}"
    except FileNotFoundError:
        return (
            f"Claude Code CLI not found at: {config.claude_path}. "
            "Run `which claude` and set CLAUDE_CODE_PATH in .claude/adw/adw.env."
        )
    return None


def _claude_env() -> dict:
    """Environment for the child `claude` process.

    Inherits the parent environment so Claude Code can reach its own credentials —
    normally a claude.ai subscription, stored in the macOS Keychain or ~/.claude.

    ANTHROPIC_API_KEY is then actively REMOVED unless adw.env explicitly supplies one.
    A stale key exported from a shell profile otherwise takes precedence over working
    subscription auth, and every node dies in a 401 retry loop that looks like a hang
    rather than an auth failure.
    """
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env["CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR"] = "true"

    if config.anthropic_key:
        env["ANTHROPIC_API_KEY"] = config.anthropic_key
    if config.github_pat:
        env["GITHUB_PAT"] = config.github_pat
        env["GH_TOKEN"] = config.github_pat
    return env


def _parse_result(output_file: str) -> Tuple[Optional[str], bool]:
    """Pull the final result text and error flag out of the stream-json transcript."""
    try:
        with open(output_file) as f:
            messages = [json.loads(line) for line in f if line.strip()]
    except Exception as e:
        return f"Could not parse agent transcript: {e}", False

    for message in reversed(messages):
        if message.get("type") == "result":
            return message.get("result", ""), not message.get("is_error", False)
    return None, False


def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Run one slash command headless and return its final text.

    Note `--dangerously-skip-permissions`: unattended runs cannot answer prompts. This
    is precisely why the trigger enforces an author allowlist and a verified webhook
    signature before ever reaching this function — those checks are the only thing
    standing between a GitHub issue and unsupervised tool use on this machine.
    """
    error = check_claude_installed()
    if error:
        return AgentPromptResponse(output=error, success=False)

    prompt = f"{request.slash_command} {' '.join(request.args)}".strip()
    agent_dir = run_dir(request.adw_id, request.agent_name)

    (agent_dir / "prompt.txt").write_text(prompt)
    output_file = agent_dir / "raw_output.jsonl"

    cmd = [
        config.claude_path,
        "-p",
        prompt,
        "--model",
        request.model,
        "--output-format",
        "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
    ]

    try:
        with open(output_file, "w") as sink:
            result = subprocess.run(
                cmd, stdout=sink, stderr=subprocess.PIPE, text=True,
                env=_claude_env(), cwd=repo_root(),
            )
    except Exception as e:
        return AgentPromptResponse(output=f"Error executing Claude Code: {e}", success=False)

    if result.returncode != 0:
        return AgentPromptResponse(output=f"Claude Code error: {result.stderr}", success=False)

    output, ok = _parse_result(str(output_file))
    if output is None:
        return AgentPromptResponse(output="No result message in agent transcript", success=False)
    return AgentPromptResponse(output=output, success=ok)


def run_template(request: AgentTemplateRequest, logger) -> AgentPromptResponse:
    """execute_template with logging, for pipeline nodes."""
    logger.info(f"→ {request.agent_name}: {request.slash_command}")
    response = execute_template(request)
    logger.debug(f"{request.agent_name} output: {response.output}")
    if not response.success:
        logger.error(f"{request.agent_name} failed: {response.output}")
    return response
