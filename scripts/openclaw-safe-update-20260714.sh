#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_VERSION="2026.7.1"
BACKUP_DIR="/root/.openclaw/backups/openclaw-update-20260714-111403"
WORKSPACE="/root/.openclaw/workspace"
STATUS_FILE="$WORKSPACE/logs/openclaw-stable-update.latest"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$WORKSPACE/logs/openclaw-stable-update-$STAMP.log"
GUARD_FILE="$WORKSPACE/logs/openclaw-stable-update-guard-$STAMP.json"

export HOME=/root
export XDG_RUNTIME_DIR=/run/user/0
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/0/bus
export PATH=/usr/bin:/bin:/usr/local/bin:/root/.local/bin
unset OPENCLAW_SERVICE_MARKER OPENCLAW_SERVICE_KIND OPENCLAW_GATEWAY_SERVICE_PID

mkdir -p "$WORKSPACE/logs"
exec >>"$LOG_FILE" 2>&1

write_status() {
  local state="$1"
  local detail="${2:-}"
  local tmp="${STATUS_FILE}.tmp"
  {
    printf 'status=%s\n' "$state"
    printf 'updated_at=%s\n' "$(date -Is)"
    printf 'target_version=%s\n' "$TARGET_VERSION"
    printf 'detail=%s\n' "$detail"
    printf 'log=%s\n' "$LOG_FILE"
    printf 'backup=%s\n' "$BACKUP_DIR"
    printf 'guard=%s\n' "$GUARD_FILE"
  } >"$tmp"
  mv "$tmp" "$STATUS_FILE"
}

wait_for_gateway() {
  local expected="$1"
  for _ in $(seq 1 45); do
    if systemctl --user is-active --quiet openclaw-gateway.service; then
      if /usr/bin/openclaw gateway probe --json >"$WORKSPACE/logs/openclaw-stable-update-probe-$STAMP.json" 2>&1; then
        /usr/bin/openclaw gateway status --deep >"$WORKSPACE/logs/openclaw-stable-update-gateway-$STAMP.txt" 2>&1 || true
        if /usr/bin/openclaw gateway status --deep 2>&1 | grep -Fq "Gateway version: $expected"; then
          return 0
        fi
      fi
    fi
    sleep 2
  done
  return 1
}

restore_beta6() {
  echo "[$(date -Is)] rolling back to backed-up beta.6 runtime"
  systemctl --user stop openclaw-gateway.service || true
  rm -rf /usr/lib/node_modules/openclaw
  tar -xzf "$BACKUP_DIR/runtime-package-beta6.tgz" -C /usr/lib/node_modules
  cp -a "$BACKUP_DIR/openclaw.json" /root/.openclaw/openclaw.json
  cp -a "$BACKUP_DIR/openclaw-gateway.service" /root/.config/systemd/user/openclaw-gateway.service
  systemctl --user daemon-reload
  systemctl --user start openclaw-gateway.service
  wait_for_gateway "2026.7.1-beta.6" || true
}

fail_and_rollback() {
  local reason="$1"
  echo "[$(date -Is)] FAILURE: $reason"
  write_status rolling_back "$reason"
  restore_beta6
  write_status failed_rolled_back "$reason"
  exit 1
}

main() {
  echo "[$(date -Is)] detached stable update started"
  write_status starting

  [[ -s "$BACKUP_DIR/runtime-package-beta6.tgz" ]] || fail_and_rollback backup_missing
  [[ -s "$BACKUP_DIR/sqlite/lcm.db" ]] || fail_and_rollback sqlite_backup_missing
  df -Pk /tmp | awk 'NR==2 { exit ($4 >= 2097152 ? 0 : 1) }' || fail_and_rollback tmp_space_below_2gb

  write_status stopping_gateway
  systemctl --user stop openclaw-gateway.service || fail_and_rollback gateway_stop_failed

  write_status updating
  if ! /usr/bin/openclaw update --channel stable --yes --no-restart --timeout 1800 --json; then
    fail_and_rollback update_command_failed
  fi

  installed="$(/usr/bin/openclaw --version 2>&1 || true)"
  echo "[$(date -Is)] installed: $installed"
  [[ "$installed" == *"$TARGET_VERSION"* ]] || fail_and_rollback version_verify_failed

  write_status reapplying_runtime_patches "$installed"
  if ! python3 "$WORKSPACE/scripts/reapply-openclaw-2026-5-18-runtime-patches.py"; then
    echo "[$(date -Is)] patch reapply returned nonzero; checking whether stable already contains required behavior"
  fi
  python3 "$WORKSPACE/scripts/check-openclaw-runtime-patches.py" || fail_and_rollback runtime_patch_check_failed
  /usr/bin/openclaw config validate || fail_and_rollback config_validation_failed

  write_status starting_gateway "$installed"
  systemctl --user daemon-reload
  systemctl --user start openclaw-gateway.service || fail_and_rollback gateway_start_failed
  wait_for_gateway "$TARGET_VERSION" || fail_and_rollback gateway_health_failed

  write_status verifying "$installed"
  /usr/bin/openclaw plugins list --verbose --json >"$WORKSPACE/logs/openclaw-stable-update-plugins-$STAMP.json" || fail_and_rollback plugin_check_failed
  /usr/bin/openclaw cron list --json >"$WORKSPACE/logs/openclaw-stable-update-cron-$STAMP.json" || fail_and_rollback cron_check_failed
  /usr/bin/openclaw status --json >"$WORKSPACE/logs/openclaw-stable-update-status-$STAMP.json" || fail_and_rollback runtime_status_failed
  python3 "$WORKSPACE/scripts/openclaw-update-guard.py" --write-report --json >"$GUARD_FILE" || guard_rc=$?
  guard_rc="${guard_rc:-0}"
  if [[ "$guard_rc" -ne 0 && "$guard_rc" -ne 2 ]]; then
    fail_and_rollback update_guard_failed
  fi
  if ! grep -Eq '"verdict": "(PASS|WARN)"' "$GUARD_FILE"; then
    fail_and_rollback update_guard_invalid
  fi

  write_status completed "$installed"
  echo "[$(date -Is)] stable update completed"
}

main "$@"
