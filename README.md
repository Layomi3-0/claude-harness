# claude-harness

A portable Clean Code harness for Claude Code. Drop it into any project — new or
existing — to bring along your standards, agents, and commands **without pushing
any of it to the project's repo**.

## What's inside

```
core/
├── agents/      clean-code-reviewer, test-writer
├── commands/
│   ├── setup     /make_relevant, /prime
│   ├── plan      /plan_chore, /plan_bug, /plan_feature, /create_plan
│   ├── execute   /implement, /clean, /redesign
│   └── ship      /commit, /pull_request, /note
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

## Making it repo-relevant: `/make_relevant`

The harness ships generic. Its commands say "focus on the relevant files" and "run the
validation commands" without knowing what those are in *your* repo — so a fresh agent
rediscovers the layout, test runner, and conventions on every single boot, burning
context before it does any work.

`/make_relevant` does that discovery once and writes `.claude/PROJECT.md`: stack, entry
points, architecture map, relevant-files map (including what to *ignore*), verified
validation commands, testing conventions, and gotchas. Every planning and execution
command reads it first and defers to it.

The important part: it **executes** each candidate test/build/lint command and records
whether it actually passes, fails, or can't run at all — including which failures are
pre-existing. That last detail is what stops a later agent from mistaking the repo's
own broken test for a regression it caused.

```bash
# in the target repo, after installing:
/make_relevant
```

Re-run it when the stack or layout changes materially. It writes exactly one file and
touches no tracked source.

### Why a file instead of editing the commands

`install.sh` overwrites the copied command files every time you update the harness. If
`/make_relevant` edited `.claude/commands/*.md` directly, your adaptation would be
silently wiped on the next update. `.claude/PROJECT.md` sits outside the copied trees,
so it survives — and it gives you one source of truth to read and correct by hand
rather than adaptation smeared across eight files.

## The planning workflow

Two-phase, borrowed from the ADW pattern: a planning agent writes a spec, a **fresh**
agent executes it. The spec — not the conversation history — carries everything needed,
which is what makes one-shot runs and off-device execution possible.

```
/make_relevant                       # once per repo
/plan_feature add CSV export         # writes specs/add-csv-export.md — changes no code
                                     # review the spec yourself here ← the leverage point
/implement specs/add-csv-export.md   # executes it, gated on validation passing
/commit
```

| Command | Produces | Use for |
|---------|----------|---------|
| `/plan_chore` | one spec file | maintenance, sweeps, renames, dep bumps |
| `/plan_bug` | one spec file | bugs — diagnosis, root cause, test-first fix plan |
| `/plan_feature` | one spec file | a feature one agent can ship in one pass |
| `/create_plan` | milestone tree | multi-day work needing checkpoints |

The planning commands deliberately **do not touch code**. Reviewing a spec is far
cheaper than reviewing a diff, and it's the point where your judgment has the most
leverage — a wrong plan caught here costs seconds, caught after implementation it costs
the whole run.

`/implement` **gates on validation**: it runs every command in the spec's Validation
Commands section, distinguishes new failures from the pre-existing ones `PROJECT.md`
recorded, and reports per-command pass/fail rather than asserting success. It won't
weaken a test to go green.

## Bug fixing: `/plan_bug` → `/implement`

`/plan_bug` diagnoses and writes the spec; `/implement` executes it. Same two-phase
shape as every other planning command — the diagnosis gets reviewed before any code
moves, and the fix runs from a fresh agent with no conversation history.

The plan it emits **prescribes the discipline** rather than merely describing the fix.
Its task list is `baseline → RED → minimal fix → PROVE → SWEEP → VALIDATE`, so the
implementing agent is the one held to it:

- **Baseline first.** `/plan_bug` runs the suite at planning time and records which
  tests already fail, into the spec's `Notes`. This costs one command and prevents the
  most common wasted session: the implementing agent sees red, assumes it caused the
  breakage, and spends the run chasing a failure that predates it.
- **Root cause, not crash site.** The plan requires an explicit "why this is the root,
  not a symptom" line plus a stated confidence level. A null check where it blew up
  treats the symptom; the root cause is whatever produced the null.
- **The failing test must fail for the *right reason*.** A test failing on an import
  error proves nothing. The plan carries a decision table: assertion failure matching
  the diagnosis = genuine RED; unexpected error = the diagnosis is probably wrong;
  *passes* = stop, the bug isn't what we think.
- **PROVE — revert the fix, confirm the test fails again.** The step almost everyone
  skips. If the test still passes with the fix removed, it guards nothing and the bug
  can return silently behind a green suite.
- **SWEEP for siblings.** One root cause usually has several call sites. Fixing one of
  five leaves four live bugs plus a false sense of completion.
- **Never weaken a test to reach green.** A test encoding wrong behavior gets escalated
  with reasoning, not quietly edited.

Low confidence in the root cause is reported as low confidence, and task 1 becomes a
diagnostic that discriminates between the hypotheses. A plan saying "I narrowed it to
two candidates, here's how to tell them apart" beats a confident wrong one — confident
wrong diagnoses produce fixes that pass tests and don't fix the bug.

### Overlapping commands, disambiguated

| If you want to… | Use |
|---|---|
| diagnose a bug and plan a test-first fix | `/plan_bug` → `/implement` |
| ship a feature in one agent run | `/plan_feature` → `/implement` |
| plan multi-session work with checkpoints | `/create_plan` |
| load a repo into context cheaply at session start | `/prime` |
| teach the harness about a repo, once | `/make_relevant` |
| open a PR explaining the *why* | `/pull_request` |

## Shipping: `/pull_request`

Pushes the branch and opens a PR whose body carries the reasoning, not a restatement of
the diff. Three sections: **Summary** (lead with the problem), **Key design decisions**
(each choice *and what it was chosen over* — a decision without its discarded
alternative is just a description), and **Verification**.

That last one is the point. The command establishes what was *actually* run before
composing anything, and is required to say so plainly — including "not verified, no
tests were run against this branch," which is a legitimate PR. An inflated Verification
section causes a reviewer to misallocate real attention, and it is the single most
damaging thing a PR body can get wrong.

Assumes work is already committed; `/commit` owns commit creation and secret scanning.
It refuses to open a PR from the default branch, won't force-push, and won't open a
second PR on a branch that already has one.

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
| `COAUTHOR_LINE` | /commit, /plan_bug | `Co-Authored-By: Claude <noreply@anthropic.com>` |
| `TEST_CMD` / `BUILD_CMD` / `LINT_CMD` / `TYPECHECK_CMD` | /commit, /plan_bug, /clean | `npm test` |
| `NOTES_PATH` | /note | `docs/NOTES.md` |
| `SPECS_PATH` | /plan-*, /implement | `specs` |

`/make_relevant` reports **config drift** — if the values you substituted at install
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
  `/make_relevant` handles the *semantic* layer (layout, conventions, what to ignore,
  what actually passes) in `.claude/PROJECT.md`. The first is a find-and-replace; the
  second needs an agent to read the repo. Keeping them separate is why re-installing
  can't destroy the second.
- **Plans are the handoff unit** — the planning commands write a spec and stop. That
  boundary is deliberate: it gives you a cheap review checkpoint, and it means the
  executing agent needs no conversation history, only the file.
- **Validation is gated, not asserted** — `/implement` reports per-command results and
  distinguishes new failures from pre-existing ones. A workflow that says "zero
  regressions" in its template but never checks is worse than one that says nothing.
