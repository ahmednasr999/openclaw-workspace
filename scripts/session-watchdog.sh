#!/usr/bin/env bash
# session-watchdog.sh
# Archives and resets JSONL session files that exceed MAX_SIZE_MB.
# Safe with LCM: real memory lives in lcm.db, JSONL is just the raw append log.
# Runs via cron. Logs to /root/.openclaw/workspace/logs/session-watchdog.log

MAX_SIZE_MB=3
SESSION_DIRS=(
  /root/.openclaw/agents/main/sessions
  /root/.openclaw/agents/hr/sessions
  /root/.openclaw/agents/cto/sessions
  /root/.openclaw/agents/cmo/sessions
)
LOG=/root/.openclaw/workspace/logs/session-watchdog.log
ARCHIVE_DIR=/root/.openclaw/workspace/logs/session-archives

mkdir -p "$ARCHIVE_DIR"

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG"; }

RESET_COUNT=0
SKIP_COUNT=0

for DIR in "${SESSION_DIRS[@]}"; do
  [ -d "$DIR" ] || continue
  while IFS= read -r -d '' FILE; do
    SIZE_MB=$(du -m "$FILE" | cut -f1)
    BASENAME=$(basename "$FILE")
    AGENT=$(basename "$(dirname "$DIR")")

    # Skip if locked by a live process
    LOCKFILE="${FILE}.lock"
    if [ -f "$LOCKFILE" ]; then
      LOCK_PID=$(python3 -c "import json,sys; d=json.load(open('$LOCKFILE')); print(d.get('pid',''))" 2>/dev/null)
      if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        log "SKIP [$AGENT] $BASENAME — locked by live PID $LOCK_PID (${SIZE_MB}MB)"
        ((SKIP_COUNT++))
        continue
      fi
    fi

    if [ "$SIZE_MB" -ge "$MAX_SIZE_MB" ]; then
      ARCHIVE_NAME="${ARCHIVE_DIR}/${BASENAME%.jsonl}.$(date -u '+%Y%m%dT%H%M%SZ').jsonl.gz"
      gzip -c "$FILE" > "$ARCHIVE_NAME"
      > "$FILE"  # truncate in place (preserve inode)
      log "RESET [$AGENT] $BASENAME — was ${SIZE_MB}MB → archived to $(basename "$ARCHIVE_NAME")"
      ((RESET_COUNT++))
    fi
  done < <(find "$DIR" -maxdepth 1 -name "*.jsonl" -not -name "*.reset.*" -print0 2>/dev/null)
done

log "Done — reset=$RESET_COUNT skipped=$SKIP_COUNT"
