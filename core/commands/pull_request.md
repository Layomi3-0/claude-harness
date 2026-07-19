# Pull Request Command

Push the current branch and open a pull request with a body that explains the *why*,
not just the *what*.

**Usage:** `/pull_request [optional-framing]`

Assumes the work is already committed — use `/commit` first. This command creates no
commits.

## Instructions

### Step 1: Preflight

```bash
git branch --show-current
git status --porcelain
git remote -v
gh auth status
```

Stop and tell the user if:

| Condition | Why it blocks |
|---|---|
| On `main` / `master` / `develop` | A PR needs a branch. Offer to create one with `{{BRANCH_PREFIX}}` and move the commits onto it. |
| Uncommitted changes | They won't be in the PR. Offer `/commit` first. |
| No remote | Nothing to push to. |
| `gh` not authenticated | Tell the user to run `gh auth login` themselves — it's interactive. |
| Branch already has an open PR | Don't open a second one. Offer to update the existing PR body instead. |

### Step 2: Gather the Facts

```bash
git log origin/main..HEAD --oneline        # commits that will land
git diff origin/main...HEAD --stat         # scope of change
git diff origin/main...HEAD --name-only    # files touched
```

Read the commit messages — they hold the reasoning you already worked out. Do not
re-derive it from the diff and do not contradict it.

### Step 3: Establish Verification Status Honestly

**This is the step that determines whether the PR body is trustworthy.**

Determine what was *actually* verified. Do not infer from the fact that code exists
that it was run.

- Was `{{TEST_CMD}}` run against this branch? What was the result?
- Were the changes exercised end-to-end, or only built/installed?
- Are there pre-existing failures (see `.claude/PROJECT.md`) a reviewer would otherwise
  attribute to this branch?

If you did not verify something, the PR must say so. A reviewer reads the Verification
section to decide how hard to look — an inflated one causes real review effort to be
misallocated, and it is the single most damaging thing a PR body can get wrong.

If nothing has been run, say exactly that: **"Not verified — no tests were run against
this branch."** That is a legitimate PR. A false claim of passing tests is not.

### Step 4: Compose the PR

**Title:** `<type>: <concise description>` — conventional-commit types (`feat`, `fix`,
`refactor`, `docs`, `chore`, `test`, `perf`), imperative, no trailing period, under
~70 chars.

**Body:**

```md
## Summary

<2-4 sentences: what this changes and why it was worth doing. Lead with the problem,
not the solution. A reviewer should be able to stop here and know whether they care.>

<If several related things changed, a table beats a bullet list:>

| Change | Role |
|---|---|
| `<thing>` | <one line> |

## Key design decisions

<The section that makes the PR worth writing. For each non-obvious choice: what you
chose, and what you chose it OVER. A decision without its discarded alternative is
just a description.

Include decisions that constrained the implementation — "X writes to a file rather
than editing Y, because Z overwrites Y on every update" tells a reviewer more than any
amount of diff-reading will.

Omit this heading entirely if the change is genuinely mechanical.>

## Verification

<What was actually run, with results. Be specific and be honest:>

| Check | Result |
|---|---|
| `<cmd>` | ✅ passed / ❌ failed / ⚠️ pre-existing failure / not run |

<State plainly what was NOT verified and what a reviewer should therefore exercise
themselves. If pre-existing failures exist, name them so they aren't blamed on this
branch.>

## Follow-ups

<Deliberately deferred work, with a one-line reason each. Or omit the heading.>

<If the branch closes an issue: `Closes #N`>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Step 5: Push and Open

```bash
git push -u origin <branch-name>
gh pr create --base main --title "<title>" --body "<body>"
```

Use a HEREDOC for the body so markdown and backticks survive intact:

```bash
gh pr create --base main --title "<title>" --body "$(cat <<'EOF'
<body>
EOF
)"
```

Confirm the base branch is the repo's actual default (`gh repo view --json defaultBranchRef`)
rather than assuming `main`.

### Step 6: Report

- The PR URL
- The title used
- **The verification status, restated** — so the honest version is the last thing the
  user reads, not buried in the body
- Anything you flagged as unverified that they may want to check before merging

## Rules

- **Never claim a check passed that you did not run to completion.** If in doubt, mark
  it "not run" — an under-claimed PR costs a reviewer a few minutes; an over-claimed one
  costs them their trust in every future PR.
- **Never force-push** without an explicit request.
- **Never open a PR from the default branch.**
- Do not create commits here — `/commit` owns that, including its secret scanning.
- If the diff contains anything that looks like a credential, stop and say so rather
  than pushing.
- Match the repo's existing PR conventions if it has a template or a visible house
  style (`gh pr list` on recent merges will show it).
