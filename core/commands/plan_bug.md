# Bug Planning Command

Create a plan in `{{SPECS_PATH}}/*.md` that resolves the `Bug`, using the exact
`Plan Format` below. Follow the `Instructions` to build the plan, then follow `Report`.

**Usage:** `/plan_bug <bug-description>`

Execute the resulting plan with `/implement {{SPECS_PATH}}/<file>.md`.

## CRITICAL: You Are Not Fixing the Bug

The `Bug` describes what will be resolved — but **we are not resolving it here.** We
are writing the plan that will be used to resolve it.

That plan will be executed by a **separate agent with no memory of this conversation**.
Everything it needs must be in the plan file. Nothing it needs may live only in your
head or in this session's context.

**Do not edit project source files.** The one exception: you may write throwaway
reproduction scripts *outside* the repo to confirm your diagnosis. Delete them, and
record what they proved in the plan.

## Instructions

### 1. Load project context

Read `.claude/PROJECT.md` first — stack, layout, relevant files, verified validation
commands, testing conventions. **Defer to it over any default in this file.** If it
doesn't exist, tell the user to run `/make_relevant`, then proceed with reduced
confidence from `README.md` and the manifest.

### 2. Capture the test baseline

Run `{{TEST_CMD}}` once and record which tests **already** fail.

This costs one command and prevents the most common wasted bug-fix session: the
implementing agent sees a red suite, assumes it caused the breakage, and spends the run
chasing a failure that was there before it arrived. These go in the plan's `Notes`.

### 3. Reproduce before you theorize

Establish the actual failure. Read the code path end to end — entry point through to
the failure site. Do not stop at the first plausible cause.

### 4. Find the root cause, not the crash site

The crash site is rarely the defect. A null check where it blew up treats the symptom;
the root cause is whatever produced the null.

Useful test: *if I fix this, what else that's currently broken gets fixed too?* If the
answer is "nothing," you may still be at symptom level.

**Be honest about confidence.** If you cannot confidently identify the root cause, say
so in the plan, list the competing hypotheses, and make task 1 a diagnostic step that
discriminates between them. A plan that says "I narrowed it to two candidates, here's
how to tell them apart" is worth far more than a confident wrong one — confident wrong
diagnoses produce fixes that pass tests and don't fix the bug.

### 5. Think

Use your reasoning model. **THINK HARD** about the bug, its root cause, and the steps
to fix it properly. Think about what *else* the same root cause is breaking silently.

### 6. Be surgical

Plan the **minimal** number of changes that fix the bug. Solve the bug at hand and
don't fall off track. No refactoring, no adjacent cleanup, no features. Keep it simple.

If the plan needs a new dependency, say so explicitly in `Notes` and justify it.

### 7. Write the plan

Create `{{SPECS_PATH}}/<descriptive-slug>.md`, named after the bug. **Replace every
`<placeholder>`.** Add as much detail as needed to fix the bug.

## Plan Format

```md
# Bug: <bug name>

## Bug Description
<the bug in detail, including symptoms and expected vs actual behavior>

## Problem Statement
<the specific problem that needs to be solved>

## Solution Statement
<the proposed approach, and why it over the alternatives considered>

## Steps to Reproduce
<exact, runnable steps. If you could NOT reproduce it, say so explicitly and explain
what you did instead — never imply a reproduction you did not perform.>

## Root Cause Analysis
<The mechanism. Name the file and line where the defect originates, then trace the
causal chain from there to the observed symptom.

**Confidence:** high | medium | low
**Why this is the root, not a symptom:** <what else this same cause explains; what
would remain broken if you patched at the crash site instead>

If confidence is low, list competing hypotheses and the experiment that discriminates
between them.>

## The Failing Test
- **File:** <path, matching this repo's test conventions>
- **Name:** <test name>
- **Asserts:** <the correct behavior it demands>
- **Expected failure before the fix:** <the specific assertion message you expect —
  not merely "it errors">

<If root cause and symptom live in different modules, specify TWO tests: a unit test at
the root cause to prevent recurrence, and a regression test at the symptom to prove the
user-visible problem is gone.>

## Relevant Files
Use these files to fix the bug:

<each file, with a bullet on why it's relevant>

### New Files
<new files with their purpose. Omit this heading if none.>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Capture the baseline
- Run the validation commands and record which tests already fail.
- Cross-check against `Notes` below. Do NOT attribute pre-existing failures to your
  own changes.

### 2. Write the failing test (RED)
- Create the test described in `The Failing Test` above.
- Run it. **It must fail for the right reason:**

  | What you see | Meaning | Do |
  |---|---|---|
  | Assertion failure matching the diagnosis | ✅ genuine RED | proceed |
  | Import/syntax error, missing fixture | ❌ broken test, not a caught bug | fix the test |
  | An error you did not predict | ⚠️ diagnosis may be wrong | STOP, report back |
  | **Passes** | ⚠️ bug is not what we think | **STOP, report back** |

- Record the actual failure output — it is evidence for the final report.

### 3..N <the minimal fix — foundational shared changes first, then specific ones>
<Concrete steps naming files and symbols. Surgical. No refactoring, no features.>

### N+1. Prove the test guards the fix (PROVE)
- Temporarily revert the fix and re-run the new test.
- **Fails again** → ✅ it genuinely guards this fix. Restore the fix.
- **Still passes** → ❌ the test isn't testing what we think; the bug could return
  silently behind a green suite. Rewrite it until it fails without the fix.
- Restore the fix and confirm green before continuing. Never leave this step reverted.

### N+2. Sweep for siblings (SWEEP)
- Grep for the pattern that caused this — the same unguarded access, wrong comparison,
  missing `await`. State the search command used.
- Same root cause, in scope → fix and extend the test to cover it.
- Same root cause, larger blast radius → do NOT silently expand this fix; report it as
  a follow-up needing its own diagnosis.

### N+3. Run the Validation Commands
- Every command, not a subset. Zero new regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

<Commands from `.claude/PROJECT.md` — do not invent them. Include a command to
reproduce the bug, which must fail before the fix and pass after.>
- `<the new test, run specifically>` — fails before the fix, passes after
- `{{TEST_CMD}}` — full suite, zero regressions

## Regression Risk
<What else touches this code path and could break. What a reviewer should look at
hardest.>

## Notes
**Pre-existing failures** (recorded at planning time — do NOT attribute these to your
changes): <list, or "none — suite was green">

<New dependencies and why. Anything deliberately left unfixed, and why.>

**Never weaken, skip, or delete a test to reach green.** If an existing test genuinely
encodes wrong behavior, escalate it to the user with reasoning — do not quietly edit
it. Silently editing a test to accommodate a change is how a real defect ships behind
a green suite.
```

## Self-Check Before Reporting

Reread the plan as the implementing agent, with zero context:

- [ ] Is the root cause a *cause*, or did I just describe the symptom again?
- [ ] Would task 2 produce a test that genuinely fails now, for the stated reason?
- [ ] Is the fix minimal — am I smuggling in a refactor?
- [ ] Are the validation commands real ones from `PROJECT.md`?
- [ ] Are the pre-existing failures recorded in `Notes`?
- [ ] Could I execute every step without asking a question?
- [ ] Any `<placeholder>`s left unreplaced?

## Bug

$ARGUMENTS

## Report

- Summarize the plan in a concise bullet point list.
- Include the path to the plan you created in `{{SPECS_PATH}}/`.
- State your **confidence in the root cause analysis** plainly. If it's low, lead with
  that — do not bury it.
- State explicitly: `Run /implement {{SPECS_PATH}}/<file>.md to execute this plan.`
