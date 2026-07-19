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

if [ -z "$TOKEN" ]; then
  echo "CLOUDFLARED_TUNNEL_TOKEN is not set in adw.env." >&2
  echo "Create a tunnel at https://one.dash.cloudflare.com → Networks → Tunnels" >&2
  exit 1
fi

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

echo "Starting Cloudflare tunnel → 127.0.0.1:$(grep -E '^ADW_PORT=' "$ENV_FILE" | cut -d= -f2- || echo 8001)"
exec cloudflared tunnel run --token "$TOKEN"
