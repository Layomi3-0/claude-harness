# ADW — AI Developer Workflow

GitHub issue in, pull request out, running on your machine while you're away from it.

```
issue opened ──► Cloudflare tunnel ──► trigger_webhook.py
                                            │  ① verify HMAC signature
                                            │  ② check author allowlist
                                            ▼
                                       adw_run.py
   /classify_issue → branch → /plan_* → /implement → /validate ──► PR
                                                         │
                                                    FAIL └──► stop, report, no PR
```

Every arrow into a slash command is a **fresh `claude -p` process** with no shared
context. The spec file on disk is the only thing that crosses between planning and
implementation — which is exactly why the planning commands are written to be
self-contained.

## Setup

### 1. Prerequisites

```bash
brew install gh cloudflared          # or your platform's equivalent
curl -LsSf https://astral.sh/uv/install.sh | sh
gh auth login
```

### 2. Configure

```bash
cd .claude/adw
cp adw.env.sample adw.env
openssl rand -hex 32                 # paste into GITHUB_WEBHOOK_SECRET
```

Fill in `adw.env`: `ADW_ALLOWED_AUTHORS` (your GitHub username),
`GITHUB_WEBHOOK_SECRET`, `ANTHROPIC_API_KEY`.

### 3. Teach the harness this repo

```bash
# in Claude Code, in this repo:
/make_relevant
```

Not optional. `/validate` reads its commands from `.claude/PROJECT.md`, and with no
`PROJECT.md` it has nothing verified to run — so it returns `FAIL` and no PR is ever
opened. This is also where pre-existing failures get recorded, so the pipeline doesn't
blame the repo's own broken tests on its own changes.

### 4. Preflight

```bash
uv run health_check.py
```

Checks the binaries, `gh` auth, the git remote, the required slash commands, and your
config. Fix everything it flags before going further.

### 5. Start it

```bash
uv run trigger_webhook.py            # terminal 1 — binds 127.0.0.1 only
./expose_webhook.sh                  # terminal 2 — Cloudflare tunnel
```

### 6. Point GitHub at it

Repo → Settings → Webhooks → Add webhook:

| Field | Value |
|---|---|
| Payload URL | `https://<your-tunnel>.trycloudflare.com/gh-webhook` |
| Content type | `application/json` |
| Secret | the same `GITHUB_WEBHOOK_SECRET` |
| Events | Issues, Issue comments |

GitHub sends a ping; check the Recent Deliveries tab for a `200`. A `401` means the
secret doesn't match on both sides.

### 7. Try it

Open an issue describing a small chore. Watch the run report itself in the issue thread.

To re-run on an existing issue, comment `adw` (or whatever `ADW_TRIGGER_PHRASE` is).

## Security

The pipeline runs Claude Code with `--dangerously-skip-permissions`, because an
unattended run cannot answer a permission prompt. **Two gates are the entire boundary
between a GitHub event and unsupervised tool use on your machine:**

1. **HMAC signature verification** — proves the request came from GitHub, not from
   someone who found your tunnel URL. `expose_webhook.sh` refuses to start without a
   secret configured.
2. **Author allowlist** — proves the human behind the event is one you trust. An empty
   allowlist authorizes *nobody*; that default is deliberate, since the alternative
   turns a half-finished install into remote code execution.

Both are checked in `trigger_webhook.py`, and the allowlist is re-checked in
`adw_run.py` so a manual run can't bypass it.

Beyond that: prefer a private repo to start, use a fine-grained `GITHUB_PAT` if you set
one, enable branch protection so an ADW PR can't self-merge, and read the PR before
merging. The pipeline is designed to produce a reviewable artifact, not to be trusted
blindly.

## Files

| File | Role |
|---|---|
| `adw_run.py` | the pipeline — classify, branch, plan, implement, validate, PR |
| `trigger_webhook.py` | FastAPI receiver; signature + allowlist gates |
| `agent.py` | headless `claude -p` invocation, one fresh process per node |
| `git_ops.py` | deterministic git/PR operations |
| `github.py` | `gh` CLI wrapper; repo auto-detected from the git remote |
| `data_types.py` | typed models; the enums are enforced return types for glue commands |
| `config.py` | `adw.env` loading and validation |
| `health_check.py` | preflight |
| `expose_webhook.sh` | Cloudflare tunnel |

## Run artifacts

```
.claude/adw/runs/{adw_id}/
├── adw_run.log              full transcript
├── classifier/
│   ├── prompt.txt           exactly what the agent was asked
│   └── raw_output.jsonl     everything it did
├── planner/ implementor/ validator/
```

The `adw_id` appears in the branch name, the commit trailer, the PR body, and every
issue comment — so from any one of those you can find the transcript. When a run
misbehaves, `prompt.txt` is the first thing to read: it is the complete context that
agent had.

## Manual runs

```bash
uv run adw_run.py 42               # run the pipeline against issue #42
uv run adw_run.py 42 abc12345      # reuse a specific run id
```

## Differences from the tac-4 reference implementation

- **Validation gate.** tac-4 opens a PR whether or not tests pass; its plan templates
  assert "zero regressions" that nothing checks. Here `/validate` returns a bare
  `PASS`/`FAIL` and a `FAIL` stops the run — the branch is pushed and reported, but no
  PR is opened.
- **Webhook signature verification.** tac-4 has none.
- **Author allowlist.** tac-4 triggers on any newly-opened issue.
- **Fewer agent calls.** Branch naming, commit messages, and locating the new plan file
  are mechanical transforms with one right answer, so they're plain Python here rather
  than LLM calls. tac-4 spends four agent invocations on them, including one whose job
  is to parse a previous agent's prose for a file path.
- **Artifacts under `.claude/`** so they inherit the harness's git exclusion instead of
  appearing in the target repo's `git status`.
