#!/usr/bin/env bash
# gmail-check.sh — Check Gmail for important emails
# Runs every 4 hours via OpenClaw cron
# Uses GOG CLI to check Gmail, flags important emails

set -euo pipefail

# Fix: bypass keyring prompt
export GOG_KEYRING_PASSWORD=""

WORKSPACE="/root/.openclaw/workspace"
STATE_FILE="$WORKSPACE/.heartbeat/last_gmail_check.json"
NOW_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
CAIRO_TIME=$(TZ="Africa/Cairo" date +"%H:%M")

# Check if we should skip (quiet hours: 10 PM - 7 AM Cairo)
HOUR_CAIRO=$(TZ="Africa/Cairo" date +"%H" | sed 's/^0//')
if [ "$HOUR_CAIRO" -ge 22 ] || [ "$HOUR_CAIRO" -lt 7 ]; then
  echo "Quiet hours (22:00-07:00 Cairo) — skipping check"
  exit 0
fi

# Use GOG to fetch recent unread emails (last 10)
# Filter for important senders: LinkedIn, recruiters, job portals
echo "Checking Gmail for important emails..."

cd "$WORKSPACE"

# Run gog to list recent emails (search for inbox)
EMAILS=$(gog gmail search "in:inbox is:unread" --max 15 --account ahmednasr999@gmail.com 2>&1 || echo "ERROR: $?")

if echo "$EMAILS" | grep -q "ERROR"; then
  echo "GOG error: $EMAILS"
  exit 1
fi

# Extract and filter for important keywords
IMPORTANT=""
while IFS= read -r line; do
  # Keywords to flag
  if echo "$line" | grep -iqE "(linkedin|recruiter|interview|hiring|job|opportunity|offer|urgent|urgent|apply|career|portal)"; then
    IMPORTANT="$IMPORTANT$line\n"
  fi
done <<< "$EMAILS"

if [ -n "$IMPORTANT" ]; then
  echo "IMPORTANT EMAILS FOUND:"
  echo -e "$IMPORTANT"
  # Store last flagged for dedup
  echo "{\"last_check\":\"$NOW_ISO\",\"flagged\":true}" > "$STATE_FILE"
else
  echo "No important emails found"
  echo "{\"last_check\":\"$NOW_ISO\",\"flagged\":false}" > "$STATE_FILE"
fi
