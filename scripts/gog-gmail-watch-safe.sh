#!/usr/bin/env bash
set -euo pipefail

: "${GOG_KEYRING_PASSWORD:?Set GOG_KEYRING_PASSWORD in an EnvironmentFile, not in this service file}"
: "${OPENCLAW_HOOKS_TOKEN:?Set OPENCLAW_HOOKS_TOKEN in an EnvironmentFile or SecretRef-resolved runtime env}"
: "${GMAIL_WATCH_TOKEN:?Set GMAIL_WATCH_TOKEN in an EnvironmentFile, not in this service file}"
: "${OPENCLAW_GATEWAY_URL:=http://127.0.0.1:18789}"
: "${GMAIL_WATCH_ACCOUNT:=ahmednasr999@gmail.com}"
: "${GMAIL_WATCH_BIND:=127.0.0.1}"
: "${GMAIL_WATCH_PORT:=8788}"
: "${GMAIL_WATCH_MAX_BYTES:=20000}"

exec /usr/local/bin/gog gmail watch serve \
  --account "$GMAIL_WATCH_ACCOUNT" \
  --bind "$GMAIL_WATCH_BIND" \
  --port "$GMAIL_WATCH_PORT" \
  --path / \
  --token "$GMAIL_WATCH_TOKEN" \
  --hook-url "$OPENCLAW_GATEWAY_URL/hooks/gmail" \
  --hook-token "$OPENCLAW_HOOKS_TOKEN" \
  --include-body \
  --max-bytes "$GMAIL_WATCH_MAX_BYTES"
