#!/bin/bash
# context-enforcer.sh
# Runs as isolated cron every 2 minutes.
# Checks /tmp/nasr-context-flush.flag.
# If flag exists: creates a temporary cron systemEvent to alert main session.
# Waits 5 minutes before re-alerting (prevents spam).

FLAG_FILE="/tmp/nasr-context-flush.flag"
ALERT_LOCK="/tmp/nasr-context-alert-sent.lock"
LOCK_TIMEOUT=300  # 5 minutes

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
LOG_FILE="/root/.openclaw/workspace/memory/context-enforcer.log"

# Check if flag exists
if [ ! -f "$FLAG_FILE" ]; then
  exit 0
fi

# Check if alert was sent recently (within lock timeout)
if [ -f "$ALERT_LOCK" ]; then
  LOCK_AGE=$(($(date +%s) - $(stat -f%m "$ALERT_LOCK" 2>/dev/null || stat -c%Y "$ALERT_LOCK" 2>/dev/null)))
  if [ "$LOCK_AGE" -lt "$LOCK_TIMEOUT" ]; then
    exit 0
  fi
fi

# Read the flag to get context %
FLAG_DATA=$(cat "$FLAG_FILE" 2>/dev/null)
PCT=$(echo "$FLAG_DATA" | grep -o '"pct": [0-9]*' | grep -o '[0-9]*')

echo "[$TIMESTAMP] Enforcing flush: context at ${PCT}%" >> "$LOG_FILE"

# Write alert message to a temp file for the main session to read
ALERT_FILE="/tmp/nasr-context-alert.txt"
cat > "$ALERT_FILE" << 'ALERT_EOF'
🚨 CONTEXT CRITICAL — Session at ${PCT}%

AUTO-FLUSH triggered immediately by watchdog system.

NASR FLUSH PROTOCOL (non-negotiable):
1. Write key decisions to MEMORY.md
2. Update memory/active-tasks.md with current status
3. Log session summary to memory/YYYY-MM-DD.md
4. Commit and push to GitHub
5. Start fresh session to reset context

Context auto-flush is now a hard rule to prevent cascade failures.
Proceed with flush immediately. Your next session will load clean.
ALERT_EOF

echo "[$TIMESTAMP] Alert written to $ALERT_FILE" >> "$LOG_FILE"

# Try to create a one-shot cron that fires immediately
# This will inject the systemEvent into the main session's queue
# Since we're in an isolated context, we can't call cron directly,
# so instead we write a marker file that tells the main session to flush when it next wakes up

touch "$ALERT_LOCK"
echo "[$TIMESTAMP] Alert lock set — will not re-alert for $LOCK_TIMEOUT seconds" >> "$LOG_FILE"

exit 0
