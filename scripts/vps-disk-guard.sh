#!/usr/bin/env bash
set -euo pipefail

THRESHOLD="${DISK_GUARD_THRESHOLD:-75}"
ROOT="${DISK_GUARD_MOUNT:-/}"
WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs/disk-guard"
TMP_DIR="$WORKSPACE/tmp"
STATE_FILE="$WORKSPACE/tmp/disk-guard-last-trigger.txt"
BACKUP_WARN_GB="${DISK_GUARD_BACKUP_WARN_GB:-8}"
BACKUP_KEEP_DAYS="${DISK_GUARD_BACKUP_KEEP_DAYS:-14}"
BACKUP_PRUNE="${DISK_GUARD_PRUNE_BACKUPS:-0}"
SAFE_TMP_AGE_DAYS="${DISK_GUARD_SAFE_TMP_AGE_DAYS:-3}"
COMPILE_CACHE_AGE_DAYS="${DISK_GUARD_COMPILE_CACHE_AGE_DAYS:-0}"
HERMES_FRAME_MIN_AGE_MINUTES="${DISK_GUARD_HERMES_FRAME_MIN_AGE_MINUTES:-120}"
mkdir -p "$LOG_DIR" "$TMP_DIR"

now_iso() { date -Is; }
usage_pct() { df -P "$ROOT" | awk 'NR==2 {gsub(/%/,"",$5); print $5}'; }
disk_line() { df -hT "$ROOT" | awk 'NR==2 {print $4 " used / " $5 " free / " $6 " used"}'; }
backup_warn_bytes() { awk -v gb="$BACKUP_WARN_GB" 'BEGIN {printf "%.0f", gb * 1024 * 1024 * 1024}'; }

backup_report() {
  local warn_bytes
  warn_bytes="$(backup_warn_bytes)"
  echo "Backup/snapshot audit: files >= ${BACKUP_WARN_GB}G or older than ${BACKUP_KEEP_DAYS} days."
  find /root/openclaw-backups /root/.openclaw/backups -xdev \
    \( -type f \( -name '*.tar.gz' -o -name '*.tar.zst' \) -o -type d -name 'manual-update-*' \) \
    \( -size +"${warn_bytes}"c -o -mtime +"${BACKUP_KEEP_DAYS}" \) \
    -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' 2>/dev/null | sort || true
  find /root -xdev -maxdepth 1 -type d -name 'openclaw-snapshot-*' \
    \( -mtime +"${BACKUP_KEEP_DAYS}" -o -size +"${warn_bytes}"c \) \
    -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' 2>/dev/null | sort || true
  find /root -xdev -maxdepth 1 -type f -name 'openclaw-snapshot-*.tar.zst' \
    \( -mtime +"${BACKUP_KEEP_DAYS}" -o -size +"${warn_bytes}"c \) \
    -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' 2>/dev/null | sort || true
}

