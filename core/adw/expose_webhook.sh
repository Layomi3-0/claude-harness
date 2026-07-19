#!/usr/bin/env bash
#
# Expose the local ADW webhook to GitHub via a Cloudflare tunnel.
#
# The webhook server binds to 127.0.0.1 only — this tunnel is the single path in
# from the internet, and it terminates at Cloudflare, so no router or firewall
# configuration is needed and no port is opened on your machine.
#
# Usage: ./expose_webhook.sh
#
set -euo pipefail

ADW_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ADW_DIR/adw.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "No adw.env found. Copy adw.env.sample to adw.env and fill it in." >&2
  exit 1
fi

TOKEN="$(grep -E '^CLOUDFLARED_TUNNEL_TOKEN=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]')"
SECRET="$(grep -E '^GITHUB_WEBHOOK_SECRET=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]')"
PORT="$(grep -E '^ADW_PORT=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]')"
PORT="${PORT:-8001}"

# Refuse to expose an unauthenticated endpoint to the public internet.
if [ -z "$SECRET" ]; then
  echo "REFUSING TO START: GITHUB_WEBHOOK_SECRET is empty." >&2
  echo "Exposing the webhook without signature verification means anyone who finds" >&2
  echo "the tunnel URL can trigger agent runs on this machine." >&2
  echo "Generate one with: openssl rand -hex 32" >&2
  exit 1
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared not found. Install it:" >&2
  echo "  macOS: brew install cloudflared" >&2
  echo "  Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/" >&2
  exit 1
fi

# Named tunnel (stable hostname) if a token is configured; otherwise a quick tunnel,
# which needs no Cloudflare account at all. The quick tunnel's hostname is random and
# CHANGES ON EVERY RESTART, so the GitHub webhook URL must be updated each time —
# fine for testing, not for anything you leave running.
if [ -n "$TOKEN" ]; then
  echo "Starting named Cloudflare tunnel → 127.0.0.1:$PORT"
  exec cloudflared tunnel run --token "$TOKEN"
fi

echo "No CLOUDFLARED_TUNNEL_TOKEN set — starting a quick tunnel (no account needed)."
echo
echo "  ⚠️  The URL below changes every restart. Paste it into GitHub's webhook"
echo "      settings as https://<host>/gh-webhook each time you restart."
echo "      For a stable URL, create a named tunnel at"
echo "      https://one.dash.cloudflare.com → Networks → Tunnels, and put its"
echo "      token in adw.env."
echo
exec cloudflared tunnel --url "http://127.0.0.1:$PORT"
