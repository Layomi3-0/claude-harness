# Fix Bug Command (Diagnose → Test-First → Fix)

Diagnose a bug to its root cause, prove it with a failing test, fix it minimally, and
prove the test actually guards the fix.

**Usage:**
- `/fix-bug <bug-description>` — full cycle: diagnose, spec, RED, GREEN, validate
- `/fix-bug <bug-description> --plan-only` — stop after the spec, change no code

Use `--plan-only` when you want to review the diagnosis before any code moves, or when
a **fresh agent** will do the fix later. The spec is written to carry the whole job —
it must not depend on this conversation's history.

## THE NON-NEGOTIABLE

**You MUST have a test that fails against the current code before you write any fix.**

Not "you should." The failing test is what distinguishes a fix from a guess. Without
it you cannot know the bug exists, cannot know your fix addressed it, and cannot stop
it from silently returning.

The cycle: **RED** (failing test) → **GREEN** (minimal fix) → **PROVE** (test truly
guards it) → **SWEEP** (siblings) → **VALIDATE** (no regressions).

## Phase 0: Baseline — Do This Before Touching Anything

Read `.claude/PROJECT.md` for stack, conventions, and verified validation commands.
Defer to it. If it's missing, tell the user to run `/make-relevant`.

Then capture the starting state:

```bash
{{TEST_CMD}}
```

Record which tests already fail. **This is the single most important line of defense
against a confusing session** — without a baseline you cannot tell your regression
from the repo's pre-existing breakage, and you will waste the run chasing a failure
that was there before you arrived.

If `PROJECT.md` already lists pre-existing failures, confirm they match. Note any
divergence.

## Phase 1: Diagnose

### Reproduce first, theorize second

Establish the actual failure before forming a theory. Read the code path end to end —
entry point through to the failure site. Do not stop at the first plausible cause.

### Separate the symptom from the root cause

The crash site is rarely the defect. A null check where it blew up treats the symptom;
the root cause is whatever produced the null. **Fix the root cause.** In the spec,
state why you believe it is the root and not one more symptom in the chain.

Ask: *if I fix this, what else that's currently broken gets fixed too?* If the answer
is "nothing," you may still be at symptom level.

### Be honest about confidence

If you cannot confidently identify the root cause, **say so plainly**. List competing
hypotheses and the experiment that discriminates between them, and run that experiment.

A spec that says "I narrowed it to two candidates, here's how to tell them apart" is
worth far more than a confident wrong one. Confident wrong diagnoses produce fixes that
pass tests and don't fix the bug.

**Stop and ask the user if:** confidence in the root cause is low, the fix touches a
public interface or data migration, or the blast radius is much larger than the
reported symptom suggests.

## Phase 2: Write the Bug Spec

Write to `{{SPECS_PATH}}/<descriptive-slug>.md`. This is the durable record — it
survives the session, it's reviewable before code moves, and under `--plan-only` it's
the entire handoff to the next agent.

```md
# Bug: <bug name>

## Bug Description
<symptoms, plus expected vs actual behavior>

## Steps to Reproduce
<exact, runnable steps. If you could NOT reproduce it, say so explicitly and explain
what you did instead — never imply a reproduction you did not perform.>

## Root Cause Analysis
<The mechanism. Name the file and line where the defect originates, then trace the
causal chain from there to the observed symptom. State confidence: high / medium /
low. If uncertain, list competing hypotheses and how to discriminate.>

## Why This Is the Root, Not a Symptom
<What else this same cause explains. What would remain broken if you patched at the
crash site instead.>

## Solution Statement
<The approach, and why it over the alternatives considered.>

## The Failing Test
- **File:** <path, matching this repo's conventions>
- **Name:** <test name>
- **Asserts:** <the correct behavior it demands>
- **Expected failure before the fix:** <the specific assertion message you expect —
  not "it errors">

## Relevant Files
<Each file that must change, one line of why each.>

## Step by Step Tasks
### 1. Write the failing test (RED)
### 2..N <the minimal fix, foundational changes first>
### Final. Run the Validation Commands

## Regression Risk
<What else touches this code path. What a reviewer should look at hardest.>

## Notes
<Pre-existing failures from Phase 0 — the implementor must NOT attribute these to
itself. New dependencies. Anything deliberately left unfixed, and why.>
```

**If `--plan-only`: stop here.** Report the spec path and say
`Run /implement {{SPECS_PATH}}/<file>.md to execute this plan.` Change no code.

## Phase 3: RED — The Failing Test

Find the existing tests for this area first and match their patterns, runner, and
naming. A test written in a foreign style is a maintenance burden even when correct.

Write a test that:
- Reproduces the **exact** bug scenario
- Targets the **root cause**, not just the symptom. If root cause and symptom live in
  different modules, write the unit test at the root cause **and** a regression test at
  the symptom — the first prevents recurrence, the second proves the user-visible
  problem is genuinely gone.
- Asserts the **correct** behavior, so the test stays meaningful after the fix

```
describe("ComponentOrFunction", () => {
  it("should <expected-behavior> when <condition>", () => {
    // Arrange: set up the bug scenario
    // Act: trigger the buggy behavior
    // Assert: verify the CORRECT behavior — this must FAIL right now
  });
});
```

