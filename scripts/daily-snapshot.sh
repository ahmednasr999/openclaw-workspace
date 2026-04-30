#!/bin/bash
# Daily local snapshot - lightweight OpenClaw state snapshot.
# Runs at 1AM Cairo (23:00 UTC). Keeps last 2 snapshots.
# Excludes heavy/rebuildable/runtime backup directories to avoid backup-in-backup disk growth.

set -euo pipefail
DATE=$(date +%Y%m%d)
SRC="/root/.openclaw"
DEST="/root/openclaw-snapshot-${DATE}"
LOCK_FILE="/tmp/openclaw-daily-snapshot.lock"

log() { echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $*"; }

if [ -f "$LOCK_FILE" ]; then
  old_pid=$(cat "$LOCK_FILE" 2>/dev/null || true)
  if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
    log "SKIP: snapshot already running (PID $old_pid)"
    exit 0
  fi
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

log "Snapshot started"
rm -rf --one-file-system "$DEST"
mkdir -p "$DEST"

rsync -a --delete \
  --exclude 'backups/' \
  --exclude 'media/' \
  --exclude 'browser/' \
  --exclude 'plugin-runtime-deps/' \
  --exclude 'lcm-files/' \
  --exclude 'logs/' \
  --exclude 'node_modules/' \
  --exclude '.cache/' \
  "$SRC/" "$DEST/"

log "OpenClaw snapshot written: $DEST ($(du -sh "$DEST" | awk '{print $1}'))"

cd /root
ls -1dt openclaw-snapshot-* 2>/dev/null | tail -n +3 | xargs -r rm -rf --one-file-system
log "Snapshot retention complete: kept last 2 snapshots"
log "Snapshot complete"
