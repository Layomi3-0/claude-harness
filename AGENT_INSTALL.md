# Agent task: install the clean-code harness into this project

You are installing the **clean-code harness** into the current project, on its own.
Do this autonomously — infer everything from the project. Only ask the user if
something is genuinely ambiguous.

The harness lives at: `/Users/jkupo/Documents/Resources/claude-harness`

## Steps

1. **Read the README first:** `/Users/jkupo/Documents/Resources/claude-harness/README.md`
   to understand what the harness provides and how `install.sh` works.

2. **Detect this project's commands and metadata** by inspecting its manifest —
   `package.json` scripts, or the stack's equivalent (`Makefile`, `pyproject.toml`,
   `Cargo.toml`, `go.mod`, etc.):
   - `TEST_CMD`, `BUILD_CMD`, `LINT_CMD`, `TYPECHECK_CMD` — use the project's real
     commands; fall back to a sensible default only if absent.
   - `PROJECT_NAME` / `PROJECT_DESCRIPTION` — from the manifest or README.
   - `BRANCH_PREFIX` — from existing branch-naming conventions if any, else `feature/`.
   - `COAUTHOR_LINE` — `Co-Authored-By: Claude <noreply@anthropic.com>` unless the
     repo clearly uses another trailer.
   - `NOTES_PATH` — `docs/NOTES.md`.
   - `SPECS_PATH` — `specs` unless the repo already has a specs/plans directory.

3. **Write the config to a temp file OUTSIDE the repo** (the session scratchpad or
   `/tmp`) — never inside the project, so it never shows up in `git status`. Use the
   `KEY=value` format from `harness.config`.

4. **Run the installer** against the current project:
   ```bash
   /Users/jkupo/Documents/Resources/claude-harness/install.sh --project "$PWD" --config <tempconfig>
   ```

5. **Verify it's hidden:** run `git status --porcelain` and confirm the harness
   (`.claude/`, `CLAUDE.md`, `CLAUDE.local.md`) does **not** appear — it should be
   excluded via `.git/info/exclude`. If the project already had a `CLAUDE.md`, note
   that it was left untouched (and the Clean Code section can be merged manually).

6. **Make it repo-relevant:** now run the `/make-relevant` command that was just
   installed (`.claude/commands/make-relevant.md`) — follow its instructions to
   analyze this repo and write `.claude/PROJECT.md`. This is what turns the generic
   harness into one that knows this codebase. Crucially it **executes** the candidate
   validation commands rather than trusting the manifest, so the recorded commands are
   known-good and pre-existing failures are documented up front.

   If its config-drift section disagrees with the values you detected in step 2,
   correct the config and re-run the installer.

7. **Report**: list what was installed (commands, agents, standards), the config
   values you detected, the validation-command status from `/make-relevant`, and
   confirm the harness is invisible to the repo's remote.

## Rules

- Do **not** commit. Do **not** push. The harness is intentionally local-only.
- Do not modify the project's tracked files (other than stamping a `CLAUDE.md` only
  if none exists — which is itself excluded from git).
