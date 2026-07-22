# Run Local Command

Start the events-os app locally for testing: the Convex backend + the Expo web dev server. Handles this repo's non-obvious setup (Node 22, run-Convex-from-root, auth bypass) so the app comes up cleanly.

**Usage:** `/run-local`

## Why this exists

`pnpm dev` / `scripts/dev.js` is broken in this repo (needs the unpublished `@supa-media/dev`). And the system default `node` is broken, so every `node`/`npx` call must be prefixed with Node 22. This command runs Convex + Expo directly instead.

## Instructions

### Step 1: Check what's already running

```bash
lsof -ti:3210 >/dev/null 2>&1 && echo "convex UP" || echo "convex down"
lsof -ti:8081 >/dev/null 2>&1 && echo "expo UP"   || echo "expo down"
```

Only (re)start the services that are down. If both are up, just report the URLs and stop.

### Step 2: Start Convex (backend) — from the REPO ROOT

Convex **must** run from the repo root, not `apps/convex` (root `convex.json` points `functions` at `apps/convex`; running from `apps/convex` silently deploys zero functions). Run in the background:

```bash
PATH="/opt/homebrew/opt/node@22/bin:$PATH" npx convex dev
```

Wait for it to bind `http://127.0.0.1:3210` and finish "Preparing Convex functions" before moving on.

### Step 3: Start Expo web (frontend)

```bash
cd apps/mobile && PATH="/opt/homebrew/opt/node@22/bin:$PATH" npx expo start --web
```

Expo serves on `http://localhost:8081`. `app.config.js` rewrites the loopback Convex URL to the machine's LAN IP at start (Chrome blocks cross-origin loopback).

### Step 4: Report to the user

Give them:
- Web app: **http://localhost:8081**
- Convex dashboard: the local dashboard URL printed by `convex dev`
- **Login:** email OTP code is always **`000000`** (`DEV_OTP_BYPASS=true`). Any test email works.
- To reset a stuck OTP: `PATH="/opt/homebrew/opt/node@22/bin:$PATH" npx convex run seedTicketing:devClearAuthCodes`

## Notes

- **Always** prefix `node`/`npx` with `PATH="/opt/homebrew/opt/node@22/bin:$PATH"` — the default `node` (Homebrew 25) is broken (`libsimdjson` dyld crash).
- If Convex complains about `"use node"` actions failing, it's the Node version — check the PATH prefix.
- To seed demo data: `PATH="/opt/homebrew/opt/node@22/bin:$PATH" npx convex run seed:reseedNyDemo` (sign in once first so a `users` row exists).
- Keep both services running in the background; don't block the session waiting on them.
- If `convex dev` keeps retrying to connect, the local backend may have died (sleep/network change) — kill the process on port 3210 and rerun.
