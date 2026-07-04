# claude-harness

A portable Clean Code harness for Claude Code. Drop it into any project — new or
existing — to bring along your standards, agents, and commands **without pushing
any of it to the project's repo**.

## What's inside

```
core/
├── agents/      clean-code-reviewer, test-writer
├── commands/    /clean, /commit, /fix-bug, /create-plan, /redesign, /note
└── standards/   CLEAN_CODE.md, REACT_COMPONENTS.md
templates/
└── CLAUDE.md.template
harness.config   project-specific values (commands, branch prefix, co-author…)
install.sh       copies the harness in and hides it from the target repo
```

The standards are the heart of it — the hard limits (≤250-line files, ≤20-line
functions, 0-2 args, no flag arguments, one level of abstraction per function).
They're enforced as prose the model follows, plus the `clean-code-reviewer` agent
and `/clean` command you run on demand.

## Quickest way: let an agent install it for you

Open Claude Code in the project you want the harness in, and paste:

```
Install the clean-code harness into this project by following
/path/to/claude-harness/AGENT_INSTALL.md
```

The agent reads [AGENT_INSTALL.md](AGENT_INSTALL.md), auto-detects the project's
test/build/lint commands and branch convention, writes a config outside the repo,
runs the installer, and verifies the harness is git-excluded — autonomously, no
further input. It never commits or pushes; the harness stays local-only.

(Replace `/path/to/claude-harness` with wherever you cloned this repo.)

## Install into a project (manual)

```bash
cd /path/to/your/project
/path/to/claude-harness/install.sh --config /path/to/your-project.config
```

This:
1. Copies `agents/`, `commands/`, `standards/` into the project's `.claude/`
2. Fills placeholders (`{{TEST_CMD}}`, `{{BRANCH_PREFIX}}`, …) from your config
3. Stamps a `CLAUDE.md` from the template if one doesn't exist
4. Appends `.claude/` and `CLAUDE.local.md` to `.git/info/exclude` — a **local,
   uncommitted** ignore, so the harness never reaches the project's remote

That last step is the trick for working on open-source repos: the harness is fully
present for you, fully invisible to everyone else.

## Install globally (applies to every project)

```bash
/path/to/claude-harness/install.sh --global
```

Copies into `~/.claude/`. Use this for harness pieces you want everywhere without
per-project setup. Re-run after editing the harness to update.

## Configure

Copy `harness.config`, edit per project, and pass it with `--config`. Keys:

| Key | Used by | Example |
|-----|---------|---------|
| `PROJECT_NAME` / `PROJECT_DESCRIPTION` | CLAUDE.md template | — |
| `BRANCH_PREFIX` | CLAUDE.md | `lkupo/` |
| `COAUTHOR_LINE` | /commit, /fix-bug | `Co-Authored-By: Claude <noreply@anthropic.com>` |
| `TEST_CMD` / `BUILD_CMD` / `LINT_CMD` / `TYPECHECK_CMD` | /commit, /fix-bug, /clean | `npm test` |
| `NOTES_PATH` | /note | `docs/NOTES.md` |

## Updating a project later

Re-run `install.sh` against the project. It overwrites the copied harness files
(your `CLAUDE.md` is left untouched if it already exists).

## Design notes

- **Per-project copy, not symlink** — each project can diverge, and the
  placeholder substitution bakes in project-specific commands.
- **Standards are universal; commands/agents are lightly parameterized** — the
  project-coupled bits (commands, branch prefix, co-author) live in `harness.config`.
- **No enforcement hook** — rules are followed by the model and checked via the
  `clean-code-reviewer` agent / `/clean`. Add a `PostToolUse` hook later if you
  want hard blocking.
