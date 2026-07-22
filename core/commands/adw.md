# ADW Command

Get the ADW pipeline running in this repo, or diagnose why it isn't. Follow the
`Instructions`, then `Report`.

**Usage:**
- `/adw` — check readiness and report what to do next
- `/adw run <issue-number>` — run the pipeline directly against an issue (no webhook)
- `/adw serve` — bring up the webhook trigger and tunnel
- `/adw status` — what the current run is doing right now
- `/adw doctor` — diagnose a failed or stuck run

## What ADW Is

A GitHub issue becomes a reviewed PR on this machine, unattended:

```
issue → classify → worktree → setup → plan → implement → validate → PR
```

Each run works in its own git worktree cut from freshly-fetched `origin/<default>`
(under `../<repo>-adw-worktrees/<adw_id>`), so your checkout is never touched and
runs can overlap.

Each node is a fresh `claude -p` process with no memory of the others, so everything a
later node needs must be written into the plan file or the repo. Progress is posted to
the issue thread, which doubles as the run log.

**A PR is only opened if `/validate` returns PASS.** A failing run stops, says so on the
issue, and leaves the branch pushed for a human.

Everything lives in `.claude/adw/`. All commands below run from there:

```bash
cd .claude/adw
```

## CRITICAL: Two Systems, Tested Separately

The **pipeline** and the **trigger** fail for completely different reasons. Test them
together and you debug two systems through one symptom.

| Stage | Command | Proves |
|---|---|---|
| 1. Pipeline | `uv run adw_run.py <issue>` | classify → plan → implement → validate → PR |
| 2. Trigger | `uv run trigger_webhook.py` + tunnel | GitHub reaches this machine and launches a run |

**Always get stage 1 green before touching stage 2.** Stage 2 only decides *when*
stage 1 runs.

## Instructions

### If no arguments — check readiness

Run the preflight and report honestly:

```bash
cd .claude/adw && uv run health_check.py
```

It verifies `claude`/`gh`/`uv` are present, `gh` is authenticated, **`claude` can
actually authenticate** (one real round trip, not a guess), the repo has an `origin`,
the six required slash commands exist, and config is valid.

Then check the one thing it does not:

```bash
grep ADW_WORKTREE_SETUP .claude/adw/adw.env   # dependency install for fresh worktrees
```

Runs work in their own worktrees, so a dirty tree or odd branch in your checkout
does NOT block anything — no need to check `git status` first.

Report what is ready, what is not, and the single next command to run. If
`.claude/PROJECT.md` is missing, say that first — without it `/validate` does not know
this repo's real validation commands, and the gate becomes a coin flip. Run
`/make_relevant` before anything else.

### `run <issue-number>` — stage 1

```bash
cd .claude/adw && uv run adw_run.py <issue-number>
```

It runs in the foreground and posts progress to the issue. Watch it from another
terminal with `/adw status`.

**Pick a genuinely small issue for the first run.** You are testing the machine, not the
model. A typo, a missing type, a doc comment. Save hard tasks for after it works.

### `serve` — stage 2

Only after stage 1 has opened a PR.

1. Read the port for THIS repo — each repo needs its own, or the second server will not
   bind:
   ```bash
   grep ADW_PORT .claude/adw/adw.env
   ```
2. Start the trigger (bound to 127.0.0.1 only; the tunnel is what reaches it):
   ```bash
   cd .claude/adw && uv run trigger_webhook.py
   ```
3. In a second terminal, expose it:
   ```bash
   cd .claude/adw && ./expose_webhook.sh
   ```
   It refuses to start without a webhook secret — that is deliberate. Without one,
   anyone who discovers the tunnel URL can trigger runs on this machine.
4. Add the printed URL to the repo's **Settings → Webhooks**, content type
   `application/json`, with that repo's `GITHUB_WEBHOOK_SECRET`, subscribed to
   **Issues** and **Issue comments** only.

**Never print the secret into chat.** Copy it to the clipboard and let the user paste it:

```bash
grep '^GITHUB_WEBHOOK_SECRET=' .claude/adw/adw.env | cut -d= -f2- | tr -d '\n' | pbcopy
```

5. Test with GitHub's **Recent Deliveries → Redeliver**, not by opening new issues. You
   get the exact request and response, and can retry without churn.

A quick tunnel prints a **new URL every restart**, so the webhook needs updating each
time. A named tunnel (`CLOUDFLARED_TUNNEL_TOKEN`) keeps one URL.

### `status` — what is happening now

```bash
cd .claude/adw && uv run status.py      # add -w to watch
```

