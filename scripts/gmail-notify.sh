#!/usr/bin/env bash
# gmail-notify.sh — Check for new unread emails and send Telegram notification
# Runs as OpenClaw cron fallback for when the gmail-watcher lane times out
#
# State file tracks last-seen email ID to avoid duplicate notifications

set -euo pipefail

STATE_FILE="/root/.openclaw/workspace/.watchdog/gmail-last-seen.txt"
ACCOUNT="ahmednasr999@gmail.com"
BOT_TOKEN="8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304"
CHAT_ID="866838380"

export GOG_KEYRING_PASSWORD=""

# Ensure state dir exists
mkdir -p "$(dirname "$STATE_FILE")"

# Get last seen email ID
LAST_SEEN=""
if [[ -f "$STATE_FILE" ]]; then
    LAST_SEEN=$(cat "$STATE_FILE" 2>/dev/null || true)
fi

# Fetch recent unread emails (last 10 minutes window, max 10)
EMAILS=$(gog -a "$ACCOUNT" gmail list "is:unread newer_than:15m -category:promotions -category:social" --max 10 2>/dev/null | tail -n +2 || true)

if [[ -z "$EMAILS" ]]; then
    exit 0
fi

# Parse emails and find new ones
NEW_EMAILS=""
NEWEST_ID=""

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    
    # Extract ID (first field)
    EMAIL_ID=$(echo "$line" | awk '{print $1}')
    
    # Skip if we've seen this or older
    if [[ "$EMAIL_ID" == "$LAST_SEEN" ]]; then
        break
    fi
    
    # Track newest for state update
    if [[ -z "$NEWEST_ID" ]]; then
        NEWEST_ID="$EMAIL_ID"
    fi
    
    # Extract fields
    DATE=$(echo "$line" | awk '{print $2, $3}')
    # FROM is everything between date and subject, tricky to parse
    # Use a simpler approach: grab key fields
    FROM=$(echo "$line" | sed 's/^[^ ]* *[^ ]* *[^ ]* *//' | sed 's/  .*//')
    SUBJECT=$(echo "$line" | awk -F'  +' '{print $4}')
    
    NEW_EMAILS="${NEW_EMAILS}
📧 ${FROM}
${SUBJECT}
${DATE}"
    
done <<< "$EMAILS"

# Nothing new
if [[ -z "$NEW_EMAILS" || -z "$NEWEST_ID" ]]; then
    exit 0
fi

# Update state
echo "$NEWEST_ID" > "$STATE_FILE"

# Send Telegram notification
MSG="📬 New Email(s):
${NEW_EMAILS}"

# Truncate if too long
if [[ ${#MSG} -gt 4000 ]]; then
    MSG="${MSG:0:4000}..."
fi

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=${MSG}" \
    -d "parse_mode=" \
    --max-time 10 > /dev/null 2>&1 || true
