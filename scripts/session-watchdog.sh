#!/usr/bin/env bash
# session-watchdog.sh
# Archives and resets JSONL session files that exceed MAX_SIZE_MB.
# Safe with LCM: real memory lives in lcm.db, JSONL is just the raw append log.
# Runs via cron. Logs to /root/.openclaw/workspace/logs/session-watchdog.log

set -euo pipefail

MAX_SIZE_MB="${SESSION_WATCHDOG_MAX_SIZE_MB:-3}"
SESSION_DIRS_RAW="${SESSION_WATCHDOG_DIRS:-/root/.openclaw/agents/main/sessions:/root/.openclaw/agents/hr/sessions:/root/.openclaw/agents/cto/sessions:/root/.openclaw/agents/cmo/sessions}"
IFS=':' read -r -a SESSION_DIRS <<< "$SESSION_DIRS_RAW"
LOG="${SESSION_WATCHDOG_LOG:-/root/.openclaw/workspace/logs/session-watchdog.log}"
ARCHIVE_DIR="${SESSION_WATCHDOG_ARCHIVE_DIR:-/root/.openclaw/workspace/logs/session-archives}"

mkdir -p "$ARCHIVE_DIR" "$(dirname "$LOG")"

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" >> "$LOG"; }

RESET_COUNT=0
SKIP_COUNT=0
ERROR_COUNT=0

for DIR in "${SESSION_DIRS[@]}"; do
  [ -d "$DIR" ] || continue
  while IFS= read -r -d '' FILE; do
    SIZE_MB=$(du -m "$FILE" | cut -f1)
    BASENAME=$(basename "$FILE")
    AGENT=$(basename "$(dirname "$DIR")")

    LOCKFILE="${FILE}.lock"
    if [ -f "$LOCKFILE" ]; then
      LOCK_PID=$(python3 -c "import json,sys; d=json.load(open('$LOCKFILE')); print(d.get('pid',''))" 2>/dev/null || true)
      if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        log "SKIP [$AGENT] $BASENAME locked by live PID $LOCK_PID (${SIZE_MB}MB)"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
      fi
      log "INFO [$AGENT] $BASENAME stale lock ignored"
    fi

    if [ "$SIZE_MB" -ge "$MAX_SIZE_MB" ]; then
      ARCHIVE_NAME="${ARCHIVE_DIR}/${BASENAME%.jsonl}.$(date -u '+%Y%m%dT%H%M%SZ').jsonl.gz"
      if gzip -c "$FILE" > "$ARCHIVE_NAME" && [ -s "$ARCHIVE_NAME" ]; then
        : > "$FILE"
        log "RESET [$AGENT] $BASENAME was ${SIZE_MB}MB -> archived to $(basename "$ARCHIVE_NAME")"
        RESET_COUNT=$((RESET_COUNT + 1))
      else
        rm -f "$ARCHIVE_NAME"
        log "ERROR [$AGENT] $BASENAME archive failed (${SIZE_MB}MB)"
        ERROR_COUNT=$((ERROR_COUNT + 1))
      fi
    fi
  done < <(find "$DIR" -maxdepth 1 -name "*.jsonl" -not -name "*.reset.*" -print0 2>/dev/null)
done

log "Done reset=$RESET_COUNT skipped=$SKIP_COUNT errors=$ERROR_COUNT"

if [ "$RESET_COUNT" -gt 0 ] || [ "$ERROR_COUNT" -gt 0 ]; then
  echo "session-watchdog: reset=$RESET_COUNT skipped=$SKIP_COUNT errors=$ERROR_COUNT"
fi
