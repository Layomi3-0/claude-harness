# Feature Planning Command

Create a plan in `{{SPECS_PATH}}/*.md` that implements the `Feature`, using the exact
`Plan Format` below.

**Usage:** `/plan_feature <feature-description>`

## When to Use This vs `/create_plan`

| Command | Produces | Use when |
|---------|----------|----------|
| `/plan_feature` | One spec file, executable by `/implement` in a single run | A feature that one agent can ship in one pass |
| `/create_plan` | A milestone tree under `docs/plans/active/` | Multi-day work needing checkpoints across many sessions |

For bugs, use `/plan_bug` — same two-phase shape, with root cause analysis.

If the feature would take more than one focused agent run, use `/create_plan` instead
and let each milestone become its own `/plan_feature`.

## CRITICAL: You Are Not Building the Feature

You are writing the plan a **separate agent with no memory of this conversation** will
execute. Do not edit project source files.

## Instructions

### Step 1: Load Project Context

Read `.claude/PROJECT.md` first — stack, layout, relevant files, validation commands,
conventions. **Defer to it over any default in this file.** If it doesn't exist, tell
the user to run `/make_relevant`.

### Step 2: Find the Existing Pattern First

Before designing anything, find the closest existing analogue in this codebase and
read it fully. Almost every feature is the second instance of something.

- How does a comparable feature wire itself in?
- What does its test look like?
- What shared utilities, validators, or components already exist that you should reuse
  rather than rebuild?

**A plan that invents a new pattern where an existing one fits is a bad plan.** If you
deliberately depart from the existing pattern, justify it in the Solution Statement.

### Step 3: Break the Feature into Test-First Milestones

Phases 1–3 below are a *layering*. Milestones are the finer decomposition inside them,
and they are what the Step by Step Tasks are built from. Each milestone should be:

- **Small** — one write-test-then-implement cycle
- **Testable** — a clear pass/fail criterion, stated before any code is written
- **Independent** — verifiable on its own, without the milestones after it
- **Incremental** — leaves the repo working, never half-wired

Then, for every milestone, decide **the failing test that defines it** before deciding
the implementation. This is the ordering the plan must encode: a test written after the
code tends to assert what the code happens to do, and passes on the first run — which
tells you nothing.

Match the test to what the milestone adds:

| Milestone adds | The test must pin down |
|---|---|
| Schema / validation | Valid input accepted *and* each invalid case rejected |
| Data layer (read/write) | The stored or returned value for a concrete input, including the failure path |
| Stateful logic | State after the sequence of actions, not just the initial value |
| Rendering / output | The user-visible result, queried the way a user finds it |
| Interaction | That the handler fires with the right payload, not merely that it fires |
| Integration / wiring | The seam itself — that the caller reaches the new code in the real flow |

### Step 4: Think

**Think hard** about the design, the integration seams, and the failure modes. Then
apply the harness's Clean Code standard (`.claude/standards/CLEAN_CODE.md`) to the
shape you're proposing — file sizes, function sizes, argument counts, single
responsibility. Plan code that would pass `/clean` on the first try.

Resist over-engineering. Do not plan configurability, abstraction layers, or extension
points for needs nobody has stated.

### Step 5: Write the Plan

Create `{{SPECS_PATH}}/<descriptive-slug>.md`. Replace **every** `<placeholder>`.

## Plan Format

```md
# Feature: <feature name>

## Feature Description
<what it does and the value it delivers>

## User Story
As a <type of user>
I want to <action/goal>
So that <benefit/value>

## Problem Statement
<the specific problem or opportunity this addresses>

## Solution Statement
<the approach, the existing pattern it follows, and why this approach over the
alternatives considered>

## Scope
**In scope:** <explicit list>
**Out of scope:** <explicit list — the guardrail against scope creep during
implementation>

## Relevant Files
<Each existing file that must change, with a one-line reason. Include the file you
identified in Step 2 as the pattern to follow, marked as such.>

### New Files
<Each new file with its single responsibility. Omit this heading if none.>

## Implementation Plan

### Phase 1: Foundation
<Types, schemas, constants, shared utilities — everything later phases depend on.>

### Phase 2: Core Implementation
<The feature itself.>

### Phase 3: Integration
<Wiring into existing flows, routes, registries, exports.>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<One h3 per milestone, ordered so the repo is never left in a broken state between
steps. Name files and symbols concretely.

Each milestone follows the same three beats — write them out explicitly, do not just
reference this instruction:

**a. Write the failing test (RED).** The test named in this milestone's row of the
Testing Strategy table. Run it and confirm it fails:

  | What you see | Meaning | Do |
  |---|---|---|
  | Fails because the code doesn't exist or returns the old value | ✅ genuine RED | proceed |
  | Import/syntax error, missing fixture | ❌ broken test, not a defined milestone | fix the test |
  | **Passes immediately** | ⚠️ the test asserts nothing new — this behavior already exists, or the assertion is too loose | **make it specific enough to fail, or drop the milestone** |

**b. Implement the minimum to reach GREEN.** Only enough to pass the test. No extra
features, no premature abstraction, no "while I'm here" improvements — those belong to
a later milestone or to `/clean`.

**c. Run the full suite before moving on.** A milestone that passes its own test while
breaking a sibling is not complete.

The final step must be running the Validation Commands.>

## Testing Strategy

### Tests by Milestone
<One row per milestone, in execution order. This table is what the RED step of each
task refers back to — every milestone must appear here.>

| # | Milestone | Test file | The test asserts | Why it fails today |
|---|---|---|---|---|
| 1 | <milestone> | <path — existing file to extend, or new> | <concrete assertion> | <what's missing now> |

**Pattern followed:** <path to a real test in this repo whose conventions, setup, and
fixtures these tests reuse. If this area has no coverage yet, say so — the implementor
is then establishing a pattern, which is worth calling out.>

### Integration Tests
<what to cover across seams, or "N/A — <reason>">

### Edge Cases
<empty/null inputs, error states, concurrency, boundaries — the cases most likely to
be skipped. Say which milestone covers each, or it will not get written.>

## Acceptance Criteria
<Specific and checkable. Each line must be something a reviewer can verify as
objectively true or false, not a matter of taste.>

- [ ] <criterion>

## Validation Commands
Execute every command. Every one must exit clean.

<Commands from `.claude/PROJECT.md`.>
- `{{TEST_CMD}}` — full suite, zero regressions

## Notes
<New dependencies and why they're justified. Pre-existing failures the implementor must
not attribute to itself. Future work deliberately deferred.>
```

### Step 6: Self-Check Before Reporting

- [ ] Did I find and follow an existing pattern, or did I invent one unnecessarily?
- [ ] Does every milestone have a test that would genuinely fail today, and does every
      milestone appear in the Testing Strategy table?
- [ ] Is any milestone's test so loose it would pass before the code is written?
- [ ] Could a zero-context agent execute every step without asking a question?
- [ ] Would the code I'm describing pass `/clean` — file lengths, function sizes?
- [ ] Am I planning anything nobody asked for?
- [ ] Are the acceptance criteria objectively checkable?
- [ ] Any `<placeholder>`s left?

## Report

- Summarize the feature and approach in a concise bullet list.
- Give the path to the plan file.
- Name the existing pattern you followed, with its file path.
- State explicitly: `Run /implement {{SPECS_PATH}}/<file>.md to execute this plan.`
- Flag any design decision the user should confirm before implementation begins.
