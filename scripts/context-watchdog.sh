#!/bin/bash
# context-watchdog.sh
# Checks main session context usage via 'openclaw status' CLI.
# If >= 75%, writes flag file for enforcement cron to pick up.
# Runs as isolated cron every 5 minutes.

FLAG_FILE="/tmp/nasr-context-flush.flag"
LOG_FILE="/root/.openclaw/workspace/memory/context-watchdog.log"
THRESHOLD=75

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Parse 'openclaw status' output for Context line
# Expected format: "Context: 181k/200k (91%)"
STATUS_OUTPUT=$(openclaw status 2>/dev/null)

if [ -z "$STATUS_OUTPUT" ]; then
  echo "[$TIMESTAMP] ERROR: openclaw status command failed" >> "$LOG_FILE"
  exit 1
fi

# Extract percentage from "Context: XXXk/XXXk (NN%)" pattern
CONTEXT_PCT=$(echo "$STATUS_OUTPUT" | grep -oP '(?<=\()(\d+)(?=%\))' | head -1)

if [ -z "$CONTEXT_PCT" ]; then
  echo "[$TIMESTAMP] WARNING: Could not parse context%. Full status:" >> "$LOG_FILE"
  echo "$STATUS_OUTPUT" >> "$LOG_FILE"
  exit 0
fi

echo "[$TIMESTAMP] Context: ${CONTEXT_PCT}%" >> "$LOG_FILE"

# Check threshold
if [ "$CONTEXT_PCT" -ge "$THRESHOLD" ]; then
  echo "{\"pct\": $CONTEXT_PCT, \"ts\": \"$TIMESTAMP\"}" > "$FLAG_FILE"
  echo "[$TIMESTAMP] ALERT: ${CONTEXT_PCT}% >= ${THRESHOLD}% — flag set" >> "$LOG_FILE"
  exit 2  # exit code = threshold exceeded
else
  # Clean up flag if recovered
  rm -f "$FLAG_FILE"
  exit 0
fi
