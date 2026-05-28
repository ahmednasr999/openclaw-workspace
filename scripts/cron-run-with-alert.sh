#!/usr/bin/env bash
set -u

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <task> <lock_path> <log_path> <command> [args...]" >&2
  exit 64
fi

TASK="$1"
LOCK_PATH="$2"
LOG_PATH="$3"
shift 3

STATUS_DIR="/root/.openclaw/workspace/logs/cron/status"
STATUS_PATH="$STATUS_DIR/${TASK}.json"
mkdir -p "$(dirname "$LOCK_PATH")" "$(dirname "$LOG_PATH")" "$STATUS_DIR"

START_ISO="$(date -Is)"
START_EPOCH="$(date +%s)"
HOST="$(hostname 2>/dev/null || echo unknown)"

exec 9>"$LOCK_PATH"
if ! flock -n 9; then
  END_ISO="$(date -Is)"
  END_EPOCH="$(date +%s)"
  DURATION=$((END_EPOCH - START_EPOCH))
  printf '[%s] SKIP %s: lock busy (%s)\n' "$END_ISO" "$TASK" "$LOCK_PATH" >> "$LOG_PATH"
  cat > "$STATUS_PATH" <<EOF
{
  "task": "$TASK",
  "status": "lock_busy",
  "returncode": 0,
  "started_at": "$START_ISO",
  "finished_at": "$END_ISO",
  "duration_seconds": $DURATION,
  "log_path": "$LOG_PATH",
  "lock_path": "$LOCK_PATH",
  "host": "$HOST"
}
EOF
  exit 0
fi

printf '\n[%s] START %s: %s\n' "$START_ISO" "$TASK" "$*" >> "$LOG_PATH"
"$@" >> "$LOG_PATH" 2>&1
RC=$?
END_ISO="$(date -Is)"
END_EPOCH="$(date +%s)"
DURATION=$((END_EPOCH - START_EPOCH))

if [[ $RC -eq 0 ]]; then
  RESULT_STATUS="ok"
else
  RESULT_STATUS="failed"
fi

printf '[%s] END %s: rc=%s duration=%ss\n' "$END_ISO" "$TASK" "$RC" "$DURATION" >> "$LOG_PATH"
cat > "$STATUS_PATH" <<EOF
{
  "task": "$TASK",
  "status": "$RESULT_STATUS",
  "returncode": $RC,
  "started_at": "$START_ISO",
  "finished_at": "$END_ISO",
  "duration_seconds": $DURATION,
  "log_path": "$LOG_PATH",
  "lock_path": "$LOCK_PATH",
  "host": "$HOST"
}
EOF

if [[ $RC -ne 0 && "${CRON_RUNNER_NO_ALERT:-0}" != "1" ]]; then
  MESSAGE="Cron failed: $TASK
Return code: $RC
Host: $HOST
Started: $START_ISO
Finished: $END_ISO
Log: $LOG_PATH"
  openclaw message send --channel telegram --target -1003882622947 --thread-id 10 --message "$MESSAGE" --json >/dev/null 2>&1 || true
fi

exit "$RC"