### Run it. Then read the failure output.

**A test that fails is not enough — it must fail for the right reason.**

| What you see | What it means | Do |
|---|---|---|
| Assertion failure, expected vs actual matches your diagnosis | ✅ Genuine RED | Proceed |
| Import error, syntax error, missing fixture, wrong path | ❌ Broken test, not a caught bug | Fix the test and re-run |
| Fails with an error you did **not** predict | ⚠️ Your diagnosis may be wrong | Return to Phase 1 |
| **Passes** | ⚠️ Bug isn't what you think | **STOP** |

On a pass: the bug is already fixed, doesn't exist as described, or your test misses
the scenario. Do not "fix" the test into failing. Re-diagnose, or report back to the
user that you cannot reproduce it.

Record the actual failure output — it goes in the final report as evidence.

## Phase 4: GREEN — The Minimal Fix

Only after a genuine RED.

Make the **smallest** change that makes the test pass:

- Do not refactor adjacent code you find distasteful
- Do not add features, logging, or error handling nobody asked for
- Do not "improve" anything on the way past
- Fix one bug per commit

Improvements you spot go in the report as follow-ups, not into this diff. Every extra
line you touch is a line a reviewer must now verify, and a place a new bug can hide.

Run the test again. It must now pass.

## Phase 5: PROVE — Does the Test Actually Guard the Fix?

**This step is what separates a real regression test from decoration, and it is the one
almost everyone skips.**

Temporarily revert your fix — comment it out or stash it — and re-run the new test.

- **Test fails again** → ✅ It genuinely guards this fix. Restore the fix and continue.
- **Test still passes** → ❌ It is not testing what you think. The bug can return
  silently tomorrow and this test will say nothing. Rewrite the test until it fails
  without the fix, then restore the fix.

Restore the fix and re-run to confirm green before moving on. Never leave this phase
with the fix reverted.

## Phase 6: SWEEP — Find the Siblings

The same root cause is usually present in more than one place. A fix that repairs one
of five call sites leaves four live bugs and a false sense of completion.

Grep for the pattern that caused it — the same unguarded access, the same wrong
comparison, the same missing `await`. State your search command in the report.

For each hit found:
- **Same root cause, in scope** → fix it and extend the test to cover it
- **Same root cause, larger blast radius** → do NOT silently expand this fix. Report it
  as a follow-up so it gets its own diagnosis
- **Looks similar, different cause** → note it, leave it

## Phase 7: VALIDATE

Run every validation command from `.claude/PROJECT.md`. Not a subset.

```bash
{{TEST_CMD}}
{{BUILD_CMD}}
```

Compare against the Phase 0 baseline:

| Situation | Action |
|---|---|
| Clean, or only the Phase 0 pre-existing failures | ✅ Proceed |
| A **new** failure | Fix it, then re-run everything from the top |
| A command won't run | Report ❌ unverified — never report it as passed |

**Never weaken, skip, `.skip`, or delete a test to reach green.** If an existing test
genuinely encodes the wrong behavior, that is a finding to escalate to the user — with
your reasoning — not a thing to quietly edit. Silently editing a test to accommodate
your change is how a real defect ships behind a green suite.

## Phase 8: Report

```md
## Fixed: <bug name>

### Root cause
<the mechanism, file:line — with your confidence level>

### The failing test
- **File:** `<path>` — `<test name>`
- **Failure before fix:** `<actual output — evidence, not paraphrase>`
- **Passes after fix:** ✅
- **Guard check (Phase 5):** ✅ test fails when the fix is reverted

### The fix
<concise bullets — what changed and why it addresses the root, not the symptom>

### Sibling sweep
<search command used, hits found, what was fixed vs deferred — or "no siblings found">

### Validation
| Command | Result |
|---|---|
| `<cmd>` | ✅ passed / ⚠️ pre-existing failure / ❌ failed / ❌ could not run |

<Anything not ✅: state plainly what's broken, with real output.>

### Spec
`{{SPECS_PATH}}/<file>.md`

### Follow-ups
<Deferred siblings, improvements deliberately left alone.>
```

Then offer `/commit` — it handles conventional format, secret scanning, and its own
verification. Do not commit unless the user asks.

## Anti-Patterns — DO NOT

- Write the fix first, then backfill a test around what you already built
- Accept a test that fails from an import error as a genuine RED
- Skip Phase 5 — an unproven regression test is decoration
- Patch the crash site and call it a root cause fix
- Refactor, tidy, or add features while fixing
- Weaken or skip an existing test to reach green
- Report ✅ on a command you didn't run to completion
- Fix multiple unrelated bugs in one pass

## Why This Order

1. **Baseline first** — otherwise you can't tell your breakage from theirs
2. **Root cause before test** — a test aimed at the symptom locks in the wrong behavior
3. **Failing test before fix** — proves the bug is real and reproducible
4. **Fail for the right reason** — a test failing on a typo proves nothing
5. **Minimal fix** — only what the test demands; every extra line is unverified surface
6. **Prove the guard** — an untested test is not a regression barrier
7. **Sweep** — one root cause, many call sites
8. **Full validation** — the fix is worthless if it broke something else
