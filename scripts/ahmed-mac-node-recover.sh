#!/usr/bin/env bash
set -euo pipefail

MAC_HOST="${AHMED_MAC_HOST:-nasrs-macbook-pro.tail945bbc.ts.net}"
MAC_USER="${AHMED_MAC_USER:-ahmednasr}"
NODE_NAME="${AHMED_MAC_NODE_NAME:-Ahmed-Mac}"
LABEL="${OPENCLAW_MAC_LAUNCHD_LABEL:-ai.openclaw.node}"
PLIST_PATH="${OPENCLAW_MAC_LAUNCHD_PLIST:-/Users/${MAC_USER}/Library/LaunchAgents/${LABEL}.plist}"
SSH_TIMEOUT_SECONDS="${OPENCLAW_MAC_RECOVERY_SSH_TIMEOUT_SECONDS:-30}"

SSH_OPTS=(
  -o BatchMode=yes
  -o ConnectTimeout=8
  -o StrictHostKeyChecking=accept-new
  -o ServerAliveInterval=5
  -o ServerAliveCountMax=2
)

echo "Ensuring ${NODE_NAME} LaunchAgent on ${MAC_USER}@${MAC_HOST}"

timeout "${SSH_TIMEOUT_SECONDS}s" ssh "${SSH_OPTS[@]}" "${MAC_USER}@${MAC_HOST}" "LABEL='${LABEL}' PLIST='${PLIST_PATH}' /bin/bash -s" <<'REMOTE'
set -euo pipefail
uid="$(id -u)"

if [ ! -f "$PLIST" ]; then
  echo "ERROR: LaunchAgent plist missing: $PLIST" >&2
  exit 20
fi

/usr/bin/plutil -lint "$PLIST" >/dev/null

if ! /bin/launchctl print "gui/${uid}/${LABEL}" >/dev/null 2>&1; then
  /bin/launchctl bootstrap "gui/${uid}" "$PLIST"
fi

/bin/launchctl kickstart -k "gui/${uid}/${LABEL}" >/dev/null 2>&1 || true
sleep 2
/bin/launchctl print "gui/${uid}/${LABEL}" >/dev/null
REMOTE

deadline=$((SECONDS + ${OPENCLAW_MAC_RECOVERY_WAIT_SECONDS:-45}))
while [ "$SECONDS" -lt "$deadline" ]; do
  status_json="$(timeout 20s openclaw nodes status --json 2>/dev/null | sed -n '/^{/,$p' || true)"
  if printf '%s' "$status_json" | jq -e --arg name "$NODE_NAME" '.nodes[]? | select(.displayName == $name and .connected == true)' >/dev/null 2>&1; then
    echo "OK: ${NODE_NAME} connected"
    exit 0
  fi
  sleep 3
done

echo "ERROR: ${NODE_NAME} did not reconnect before timeout" >&2
timeout 20s openclaw nodes status --json 2>/dev/null | sed -n '/^{/,$p' | jq -r '.nodes[]? | "\(.displayName): connected=\(.connected) version=\(.version // "-") client=\(.clientId // "-")"' >&2 || true
exit 30
