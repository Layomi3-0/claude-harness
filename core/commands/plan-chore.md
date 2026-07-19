# Chore Planning Command

Create a plan in `{{SPECS_PATH}}/*.md` that resolves the `Chore`, using the exact
`Plan Format` below. Follow the `Instructions` to build the plan, then follow
`Report`.

**Usage:** `/plan-chore <chore-description>`

A chore is maintenance work with no new user-facing behavior: dependency bumps,
renames, dead code removal, config changes, replacing a pattern across files.

## CRITICAL: You Are Not Doing the Chore

You are writing the plan that a **separate agent with no memory of this conversation**
will execute. Everything that agent needs must be in the plan file. Nothing it needs
may live only in your head or in this session's context.

If you catch yourself editing project source files, stop — that is the job of
`/implement`.

## Instructions

### Step 1: Load Project Context

Read `.claude/PROJECT.md` first. It defines this repo's stack, layout, relevant files,
validation commands, and conventions — **defer to it over any default in this file.**

If `.claude/PROJECT.md` does not exist, tell the user to run `/make-relevant` first,
then proceed with reduced confidence using `README.md` and the manifest.

### Step 2: Research

- Read the files the chore touches. Read them fully; do not plan against a grep hit.
- Find **every** occurrence if the chore is a sweep — an incomplete sweep is worse
  than none. Use `git ls-files` plus Grep, and state your search commands in the plan.
- Identify the blast radius: what imports the thing you're changing?

### Step 3: Think

Use your reasoning model. **Think hard** about ordering. Foundational shared changes
come first; leaf changes last. A plan whose steps are in the wrong order will fail
halfway and leave the repo broken.

### Step 4: Write the Plan

Create `{{SPECS_PATH}}/<descriptive-slug>.md`. Replace **every** `<placeholder>`.

## Plan Format

```md
# Chore: <chore name>

## Chore Description
<what the chore is and why it's worth doing, in detail>

## Scope
**In scope:** <explicit list>
**Out of scope:** <explicit list — this is what keeps the implementing agent from
drifting>

## Relevant Files
<Every file that must change, each with a one-line reason. If the chore is a sweep,
list all occurrences and the command you used to find them so the implementor can
re-verify the list is complete.>

### New Files
<Files to create, with their purpose. Omit this heading if none.>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<h3 headers with bullets. Start with foundational shared changes, then specific ones.
Each step must be concrete enough to execute without re-deriving the decision — name
files, name symbols, show the before/after shape for anything non-obvious. The final
step must be running the Validation Commands.>

## Validation Commands
Execute every command. Every one must exit clean.

<Commands copied from `.claude/PROJECT.md` — do not invent them. Add any chore-specific
check, e.g. a grep proving zero occurrences of the old pattern remain.>
- `{{TEST_CMD}}` — full suite, zero regressions

## Notes
<Pre-existing failures the implementor must not attribute to itself. New dependencies
added. Anything deferred and why.>
```

### Step 5: Self-Check Before Reporting

Reread your plan as if you were the implementing agent with zero context:

- [ ] Could I execute every step without asking a question?
- [ ] Does any step say "update the relevant files" instead of naming them?
- [ ] Are the validation commands real ones from `PROJECT.md`, not aspirational?
- [ ] Does the scope section make it clear what NOT to touch?
- [ ] Are there `<placeholder>`s left unreplaced?

Fix anything that fails this check before reporting.

## Report

- Summarize the plan in a concise bullet list.
- Give the path to the plan file.
- State explicitly: `Run /implement {{SPECS_PATH}}/<file>.md to execute this plan.`
- Flag any assumption you made that the user should confirm before implementation.