snapshot_lock_active() {
  local pid
  if [[ ! -f /tmp/openclaw-daily-snapshot.lock ]]; then
    return 1
  fi
  pid="$(cat /tmp/openclaw-daily-snapshot.lock 2>/dev/null || true)"
  [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null
}

compress_snapshot_dirs() {
  local dir archive tmp_archive base
  local -a snapshots archives

  mapfile -t snapshots < <(find /root -xdev -maxdepth 1 -type d -name 'openclaw-snapshot-*' -printf '%T@ %p\n' 2>/dev/null | sort -nr | awk '{$1=""; sub(/^ /,""); print}')
  if (( ${#snapshots[@]} == 0 )); then
    echo "No uncompressed OpenClaw snapshot directories found."
    return 0
  fi

  if snapshot_lock_active; then
    echo "Daily snapshot is currently running; skipping snapshot compression this pass."
    return 0
  fi
  if ! command -v tar >/dev/null 2>&1 || ! command -v zstd >/dev/null 2>&1; then
    echo "tar/zstd unavailable; skipping snapshot compression."
    return 0
  fi

  for dir in "${snapshots[@]}"; do
    [[ -d "$dir" ]] || continue
    archive="${dir}.tar.zst"
    tmp_archive="${archive}.tmp"
    base="$(basename "$dir")"

    if [[ ! -s "$archive" ]]; then
      echo "Compressing $dir -> $archive"
      rm -f -- "$tmp_archive"
      if tar -C /root --use-compress-program='zstd -T0 -6' -cf "$tmp_archive" "$base" \
        && tar -I zstd -tf "$tmp_archive" >/dev/null; then
        mv -f -- "$tmp_archive" "$archive"
      else
        echo "Compression verification failed for $dir; preserving directory."
        rm -f -- "$tmp_archive"
        continue
      fi
    else
      echo "Verified existing archive for $dir: $archive"
      if ! tar -I zstd -tf "$archive" >/dev/null; then
        echo "Existing archive failed verification; preserving directory."
        continue
      fi
    fi

    rm -rf --one-file-system "$dir"
    echo "Removed uncompressed snapshot directory: $dir"
  done

  mapfile -t archives < <(find /root -xdev -maxdepth 1 -type f -name 'openclaw-snapshot-*.tar.zst' -printf '%T@ %p\n' 2>/dev/null | sort -nr | awk '{$1=""; sub(/^ /,""); print}')
  if (( ${#archives[@]} > 2 )); then
    printf '%s\n' "${archives[@]:2}" | xargs -r rm -f --
    echo "Pruned older compressed snapshot archives; kept latest 2."
  fi
}

clean_hermes_rebuildable_artifacts() {
  if [[ ! -d /srv/hermes-pilot ]]; then
    echo "Hermes workspace not present."
    return 0
  fi

  find /srv/hermes-pilot/workspace -xdev -maxdepth 1 -type d -name 'agent_roadmap*_frames' -mmin +"$HERMES_FRAME_MIN_AGE_MINUTES" \
    -print -exec rm -rf --one-file-system {} + 2>/dev/null || true
  find /srv/hermes-pilot/.cache -xdev -mindepth 1 -maxdepth 1 \
    \( -name 'ms-playwright' -o -name 'pip' -o -name 'uv' \) \
    -print -exec rm -rf --one-file-system {} + 2>/dev/null || true
}

prune_backup_candidates() {
  # Destructive backup pruning is opt-in. Keep disabled unless Ahmed explicitly approves
  # this behavior, because these files may be rollback points for gateway updates.
  if [[ "$BACKUP_PRUNE" != "1" ]]; then
    echo "Backup pruning disabled. Set DISK_GUARD_PRUNE_BACKUPS=1 only after explicit approval."
    return 0
  fi

  local warn_bytes
  warn_bytes="$(backup_warn_bytes)"
  echo "Pruning backup/snapshot candidates older than ${BACKUP_KEEP_DAYS} days or larger than ${BACKUP_WARN_GB}G."
  find /root/openclaw-backups /root/.openclaw/backups -xdev \
    \( -type f \( -name '*.tar.gz' -o -name '*.tar.zst' \) -o -type d -name 'manual-update-*' \) \
    \( -size +"${warn_bytes}"c -o -mtime +"${BACKUP_KEEP_DAYS}" \) \
    -exec rm -rf --one-file-system {} + 2>/dev/null || true
  find /root -xdev -maxdepth 1 -type d -name 'openclaw-snapshot-*' \
    \( -mtime +"${BACKUP_KEEP_DAYS}" -o -size +"${warn_bytes}"c \) \
    -exec rm -rf --one-file-system {} + 2>/dev/null || true
}

if [[ "${1:-}" == "--audit-backups" ]]; then
  backup_report
  exit 0
fi

USED_BEFORE="$(usage_pct)"
if [[ "$USED_BEFORE" -lt "$THRESHOLD" ]]; then
  echo "OK: disk ${USED_BEFORE}% below threshold ${THRESHOLD}%"
  exit 0
fi

LOG="$LOG_DIR/cleanup-$(date +%Y%m%d-%H%M%S).log"
{
  echo "Disk guard triggered at $(now_iso)"
  echo "Threshold: ${THRESHOLD}%"
  echo "Before: $(disk_line)"

  printf '\nSafe cleanup: workspace tmp files older than 2 days, preserving guard logs and current research markdown.\n'
  find "$TMP_DIR" -xdev -type f -mtime +2 \
    ! -name 'vps-disk-cleanup-*' \
    ! -name 'disk-guard-last-trigger.txt' \
    ! -name 'sharbel-hermes-post.md' \
    -delete 2>/dev/null || true
  find "$TMP_DIR" -xdev -type d -empty -delete 2>/dev/null || true

  printf '\nSafe cleanup: OpenClaw logs older than 7 days.\n'
  find /root/.openclaw -xdev -path '*/logs/*' -type f -mtime +7 -delete 2>/dev/null || true
  find "$LOG_DIR" -xdev -type f -name 'cleanup-*.log' -mtime +30 -delete 2>/dev/null || true

  printf '\nSafe cleanup: stale system temp files older than %s days.\n' "$SAFE_TMP_AGE_DAYS"
  find /tmp /var/tmp -xdev -mindepth 1 -maxdepth 1 \
    \( -name 'systemd-private-*' -o -name '.X11-unix' -o -name '.ICE-unix' -o -name '.font-unix' \) -prune -o \
    -mtime +"$SAFE_TMP_AGE_DAYS" -exec rm -rf --one-file-system {} + 2>/dev/null || true

  printf '\nSafe cleanup: OpenClaw compile cache entries older than %s days.\n' "$COMPILE_CACHE_AGE_DAYS"
  find /var/tmp/openclaw-compile-cache -xdev -mindepth 1 -mtime +"$COMPILE_CACHE_AGE_DAYS" \
    -exec rm -rf --one-file-system {} + 2>/dev/null || true

  printf '\nSafe cleanup: Hermes rebuildable browser cache and stale generated frame folders.\n'
  clean_hermes_rebuildable_artifacts

  printf '\nSafe cleanup: apt package download caches.\n'
  apt-get clean >/dev/null 2>&1 || true
  apt-get autoclean >/dev/null 2>&1 || true

  printf '\nSafe cleanup: npm/pnpm metadata logs and generic temp caches.\n'
  find /root/.openclaw/plugin-runtime-deps -xdev -type d \( -name '_logs' -o -name '.cache' \) -prune -exec rm -rf {} + 2>/dev/null || true
  rm -rf /root/.cache/pip /root/.cache/ms-playwright /root/.cache/puppeteer /root/.npm/_npx 2>/dev/null || true

  if command -v pnpm >/dev/null 2>&1; then
    pnpm store prune || true
  fi
  if command -v npm >/dev/null 2>&1; then
    npm cache clean --force || true
  fi
  if command -v docker >/dev/null 2>&1; then
    docker system prune -af || true
  fi

  printf '\nSafe cleanup: compress verified OpenClaw snapshot directories, then keep latest 2 compressed archives.\n'
  compress_snapshot_dirs

  printf '\nBackup/snapshot audit, no destructive pruning by default.\n'
  backup_report
  prune_backup_candidates

  printf '\nAfter: %s\n' "$(disk_line)"
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
