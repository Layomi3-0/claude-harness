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

### Step 3: Think

**Think hard** about the design, the integration seams, and the failure modes. Then
apply the harness's Clean Code standard (`.claude/standards/CLEAN_CODE.md`) to the
shape you're proposing — file sizes, function sizes, argument counts, single
responsibility. Plan code that would pass `/clean` on the first try.

Resist over-engineering. Do not plan configurability, abstraction layers, or extension
points for needs nobody has stated.

### Step 4: Write the Plan

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

<h3 headers with bullets, ordered so the repo is never left in a broken state between
steps. Interleave tests with implementation rather than deferring all tests to the end.
Name files and symbols concretely. The final step must be running the Validation
Commands.>

## Testing Strategy
### Unit Tests
<what to cover, in this repo's framework and conventions>

### Integration Tests
<what to cover, or "N/A — <reason>">

### Edge Cases
<empty/null inputs, error states, concurrency, boundaries — the cases most likely to
be skipped>

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

### Step 5: Self-Check Before Reporting

- [ ] Did I find and follow an existing pattern, or did I invent one unnecessarily?
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
