# Implement Command

Execute a plan produced by `/plan-chore`, `/plan-feature`, or `/fix-bug --plan-only`.

**Usage:** `/implement <path-to-plan-file>`

## Instructions

### Step 1: Load Context

1. Read `.claude/PROJECT.md` — this repo's stack, conventions, and **verified**
   validation commands. Defer to it.
2. Read the plan file at `$ARGUMENTS` **in full** before writing any code.
3. Read every file listed in the plan's `Relevant Files` section.

### Step 2: Think

**Think hard** about the plan before executing it. You are not a transcription
machine — you are the engineer holding the pen.

If the plan is wrong, **stop and say so.** A plan written by an earlier agent against
a slightly different repo state can be stale, can have missed a caller, can propose a
pattern the codebase has since moved away from. Executing a plan you can see is broken
is the worst available outcome: it produces a confident, tested, entirely wrong change.

Report the conflict to the user and ask how to proceed. Do not silently "improve" the
plan either — a silent deviation makes the plan file a lie about what the repo now
contains.

### Step 3: Execute

Work the `Step by Step Tasks` in order, top to bottom. The order is load-bearing: it
is designed so the repo is never left in a broken state between steps.

**Stay inside the plan's scope.** If the plan has an `Out of scope` section, treat it
as a hard boundary. Do not refactor adjacent code you find distasteful. Do not add
error handling for scenarios nobody raised. Note improvements you spot for later
instead of making them now.

Follow the repo's conventions from `PROJECT.md` and the Clean Code standard at
`.claude/standards/CLEAN_CODE.md` — file length limits, function size, argument
counts, one level of abstraction per function.

### Step 4: Validate — This Gate Is Not Optional

Run **every** command in the plan's `Validation Commands` section. Not a subset. Not
the fast one.

Compare failures against the plan's `Notes` section, which lists pre-existing failures:

| Situation | Action |
|-----------|--------|
| All clean | Proceed to report |
| Failure listed as pre-existing in the plan | Note it, proceed, restate it in the report |
| **New** failure caused by your change | **Fix it and re-run everything from the top** |
| Command won't run at all | Report as ❌ unverified — **never** report it as passed |

Loop until clean or until you are genuinely stuck. If stuck after honest attempts,
stop and report the failure with its actual output. **Do not** report partial success
as success, and do not weaken, skip, or delete a test to make the suite green — if a
test is genuinely wrong, that is a finding to escalate, not a thing to quietly edit.

### Step 5: Report

```md
## Implemented: <plan name>

### What changed
<concise bullet list of the actual work>

### Validation
| Command | Result |
|---------|--------|
| `<cmd>` | ✅ passed / ❌ failed / ⚠️ pre-existing failure / ❌ could not run |

<If anything is not ✅, state plainly what is broken and paste the real output.>

### Diff
<output of `git diff --stat`>

### Deviations from the plan
<Anything you did differently and why — or "None.">

### Follow-ups
<Improvements you noticed but deliberately left alone, per scope.>
```

## Rules

- **Do not commit or push** unless the user asks. Use `/commit` for that — it has its
  own verification and secret-scanning steps.
- **Report faithfully.** If tests fail, say so with the output. If you skipped a step,
  say so. The value of this command collapses entirely if its reports can't be trusted.
- Never mark a validation command ✅ that you did not actually run to completion.
