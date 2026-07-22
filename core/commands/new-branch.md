# New Branch Command

Start fresh work from an up-to-date `main`: sync `main`, then create a new feature or bug-fix branch.

**Usage:** `/new-branch [optional short description]`

## Instructions

### Step 1: Sync main

Run these before touching anything else:

```bash
git checkout main && git pull
```

- If the working tree has **uncommitted tracked changes**, STOP and tell the user — do not switch branches and risk losing work. Ask whether to stash, commit, or discard. (Untracked files are fine and can be left in place.)
- If `git pull` fails (conflicts, diverged history), STOP and surface the error rather than forcing anything.

### Step 2: Ask what we're working on

If `$ARGUMENTS` already describes the work, use it. Otherwise ask the user two things:

1. **Type** — is this a feature or a bug fix?
2. **Short description** — a few words describing the work.

### Step 3: Create the branch

Derive a kebab-case slug from the description and create the branch:

- Feature → `feat/<slug>`
- Bug fix → `fix/<slug>`

```bash
git checkout -b <prefix>/<slug>
```

Keep the slug short and descriptive (e.g. `fix/rsvp-email-verification`, `feat/phase-readiness-rings`).

### Step 4: Confirm

Report the new branch name and confirm we're ready to start work.

## Notes

- Never create a branch off a stale `main` — Step 1 must succeed first.
- Never guess the branch name from thin air; if unsure, ask (Step 2).
