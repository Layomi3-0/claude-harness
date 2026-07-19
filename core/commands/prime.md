# Prime Command

Load this repository into context and report your understanding. Run this at the start
of a session in an unfamiliar repo, or after a context compaction.

**Usage:** `/prime [optional-area-to-focus-on]`

## When to Use This vs `/make_relevant`

| Command | Cost | Output | Frequency |
|---------|------|--------|-----------|
| `/make_relevant` | Expensive — runs commands, inspects deeply | Writes `.claude/PROJECT.md` | Once per repo, then on major changes |
| `/prime` | Cheap — reads only | Nothing written; context loaded | Start of any session |

`/prime` reads `PROJECT.md` if it exists, which makes it fast. If it doesn't exist,
`/prime` falls back to reading the repo directly and should tell the user to run
`/make_relevant` for the durable version.

## Instructions

### Step 1: Read the Map

```bash
git ls-files
```

If `.claude/PROJECT.md` exists, read it — it is the distilled version of everything
below, and you can skip straight to Step 3.

### Step 2: Read the Essentials

- `README.md`
- The manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, …)
- `CLAUDE.md` if present
- The entry point file(s) the manifest names

If `$ARGUMENTS` names a focus area, read that subtree in more depth.

### Step 3: Report Your Understanding

Keep it short — this is a context primer, not a document. Aim for under 300 words.

```md
## <Project Name>

**What it is:** <2 sentences>

**Stack:** <language, framework, test runner, package manager>

**Layout:**
| Path | Responsibility |
|------|----------------|
| `<dir>/` | <one line> |

**Entry points:** <paths>

**Validation:** <the test/build/lint commands — mark them "verified" only if
PROJECT.md says they were verified; otherwise say "from manifest, unverified">

**Open questions:** <anything ambiguous you'd want confirmed before doing real work,
or "None.">
```

## Rules

- **Read only.** This command changes nothing.
- Do not pad the report to look thorough — its job is to make the *next* prompt land
  well, and every wasted token works against that.
- If you couldn't determine something, say "unknown" rather than guessing. A confident
  wrong summary at the top of a session poisons everything after it.