`adw_run.log` only writes at node boundaries, so a node thinking for four minutes looks
identical to a hung one there. `status.py` measures the agent transcript's growth over
5 seconds instead, which distinguishes working from stuck, and prints recent tool calls.

To tail the log of the newest run:

```bash
tail -f "$(command ls -td .claude/adw/runs/*/ | head -1)adw_run.log"
```

Two traps in that one line, both of which have bitten:

- **`command ls`, not `ls`.** If `ls` is aliased to `eza`/`lsd`/`exa` — common in zsh
  setups — it prints a `dir:` header inside command substitution and the path silently
  becomes garbage. `command` bypasses the alias.
- **The subshell resolves once.** A bare `runs/*/adw_run.log` glob also expands once, so
  starting it during an old run pins you to that run and you see nothing when a new one
  starts. Re-run the command after a new run begins.

`status.py` has neither problem — it reads the directory from Python. Prefer it.

### `doctor` — diagnose a failure

Find the run, then read the agent's own transcript rather than guessing:

```bash
cd .claude/adw && command ls -t runs | head -3
cat runs/<adw_id>/adw_run.log
tail -5 runs/<adw_id>/<node>/raw_output.jsonl
```

(`command ls` — a shell alias to `eza` or `lsd` corrupts the output when captured.)

`raw_output.jsonl` is the ground truth — it holds the actual API errors and tool calls.
Work from it, not from the summary.

Check these in order. Every one has bitten a real run:

| Symptom | Likely cause | Check |
|---|---|---|
| Hangs at the first node, no output | Auth. A stale `ANTHROPIC_API_KEY` makes every node 401-retry, which reads as a hang | `grep -o 'error_status[^,]*' runs/*/*/raw_output.jsonl`; then `uv run health_check.py` |
| `ANTHROPIC_API_KEY` set but you never set it | macOS `launchctl` sets it session-wide, overriding shell config | `launchctl getenv ANTHROPIC_API_KEY` → `launchctl unsetenv ANTHROPIC_API_KEY`, then restart the terminal |
| Aborts at the setup node | `ADW_WORKTREE_SETUP` failed — usually the private-registry install missing `GITHUB_TOKEN` (`read:packages`) in the trigger's environment | read the setup error on the issue; launch the trigger from a shell that has the token |
| Validation fails on missing modules | `ADW_WORKTREE_SETUP` is blank, so the fresh worktree has no `node_modules` | set it in `adw.env` (this repo: `{{WORKTREE_SETUP_CMD}}`) |
| Nothing happens when you comment | Comment must equal the trigger phrase exactly | `grep TRIGGER_PHRASE adw.env` — "adw", not "run adw please" |
| Nothing happens, webhook shows 401/403 | Signature mismatch, or author not allowlisted | secret must match GitHub byte for byte; `grep ALLOWED_AUTHORS adw.env` |
| Webhook delivers but no run starts | Wrong port, or the server is another repo's | `lsof -i :<port>` and compare to this repo's `ADW_PORT` |
| Validation failed but the work looks right | The validator's verdict, or genuinely failing commands | read the `FAIL:` detail on the issue; verify by hand in a worktree |
| Push rejected at the very end | Repo requires a branch prefix | set `ADW_BRANCH_PREFIX` in `adw.env` (include the trailing slash) |

## Worktrees

**Your working tree is never touched.** Each run gets its own worktree cut from
freshly-fetched `origin/<default>`, so a dirty checkout neither blocks a run nor
leaks into its PR, and concurrent runs on different issues cannot conflict. A failed
fetch or worktree creation is a hard error, not a warning, because a wrong base
invalidates the whole run.

Successful runs remove their worktree after the PR opens. **Failed runs keep theirs**
(the failure comment names the path) so a human can inspect what the agent left
behind — clean up with `git worktree remove --force <path>` when done.

## Security

This runs Claude Code with `--dangerously-skip-permissions` on this machine, unattended.

- `ADW_ALLOWED_AUTHORS` is an allowlist. **Empty authorizes nobody** — that is the
  intended default, not a bug. Anyone listed can cause unsupervised tool use on this
  computer with these credentials.
- The webhook secret is what proves a request came from GitHub. Without it the tunnel URL
  is the only thing standing between a stranger and a run.
- `adw.env` is mode 600 and gitignored. Never commit it, never print its values.
- Both gates are checked independently: signature first, then author.

## Report

- State plainly what is ready and what is not — do not report a check as passed that you
  did not run.
- Give **one** next command, not a menu.
- If a run failed, name the specific cause and the evidence line from `raw_output.jsonl`
  that shows it. "Something went wrong" is not a diagnosis.
- Never print secrets, tokens, or the contents of `adw.env`.

$ARGUMENTS
