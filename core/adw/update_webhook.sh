#!/usr/bin/env bash
#
# update_webhook.sh — point this repo's GitHub webhook at a new tunnel URL.
#
# Quick tunnels get a fresh random hostname every restart, so the webhook needs
# repointing each time. Doing that by hand is a trap: GitHub REPLACES the whole
# `config` object on PATCH rather than merging it, so the obvious
#
#     gh api .../hooks/ID -X PATCH -f "config[url]=..."
#
# silently deletes the secret and resets content_type to `form`. Deliveries then
# arrive unsigned, the server rejects them 401, and nothing runs — with no error
# on your side. This script always sends the complete config.
#
# Usage:
#   ./update_webhook.sh https://something.trycloudflare.com
#   ./update_webhook.sh                # reads the URL from a running tunnel's log
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
ENV_FILE="adw.env"

[ -f "$ENV_FILE" ] || { echo "No $ENV_FILE — copy adw.env.sample and fill it in." >&2; exit 1; }

read_env() { grep -E "^$1=" "$ENV_FILE" | tail -1 | cut -d= -f2- | tr -d '[:space:]'; }

SECRET="$(read_env GITHUB_WEBHOOK_SECRET)"
HOOK_ID="$(read_env ADW_WEBHOOK_ID)"

if [ -z "$SECRET" ]; then
  echo "GITHUB_WEBHOOK_SECRET is empty in $ENV_FILE." >&2
  echo "Without it GitHub's deliveries cannot be verified — refusing." >&2
  exit 1
fi

if [ -z "$HOOK_ID" ]; then
  echo "ADW_WEBHOOK_ID is not set in $ENV_FILE." >&2
  echo "Find it with:  gh api repos/{owner}/{repo}/hooks -q '.[] | \"\\(.id) \\(.config.url)\"'" >&2
  exit 1
fi

URL="${1:-}"
if [ -z "$URL" ]; then
  # Fall back to scraping a running tunnel's log, if one was redirected there.
  URL="$(grep -ohE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/adw-*tunnel*.log 2>/dev/null | tail -1 || true)"
  [ -n "$URL" ] && echo "Using URL found in tunnel log: $URL"
fi
[ -n "$URL" ] || { echo "Usage: ./update_webhook.sh https://<host>.trycloudflare.com" >&2; exit 1; }

# Accept the URL with or without the path; the bare hostname 404s.
URL="${URL%/}"
case "$URL" in */gh-webhook) ;; *) URL="$URL/gh-webhook" ;; esac

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"

# Build the payload in python so the secret never appears in argv, where any other
# process on this machine could read it from the process list.
python3 - "$URL" "$SECRET" <<'PY' | gh api "repos/$REPO/hooks/$HOOK_ID" -X PATCH --input - \
  -q '.config | "✓ \(.url)\n  content_type: \(.content_type)   secret set: \(has("secret"))"'
import json, sys
url, secret = sys.argv[1], sys.argv[2]
json.dump({"config": {"url": url, "content_type": "json",
                      "insecure_ssl": "0", "secret": secret}}, sys.stdout)
PY

echo
echo "Verifying with a ping…"
gh api "repos/$REPO/hooks/$HOOK_ID/pings" -X POST
sleep 6
RESULT="$(gh api "repos/$REPO/hooks/$HOOK_ID/deliveries" -q '.[0] | "\(.status) \(.status_code)"')"
echo "  ping → $RESULT"
case "$RESULT" in
  "OK 200") echo "  Webhook is live." ;;
  *401*)    echo "  401 = signature rejected. The secret in $ENV_FILE and GitHub disagree." >&2; exit 1 ;;
  *)        echo "  Not OK. Is the server running, and is the tunnel pointed at its port?" >&2; exit 1 ;;
esac
