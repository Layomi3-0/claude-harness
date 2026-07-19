# Classify Issue Command

Select the planning command that fits the `GitHub Issue` below.

**Usage:** `/classify_issue <issue-title-and-body>`

Called by the ADW pipeline (`.claude/adw/adw_run.py`). Its output is parsed by a
program and validated against a typed enum — anything outside the mapping fails the run.

## Instructions

- Read the `GitHub Issue` and decide which kind of work it describes.
- **Respond with the command and nothing else.** No preamble, no explanation, no
  trailing punctuation, no code fence. The entire response must be one token from the
  `Command Mapping`.
- Think hard before answering, but do not show that thinking in the response.

## Command Mapping

| Respond with | When the issue is |
|---|---|
| `/plan_chore` | maintenance: dependency bumps, renames, dead code removal, config changes, doc updates, a sweep of a pattern |
| `/plan_bug` | something is broken: wrong output, a crash, a regression, behavior that contradicts documented intent |
| `/plan_feature` | net new capability or an enhancement to existing behavior |
| `0` | none of the above — a question, a discussion, a duplicate, or too vague to act on |

## Edge Cases

- **Bug or feature?** If the described behavior never worked, it's `/plan_feature`. If
  it worked before or the docs promise it, it's `/plan_bug`.
- **Chore or feature?** If no user-observable behavior changes, it's `/plan_chore`.
- **Several kinds at once?** Choose the one the issue *leads* with — the pipeline
  produces one plan, and the plan's scope section will bound the rest.
- **Too vague to plan?** Respond `0`. A plan built on a guess wastes a whole run;
  refusing costs nothing and prompts the human to clarify.

## GitHub Issue

$ARGUMENTS
