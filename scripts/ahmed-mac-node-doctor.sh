#!/usr/bin/env bash
set -euo pipefail

MAC_HOST="${AHMED_MAC_HOST:-nasrs-macbook-pro.tail945bbc.ts.net}"
MAC_USER="${AHMED_MAC_USER:-ahmednasr}"
PRIMARY_NODE="${AHMED_MAC_NODE_NAME:-Ahmed-Mac}"
UI_NODE="${AHMED_MAC_UI_NODE_NAME:-Nasr’s MacBook Pro}"
UI_NODE_DEVICE_ID="${AHMED_MAC_UI_NODE_DEVICE_ID:-0a3c00e2c1391ae44fb4f92b6cfa7812687a67b5ca72f53751924d5ec7026864}"
EXPECTED_VERSION="${OPENCLAW_EXPECTED_VERSION:-}"
SSH_TIMEOUT_SECONDS="${OPENCLAW_MAC_DOCTOR_SSH_TIMEOUT_SECONDS:-30}"

SSH_OPTS=(
  -o BatchMode=yes
  -o ConnectTimeout=8
  -o StrictHostKeyChecking=accept-new
  -o ServerAliveInterval=5
  -o ServerAliveCountMax=2
)

read_nodes() {
  timeout 25s openclaw nodes status --json 2>/dev/null | sed -n '/^{/,$p'
}

node_field() {
  local json="$1" name="$2" field="$3"
  printf '%s' "$json" | jq -r --arg name "$name" --arg field "$field" '.nodes[]? | select(.displayName == $name) | .[$field] // empty'
}

refresh_node_fields() {
  nodes_json="$(read_nodes || true)"
  primary_connected="$(node_field "$nodes_json" "$PRIMARY_NODE" connected)"
  primary_version="$(node_field "$nodes_json" "$PRIMARY_NODE" version)"
  ui_connected="$(node_field "$nodes_json" "$UI_NODE" connected)"
  ui_version="$(node_field "$nodes_json" "$UI_NODE" version)"
}

wait_for_ui_node() {
  local attempt
  for attempt in 1 2 3 4 5 6; do
    refresh_node_fields
    if [ "$ui_connected" = "true" ]; then
      return 0
    fi
    sleep 8
  done
  refresh_node_fields
  [ "$ui_connected" = "true" ]
}

repair_ui_device_pairing() {
  local result
  result="$(
    UI_NODE="$UI_NODE" UI_NODE_DEVICE_ID="$UI_NODE_DEVICE_ID" node --input-type=module <<'NODE'
import { l as listDevicePairing, n as approveDevicePairing } from "/usr/lib/node_modules/openclaw/dist/device-pairing-yQUSQ6Hd.js";

const uiName = process.env.UI_NODE;
const uiDeviceId = process.env.UI_NODE_DEVICE_ID;
const list = await listDevicePairing();
const paired = list.paired.find((device) => device.deviceId === uiDeviceId);
const pending = list.pending.find((request) =>
  request.deviceId === uiDeviceId &&
  request.displayName === uiName &&
  request.clientId === "openclaw-macos" &&
  request.isRepair === true
);

if (!paired || !pending || paired.publicKey !== pending.publicKey) {
  console.log("none");
  process.exit(0);
}

const approved = await approveDevicePairing(pending.requestId, {
  callerScopes: ["operator.admin", "operator.approvals", "operator.pairing", "operator.read", "operator.write"]
});

if (!approved || approved.status !== "approved") {
  console.log("none");
  process.exit(0);
}

console.log(`${approved.requestId} ${approved.device.platform ?? ""}`.trim());
NODE
  )"

  if [ "$result" = "none" ]; then
    return 1
  fi

  echo "Approved Mac UI device repair: ${result}"
  return 0
}

if [ -z "$EXPECTED_VERSION" ]; then
  EXPECTED_VERSION="$(openclaw --version | awk '{print $2}')"
fi

echo "Mac Node Doctor"
echo "Expected OpenClaw version: ${EXPECTED_VERSION}"

timeout "${SSH_TIMEOUT_SECONDS}s" ssh "${SSH_OPTS[@]}" "${MAC_USER}@${MAC_HOST}" '/bin/bash -s' <<'REMOTE'
set -euo pipefail
export PATH="/usr/local/Cellar/node@22/22.22.0/bin:/usr/local/opt/node@22/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin"
/usr/local/bin/openclaw --version
/usr/bin/plutil -p /Applications/OpenClaw.app/Contents/Info.plist | /usr/bin/egrep 'CFBundleShortVersionString|CFBundleVersion' || true
REMOTE

nodes_json="$(read_nodes || true)"

if ! printf '%s' "$nodes_json" | jq -e . >/dev/null 2>&1; then
  echo "ERROR: Could not read OpenClaw node status" >&2
  exit 10
fi

refresh_node_fields

if [ "$primary_connected" != "true" ]; then
  echo "Primary node disconnected, attempting LaunchAgent recovery..."
  "$(dirname "$0")/ahmed-mac-node-recover.sh"
  refresh_node_fields
fi

if [ "$ui_connected" != "true" ]; then
  echo "Mac UI node disconnected, opening OpenClaw.app..."
  timeout "${SSH_TIMEOUT_SECONDS}s" ssh "${SSH_OPTS[@]}" "${MAC_USER}@${MAC_HOST}" 'open -a OpenClaw'
  wait_for_ui_node || true
fi

if [ "$ui_connected" != "true" ]; then
  if repair_ui_device_pairing; then
    timeout "${SSH_TIMEOUT_SECONDS}s" ssh "${SSH_OPTS[@]}" "${MAC_USER}@${MAC_HOST}" 'open -a OpenClaw'
    wait_for_ui_node || true
  fi
fi

failures=0

if [ "$primary_connected" != "true" ]; then
  echo "ERROR: ${PRIMARY_NODE} is not connected" >&2
  failures=$((failures + 1))
fi

if [ "$ui_connected" != "true" ]; then
  echo "ERROR: ${UI_NODE} is not connected" >&2
  failures=$((failures + 1))
fi

if [ "$primary_version" != "$EXPECTED_VERSION" ]; then
  echo "ERROR: ${PRIMARY_NODE} version ${primary_version:-unknown} != ${EXPECTED_VERSION}" >&2
  failures=$((failures + 1))
fi

if [ "$ui_version" != "$EXPECTED_VERSION" ]; then
  echo "ERROR: ${UI_NODE} version ${ui_version:-unknown} != ${EXPECTED_VERSION}" >&2
  failures=$((failures + 1))
fi

if [ "$failures" -gt 0 ]; then
  printf '%s' "$nodes_json" | jq -r '.nodes[]? | "\(.displayName): connected=\(.connected) version=\(.version // "-") client=\(.clientId // "-") caps=\((.caps // []) | join(","))"' >&2
  exit 20
fi

echo "OK: ${PRIMARY_NODE} connected=${primary_connected} version=${primary_version}"
echo "OK: ${UI_NODE} connected=${ui_connected} version=${ui_version}"
