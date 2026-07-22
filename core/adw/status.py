#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""Show what the current ADW run is doing right now.

Usage:
  uv run status.py            # newest run
  uv run status.py <adw_id>   # a specific run
  uv run status.py -w         # watch, refreshing every 5s

Answers the question adw_run.log cannot: a node that writes nothing for minutes
is indistinguishable from a hung one in the run log, because the log only records
node boundaries. The agent's own transcript grows continuously, so its size over
time is the real liveness signal.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"


def newest_run() -> Path | None:
    runs = [p for p in RUNS.iterdir() if p.is_dir()] if RUNS.is_dir() else []
    return max(runs, key=lambda p: p.stat().st_mtime, default=None)


def alive() -> bool:
    return subprocess.run(["pgrep", "-f", "adw_run.py"], capture_output=True).returncode == 0


def active_agent(run: Path) -> Path | None:
    """The agent directory whose transcript was written to most recently."""
    dirs = [d for d in run.iterdir() if d.is_dir() and (d / "raw_output.jsonl").exists()]
    return max(dirs, key=lambda d: (d / "raw_output.jsonl").stat().st_mtime, default=None)


def tool_calls(transcript: Path, limit: int = 8) -> list[str]:
    calls = []
    for line in transcript.read_text(errors="ignore").splitlines():
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if message.get("type") != "assistant":
            continue
        for block in message.get("message", {}).get("content", []):
            if block.get("type") != "tool_use":
                continue
            args = block.get("input", {})
            detail = (
                args.get("file_path") or args.get("pattern")
                or args.get("command") or args.get("path") or ""
            )
            first_line = (str(detail).splitlines() or [""])[0]
            calls.append(f"{block.get('name')}: {first_line[:70]}")
    return calls[-limit:]


def report(run: Path) -> None:
    print(f"run {run.name}   {'🟢 process alive' if alive() else '🔴 no adw_run.py process'}")

    log = run / "adw_run.log"
    if log.exists():
        for line in log.read_text().splitlines()[-3:]:
            print(f"  {line.split(' - ', 2)[-1]}")

    agent = active_agent(run)
    if not agent:
        print("  (no agent transcript yet)")
        return

    transcript = agent / "raw_output.jsonl"
    before = transcript.stat().st_size
    time.sleep(5)
    after = transcript.stat().st_size
    growth = after - before

    state = f"+{growth}B in 5s — producing output" if growth else "no new output — mid-inference"
    print(f"\n  active node: {agent.name}  ({after // 1024} KB, {state})")

    print("  recent actions:")
    for call in tool_calls(transcript):
        print(f"    {call}")


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "-w"]
    watch = "-w" in sys.argv

    run = RUNS / args[0] if args else newest_run()
    if not run or not run.is_dir():
        print("No runs found.")
        sys.exit(1)

    while True:
        report(run)
        if not watch:
            return
        print("\n" + "─" * 60)


if __name__ == "__main__":
    main()
