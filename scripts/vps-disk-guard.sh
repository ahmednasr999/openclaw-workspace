#!/usr/bin/env bash
set -euo pipefail

THRESHOLD="${DISK_GUARD_THRESHOLD:-65}"
ROOT="${DISK_GUARD_MOUNT:-/}"
WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs/disk-guard"
TMP_DIR="$WORKSPACE/tmp"
STATE_FILE="$WORKSPACE/tmp/disk-guard-last-trigger.txt"
mkdir -p "$LOG_DIR" "$TMP_DIR"

now_iso() { date -Is; }
usage_pct() { df -P "$ROOT" | awk 'NR==2 {gsub(/%/,"",$5); print $5}'; }
disk_line() { df -hT "$ROOT" | awk 'NR==2 {print $3 " used / " $5 " / " $6 " free"}'; }

USED_BEFORE="$(usage_pct)"
if [[ "$USED_BEFORE" -lt "$THRESHOLD" ]]; then
  echo "OK: disk ${USED_BEFORE}% below threshold ${THRESHOLD}%"
  exit 0
fi

LOG="$LOG_DIR/cleanup-$(date +%Y%m%d-%H%M%S).log"
{
  echo "Disk guard triggered at $(now_iso)"
  echo "Threshold: ${THRESHOLD}%"
  echo "Before: $(df -hT "$ROOT" | awk 'NR==2 {print $3 " used, " $5 " used%, " $6 " free"}')"

  echo "\nSafe cleanup: workspace tmp files older than 2 days, preserving guard logs and current research markdown."
  find "$TMP_DIR" -xdev -type f -mtime +2 \
    ! -name 'vps-disk-cleanup-*' \
    ! -name 'disk-guard-last-trigger.txt' \
    ! -name 'sharbel-hermes-post.md' \
    -delete 2>/dev/null || true
  find "$TMP_DIR" -xdev -type d -empty -delete 2>/dev/null || true

  echo "\nSafe cleanup: OpenClaw logs older than 7 days."
  find /root/.openclaw -xdev -path '*/logs/*' -type f -mtime +7 -delete 2>/dev/null || true

  echo "\nSafe cleanup: npm/pnpm metadata logs and generic temp caches."
  find /root/.openclaw/plugin-runtime-deps -xdev -type d \( -name '_logs' -o -name '.cache' \) -prune -exec rm -rf {} + 2>/dev/null || true
  rm -rf /root/.cache/pip /root/.cache/ms-playwright /root/.cache/puppeteer 2>/dev/null || true

  if command -v pnpm >/dev/null 2>&1; then
    pnpm store prune || true
  fi
  if command -v npm >/dev/null 2>&1; then
    npm cache clean --force || true
  fi
  if command -v docker >/dev/null 2>&1; then
    docker system prune -af || true
  fi

  echo "\nAfter: $(df -hT "$ROOT" | awk 'NR==2 {print $3 " used, " $5 " used%, " $6 " free"}')"
  echo "Largest remaining /root items:"
  du -xh --max-depth=1 /root 2>/dev/null | sort -h | tail -12 || true
} > "$LOG" 2>&1

USED_AFTER="$(usage_pct)"
echo "$(now_iso) before=${USED_BEFORE}% after=${USED_AFTER}% log=${LOG}" >> "$STATE_FILE"

cat <<EOF
DISK_GUARD_TRIGGERED
before=${USED_BEFORE}%
after=${USED_AFTER}%
threshold=${THRESHOLD}%
log=${LOG}
EOF
