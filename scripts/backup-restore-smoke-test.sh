#!/usr/bin/env bash
set -Eeuo pipefail

WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs/cron"
BACKUP_LOG="$WORKSPACE/logs/cron/daily-backup.log"
LEGACY_BACKUP_LOG="$WORKSPACE/logs/openclaw-backup.log"
ARCHIVE_DIR="/root/openclaw-backups"
mkdir -p "$LOG_DIR"

fail=0
echo "Backup/snapshot smoke test started at $(date -Is)"

if [[ ! -s "$BACKUP_LOG" && -s "$LEGACY_BACKUP_LOG" ]]; then
  BACKUP_LOG="$LEGACY_BACKUP_LOG"
fi

if [[ -s "$BACKUP_LOG" ]] && find "$BACKUP_LOG" -mtime -8 -print -quit | grep -q .; then
  if grep -q "SUCCESS: Pushed to origin workspace-sync" "$BACKUP_LOG"; then
    echo "OK: recent workspace backup log has a successful push"
  else
    echo "WARN: backup log exists but no successful push marker was found"
    fail=1
  fi
else
  echo "FAIL: backup log is missing, empty, or older than 8 days: $BACKUP_LOG"
  fail=1
fi

latest_snapshot="$(find /root -maxdepth 1 -type d -name 'openclaw-snapshot-*' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
if [[ -n "$latest_snapshot" && -r "$latest_snapshot" ]]; then
  if find "$latest_snapshot" -mindepth 1 -maxdepth 2 -print -quit | grep -q .; then
    echo "OK: latest snapshot is readable: $latest_snapshot"
    du -sh "$latest_snapshot" 2>/dev/null || true
  else
    echo "FAIL: latest snapshot exists but appears empty: $latest_snapshot"
    fail=1
  fi
else
  latest_archive="$(find "$ARCHIVE_DIR" -maxdepth 1 -type f -name 'openclaw-*.tar.gz' -mtime -8 -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
  if [[ -n "$latest_archive" && -r "$latest_archive" ]]; then
    if gzip -t "$latest_archive" && tar -tzf "$latest_archive" .openclaw/openclaw.json .openclaw/workspace/MEMORY.md >/dev/null 2>&1; then
      echo "OK: no raw snapshot found, but recent compressed backup archive passed integrity checks: $latest_archive"
      du -sh "$latest_archive" 2>/dev/null || true
    else
      echo "FAIL: recent compressed backup archive failed integrity checks: $latest_archive"
      fail=1
    fi
  else
    echo "FAIL: no readable openclaw snapshot directory or recent compressed backup archive found"
    fail=1
  fi
fi

echo "Backup/snapshot smoke test finished at $(date -Is)"
exit "$fail"
