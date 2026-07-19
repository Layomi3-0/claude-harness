# claude-harness

A portable Clean Code harness for Claude Code. Drop it into any project — new or
existing — to bring along your standards, agents, and commands **without pushing
any of it to the project's repo**.

## What's inside

```
core/
├── agents/      clean-code-reviewer, test-writer
├── commands/
│   ├── setup     /make-relevant, /prime
│   ├── plan      /plan-chore, /plan-feature, /create-plan
│   ├── execute   /fix-bug, /implement, /clean, /redesign
│   └── ship      /commit, /note
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

## Making it repo-relevant: `/make-relevant`

The harness ships generic. Its commands say "focus on the relevant files" and "run the
validation commands" without knowing what those are in *your* repo — so a fresh agent
rediscovers the layout, test runner, and conventions on every single boot, burning
context before it does any work.

`/make-relevant` does that discovery once and writes `.claude/PROJECT.md`: stack, entry
points, architecture map, relevant-files map (including what to *ignore*), verified
validation commands, testing conventions, and gotchas. Every planning and execution
command reads it first and defers to it.

The important part: it **executes** each candidate test/build/lint command and records
whether it actually passes, fails, or can't run at all — including which failures are
pre-existing. That last detail is what stops a later agent from mistaking the repo's
own broken test for a regression it caused.

```bash
# in the target repo, after installing:
/make-relevant
```

Re-run it when the stack or layout changes materially. It writes exactly one file and
touches no tracked source.

### Why a file instead of editing the commands

`install.sh` overwrites the copied command files every time you update the harness. If
`/make-relevant` edited `.claude/commands/*.md` directly, your adaptation would be
silently wiped on the next update. `.claude/PROJECT.md` sits outside the copied trees,
so it survives — and it gives you one source of truth to read and correct by hand
rather than adaptation smeared across eight files.

## The planning workflow

Two-phase, borrowed from the ADW pattern: a planning agent writes a spec, a **fresh**
agent executes it. The spec — not the conversation history — carries everything needed,
which is what makes one-shot runs and off-device execution possible.

```
/make-relevant                       # once per repo
/plan-feature add CSV export         # writes specs/add-csv-export.md — changes no code
                                     # review the spec yourself here ← the leverage point
/implement specs/add-csv-export.md   # executes it, gated on validation passing
/commit
```

| Command | Produces | Use for |
|---------|----------|---------|
| `/plan-chore` | one spec file | maintenance, sweeps, renames, dep bumps |
| `/plan-feature` | one spec file | a feature one agent can ship in one pass |
| `/create-plan` | milestone tree | multi-day work needing checkpoints |

Bugs are the exception — `/fix-bug` does its own diagnosis and spec inline (see below),
because for a bug the diagnosis *is* the work and splitting it across two commands only
loses context.

The planning commands deliberately **do not touch code**. Reviewing a spec is far
cheaper than reviewing a diff, and it's the point where your judgment has the most
leverage — a wrong plan caught here costs seconds, caught after implementation it costs
the whole run.

`/implement` **gates on validation**: it runs every command in the spec's Validation
Commands section, distinguishes new failures from the pre-existing ones `PROJECT.md`
recorded, and reports per-command pass/fail rather than asserting success. It won't
weaken a test to go green.

## Bug fixing: `/fix-bug`

One command, the whole cycle: **baseline → diagnose → spec → RED → GREEN → PROVE →
SWEEP → VALIDATE**. Add `--plan-only` to stop after the spec when you want to review
the diagnosis first, or hand the fix to a fresh agent via `/implement`.

The parts that make it thorough, most of which get skipped by hand:

- **Baseline before touching anything.** Captures which tests already fail, so a
  pre-existing breakage never gets mistaken for a regression you caused. Without this,
  a session can be lost chasing a failure that was there on arrival.
- **Root cause, not crash site.** The command forces an explicit "why this is the root
  and not one more symptom" section. A null check where it blew up treats the symptom;
  the root cause is whatever produced the null.
- **The failing test must fail for the *right reason*.** A test failing on an import
  error proves nothing. There's a decision table: assertion failure matching the
  diagnosis = genuine RED; unexpected error = the diagnosis is probably wrong; *passes*
  = stop, the bug isn't what you think.
- **PROVE — revert the fix and confirm the test fails again.** The step almost everyone
  skips. If the test still passes with the fix removed, it isn't guarding anything and
  the bug can return silently tomorrow.
- **SWEEP for siblings.** One root cause usually has several call sites. Fixing one of
  five leaves four live bugs plus a false sense of completion.
- **Never weaken a test to reach green.** If an existing test encodes wrong behavior,
  that's escalated to you with reasoning — not quietly edited. Silently editing a test
  to accommodate a change is how a real defect ships behind a green suite.

### Overlapping commands, disambiguated

| If you want to… | Use |
|---|---|
| diagnose and fix a bug, test-first | `/fix-bug` |
| diagnose a bug but review before any code moves | `/fix-bug … --plan-only` |
| ship a feature in one agent run | `/plan-feature` → `/implement` |
| plan multi-session work with checkpoints | `/create-plan` |
| load a repo into context cheaply at session start | `/prime` |
| teach the harness about a repo, once | `/make-relevant` |

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
| `SPECS_PATH` | /plan-*, /implement | `specs` |

`/make-relevant` reports **config drift** — if the values you substituted at install
time disagree with what it verified by actually running them, it tells you the exact
`harness.config` lines to change. Fix them and re-run `install.sh`.

## Updating a project later

Re-run `install.sh` against the project. It overwrites the copied harness files
(your `CLAUDE.md` is left untouched if it already exists, and `.claude/PROJECT.md`
is never touched — it lives outside the copied trees by design).

## Design notes

- **Per-project copy, not symlink** — each project can diverge, and the
  placeholder substitution bakes in project-specific commands.
- **Standards are universal; commands/agents are lightly parameterized** — the
  project-coupled bits (commands, branch prefix, co-author) live in `harness.config`.
- **No enforcement hook** — rules are followed by the model and checked via the
  `clean-code-reviewer` agent / `/clean`. Add a `PostToolUse` hook later if you
  want hard blocking.
- **Two layers of repo-specificity** — `install.sh` handles the *mechanical* layer
  (`{{TEST_CMD}}` and friends, substituted from config at install time).
  `/make-relevant` handles the *semantic* layer (layout, conventions, what to ignore,
  what actually passes) in `.claude/PROJECT.md`. The first is a find-and-replace; the
  second needs an agent to read the repo. Keeping them separate is why re-installing
  can't destroy the second.
- **Plans are the handoff unit** — the planning commands write a spec and stop. That
  boundary is deliberate: it gives you a cheap review checkpoint, and it means the
  executing agent needs no conversation history, only the file.
- **Validation is gated, not asserted** — `/implement` reports per-command results and
  distinguishes new failures from pre-existing ones. A workflow that says "zero
  regressions" in its template but never checks is worse than one that says nothing.
