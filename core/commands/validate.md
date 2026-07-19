# Validate Command

Run this repo's validation commands and report a single machine-readable verdict.

**Usage:** `/validate`

This is the **gate** in the ADW pipeline: `PASS` opens a pull request, `FAIL` stops the
run and reports on the issue. Answer accordingly — an inaccurate `PASS` ships unverified
code with a PR that claims it was checked.

## Instructions

### Step 1: Find the commands

Read `.claude/PROJECT.md` → `Validation Commands`. Those are the repo's real, verified
commands. If the file is missing, fall back to `{{TEST_CMD}}`, `{{TYPECHECK_CMD}}`, and
`{{BUILD_CMD}}`, and say so in the detail.

Also read its **pre-existing failures** list — failures recorded there are the repo's
own and must not fail this run.

### Step 2: Run every one of them

Not a subset. Not the fast one. Run each to completion and capture its exit status and
output.

### Step 3: Decide the verdict

| Situation | Verdict |
|---|---|
| Every command exits clean | `PASS` |
| Only failures already listed as pre-existing in `PROJECT.md` | `PASS` |
| Any **new** failure | `FAIL` |
| A command could not run at all (missing deps, needs a service) | `FAIL` |
| No validation commands exist anywhere | `FAIL` |

That last row is deliberate. A repo with nothing to run has not been validated, and
reporting `PASS` would let the pipeline open a PR asserting a check that never happened.
Say so in the detail so the human can fix the config.

**Do not** fix failures here. **Do not** modify, skip, or delete a test to reach green.
This command only observes and reports; it changes nothing.

## Output Format

Your entire response must be **one line**, in exactly one of these two forms:

```
PASS
```

```
FAIL: <one-line summary, then the failing command and its key output>
```

No preamble, no markdown, no code fence, no explanation before or after. A program
parses this response; anything it cannot parse is treated as `FAIL`.

### Examples

```
PASS
```

```
FAIL: 3 tests failing in src/orders.test.ts — `npm test` exited 1: expected 42, received NaN at calculateTotal (src/orders.ts:88)
```

```
FAIL: `npm run build` could not run — missing dependency 'esbuild', run npm install
```

```
FAIL: no validation commands found in .claude/PROJECT.md or harness config — nothing was verified
```
