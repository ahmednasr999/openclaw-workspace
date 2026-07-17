#!/usr/bin/env bash
set -uo pipefail

BACKUP_DIR="/root/.openclaw/backups/openclaw-update-20260714-111403"
LOG="$BACKUP_DIR/stable-maintenance.log"
SYSTEM_OC="/usr/bin/openclaw"
NVM_OC="/root/.nvm/versions/node/v22.22.0/bin/openclaw"

mkdir -p "$BACKUP_DIR"
exec >>"$LOG" 2>&1

echo "[$(date --iso-8601=seconds)] stable maintenance start"

restore_gateway() {
  local rc=$?
  if ! systemctl --user is-active --quiet openclaw-gateway.service; then
    echo "[$(date --iso-8601=seconds)] recovery start for gateway, rc=$rc"
    systemctl --user daemon-reload || true
    systemctl --user reset-failed openclaw-gateway.service || true
    systemctl --user start openclaw-gateway.service || true
  fi
  echo "[$(date --iso-8601=seconds)] maintenance exit rc=$rc"
  exit "$rc"
}
trap restore_gateway EXIT

unset OPENCLAW_SYSTEMD_UNIT OPENCLAW_SERVICE_MARKER OPENCLAW_SERVICE_KIND OPENCLAW_SERVICE_VERSION

echo "[$(date --iso-8601=seconds)] stopping gateway"
systemctl --user stop openclaw-gateway.service

echo "[$(date --iso-8601=seconds)] updating active system installation"
"$SYSTEM_OC" update --channel stable --yes --no-restart --json --timeout 1800

if [[ -x "$NVM_OC" ]]; then
  echo "[$(date --iso-8601=seconds)] updating secondary NVM installation"
  "$NVM_OC" update --channel stable --yes --no-restart --json --timeout 1800
fi

echo "[$(date --iso-8601=seconds)] reinstalling gateway service metadata"
"$SYSTEM_OC" gateway install --force --port 18789 --runtime node --json
systemctl --user daemon-reload
systemctl --user reset-failed openclaw-gateway.service || true
systemctl --user start openclaw-gateway.service

echo "[$(date --iso-8601=seconds)] waiting for gateway probe"
probe_ok=0
for _ in $(seq 1 30); do
  if "$SYSTEM_OC" gateway probe --json >"$BACKUP_DIR/gateway-probe-after.json" 2>&1; then
    probe_ok=1
    break
  fi
  sleep 2
done
if [[ "$probe_ok" -ne 1 ]]; then
  echo "gateway probe did not recover"
  exit 1
fi

echo "[$(date --iso-8601=seconds)] running post-update verification"
"$SYSTEM_OC" --version | tee "$BACKUP_DIR/version-after.txt"
"$NVM_OC" --version | tee "$BACKUP_DIR/version-nvm-after.txt" || true
"$SYSTEM_OC" update status --json >"$BACKUP_DIR/update-status-after.json"
"$SYSTEM_OC" config validate >"$BACKUP_DIR/config-validate-after.txt" 2>&1
"$SYSTEM_OC" gateway status --deep >"$BACKUP_DIR/gateway-status-after.txt" 2>&1
"$SYSTEM_OC" status >"$BACKUP_DIR/openclaw-status-after.txt" 2>&1
"$SYSTEM_OC" plugins list --verbose --json >"$BACKUP_DIR/plugins-after.json" 2>&1
"$SYSTEM_OC" doctor --post-upgrade --json >"$BACKUP_DIR/doctor-post-upgrade.json" 2>&1 || true
"$SYSTEM_OC" cron list --json >"$BACKUP_DIR/cron-after.json" 2>&1
python3 /root/.openclaw/workspace/scripts/openclaw-update-guard.py --write-report >"$BACKUP_DIR/update-guard-after.txt" 2>&1
python3 /root/.openclaw/workspace/scripts/check-openclaw-runtime-patches.py >"$BACKUP_DIR/runtime-patches-after.txt" 2>&1
systemctl --user show openclaw-gateway.service -p ExecStart -p MainPID -p ActiveEnterTimestamp -p ActiveState -p SubState >"$BACKUP_DIR/systemd-after.txt"

echo "[$(date --iso-8601=seconds)] stable maintenance complete"
trap - EXIT
exit 0
