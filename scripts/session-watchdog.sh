#!/usr/bin/env bash
# session-watchdog.sh
# Archives and resets JSONL session files that exceed MAX_SIZE_MB.
# Safe with LCM: real memory lives in lcm.db, JSONL is just the raw append log.
# Runs via cron. Logs to /root/.openclaw/workspace/logs/session-watchdog.log

set -euo pipefail

MAX_SIZE_MB="${SESSION_WATCHDOG_MAX_SIZE_MB:-3}"
SESSION_DIRS_RAW="${SESSION_WATCHDOG_DIRS:-/root/.openclaw/agents/main/sessions:/root/.openclaw/agents/hr/sessions:/root/.openclaw/agents/cto/sessions:/root/.openclaw/agents/cmo/sessions:/root/.openclaw/agents/jobzoom/sessions}"
IFS=':' read -r -a SESSION_DIRS <<< "$SESSION_DIRS_RAW"
LOG="${SESSION_WATCHDOG_LOG:-/root/.openclaw/workspace/logs/session-watchdog.log}"
ARCHIVE_DIR="${SESSION_WATCHDOG_ARCHIVE_DIR:-/root/.openclaw/workspace/logs/session-archives}"
LANE_STALL_DETECTOR="${SESSION_WATCHDOG_LANE_STALL_DETECTOR:-/root/.openclaw/workspace/scripts/agent-lane-stall-report.py}"
LANE_STALL_REPORT="${SESSION_WATCHDOG_LANE_STALL_REPORT:-/root/.openclaw/workspace/reports/agent-lane-stall-latest.md}"

mkdir -p "$ARCHIVE_DIR" "$(dirname "$LOG")"

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" >> "$LOG"; }

RESET_COUNT=0
SKIP_COUNT=0
ERROR_COUNT=0
LANE_STALL_COUNT=0
LANE_STALL_HIGH=0
LANE_STALL_MEDIUM=0

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

if [ -x "$LANE_STALL_DETECTOR" ] || [ -f "$LANE_STALL_DETECTOR" ]; then
  if python3 "$LANE_STALL_DETECTOR" --min-running-minutes 15 --report "$LANE_STALL_REPORT" >/dev/null 2>&1; then
    if [ -f "$LANE_STALL_REPORT" ]; then
      LANE_STALL_LINE=$(grep -E '^Attention needed:' "$LANE_STALL_REPORT" | head -1 || true)
      if [ -n "$LANE_STALL_LINE" ]; then
        LANE_STALL_COUNT=$(printf '%s\n' "$LANE_STALL_LINE" | grep -oE '[0-9]+' | sed -n '1p')
        LANE_STALL_HIGH=$(printf '%s\n' "$LANE_STALL_LINE" | grep -oE 'high=[0-9]+' | grep -oE '[0-9]+' | sed -n '1p')
        LANE_STALL_MEDIUM=$(printf '%s\n' "$LANE_STALL_LINE" | grep -oE 'medium=[0-9]+' | grep -oE '[0-9]+' | sed -n '1p')
        log "ALERT [agent-lane-stall] findings=$LANE_STALL_COUNT high=$LANE_STALL_HIGH medium=$LANE_STALL_MEDIUM report=$LANE_STALL_REPORT"
      else
        log "OK [agent-lane-stall] no CMO/HR stalled or recently interrupted lane sessions"
      fi
    else
      log "ERROR [agent-lane-stall] detector did not create report: $LANE_STALL_REPORT"
      ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
  else
    log "ERROR [agent-lane-stall] detector failed: $LANE_STALL_DETECTOR"
    ERROR_COUNT=$((ERROR_COUNT + 1))
  fi
else
  log "ERROR [agent-lane-stall] detector missing: $LANE_STALL_DETECTOR"
  ERROR_COUNT=$((ERROR_COUNT + 1))
fi

log "Done reset=$RESET_COUNT skipped=$SKIP_COUNT errors=$ERROR_COUNT lane_stalls=$LANE_STALL_COUNT high=$LANE_STALL_HIGH medium=$LANE_STALL_MEDIUM"

if [ "$RESET_COUNT" -gt 0 ] || [ "$ERROR_COUNT" -gt 0 ] || [ "$LANE_STALL_COUNT" -gt 0 ]; then
  echo "session-watchdog: reset=$RESET_COUNT skipped=$SKIP_COUNT errors=$ERROR_COUNT lane_stalls=$LANE_STALL_COUNT high=$LANE_STALL_HIGH medium=$LANE_STALL_MEDIUM report=$LANE_STALL_REPORT"
fi
