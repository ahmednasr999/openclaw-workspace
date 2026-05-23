#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_VERSION="${OPENCLAW_TARGET_VERSION:-2026.5.20}"
PREVIOUS_VERSION="${OPENCLAW_PREVIOUS_VERSION:-2026.5.19}"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_DIR="/root/.openclaw/workspace/logs"
BACKUP="/root/.openclaw/workspace/backups/openclaw-update-20260523-122740/openclaw-config-state.tgz"
LOG_FILE="$LOG_DIR/openclaw-safe-update-${STAMP}.log"
STATUS_FILE="$LOG_DIR/openclaw-safe-update.latest"
DOCTOR_LOG="$LOG_DIR/openclaw-doctor-after-update-${STAMP}.log"
CHAT_ID="866838380"

mkdir -p "$LOG_DIR"
exec >>"$LOG_FILE" 2>&1

export XDG_RUNTIME_DIR="/run/user/0"
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/0/bus"
export HOME="/root"
export PATH="/root/.local/bin:/root/.npm-global/bin:/root/bin:/root/.nix-profile/bin:/root/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin:/root/.bun/bin:/snap/bin"

write_status() {
  {
    printf 'status=%s\n' "$1"
    printf 'updated_at=%s\n' "$(date -Is)"
    printf 'target_version=%s\n' "$TARGET_VERSION"
    printf 'previous_version=%s\n' "$PREVIOUS_VERSION"
    printf 'log=%s\n' "$LOG_FILE"
    printf 'doctor_log=%s\n' "$DOCTOR_LOG"
    printf 'backup=%s\n' "$BACKUP"
    if [[ "${2:-}" != "" ]]; then
      printf 'detail=%s\n' "$2"
    fi
  } > "$STATUS_FILE"
}

send_telegram() {
  local text="$1"
  openclaw message send \
    --account default \
    --channel telegram \
    --target "$CHAT_ID" \
    --message "$text" \
    --json >/dev/null 2>&1 || true
}

start_gateway() {
  systemctl --user daemon-reload || true
  systemctl --user start openclaw-gateway.service
  for _ in $(seq 1 30); do
    if systemctl --user is-active --quiet openclaw-gateway.service; then
      return 0
    fi
    sleep 2
  done
  return 1
}

rollback() {
  local reason="$1"
  write_status "rolling_back" "$reason"
  echo "[$(date -Is)] rollback: $reason"
  npm install -g "openclaw@${PREVIOUS_VERSION}" --no-audit --no-fund
  start_gateway || true
  write_status "failed_rolled_back" "$reason"
  send_telegram "OpenClaw update failed and I rolled back to ${PREVIOUS_VERSION}.

Reason: ${reason}
Backup: ${BACKUP}
Log: ${LOG_FILE}"
}

main() {
  echo "[$(date -Is)] safe OpenClaw update started"
  write_status "starting"

  if [[ ! -s "$BACKUP" ]]; then
    write_status "failed" "backup_missing"
    send_telegram "OpenClaw update stopped: backup is missing or empty at ${BACKUP}."
    exit 1
  fi

  if ! df -Pk /tmp | awk 'NR==2 { exit ($4 >= 2097152 ? 0 : 1) }'; then
    write_status "failed" "tmp_space_below_2gb"
    send_telegram "OpenClaw update stopped: /tmp has less than 2GB free. No changes were made."
    exit 1
  fi

  echo "[$(date -Is)] before: $(openclaw --version || true)"
  write_status "stopping_gateway"
  systemctl --user stop openclaw-gateway.service

  write_status "updating"
  if ! openclaw update --yes --timeout 600; then
    echo "[$(date -Is)] openclaw update command failed; trying npm fallback"
    if ! npm install -g "openclaw@${TARGET_VERSION}" --no-audit --no-fund; then
      rollback "install_failed"
      exit 1
    fi
  fi

  installed="$(openclaw --version || true)"
  echo "[$(date -Is)] after install: $installed"
  if [[ "$installed" != *"$TARGET_VERSION"* ]]; then
    rollback "version_verify_failed: ${installed}"
    exit 1
  fi

  write_status "starting_gateway"
  if ! start_gateway; then
    rollback "gateway_start_failed_after_update"
    exit 1
  fi

  write_status "running_doctor"
  openclaw doctor --non-interactive > "$DOCTOR_LOG" 2>&1 || true

  write_status "completed" "$installed"
  send_telegram "OpenClaw update completed safely.

Version: ${installed}
Gateway: active
Backup: ${BACKUP}
Doctor log: ${DOCTOR_LOG}"
}

main "$@"
