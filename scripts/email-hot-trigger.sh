#!/bin/bash
# Hot Email Trigger - checks for interview/recruiter emails from pipeline companies
# Runs every 4 hours, sends immediate Telegram alert for urgent matches
# Does NOT replace the morning briefing - this is a fire alarm, not a report

set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
PIPELINE="$WORKSPACE/coordination/pipeline.md"
ALERT_LOG="/tmp/email-hot-trigger-alerted.txt"

# Initialize alert log if missing
touch "$ALERT_LOG"

# Get recent emails (last 4 hours worth)
EMAILS=$(himalaya envelope list --account ahmed --folder INBOX --page-size 20 2>/dev/null || echo "")

if [ -z "$EMAILS" ]; then
    echo "No emails or himalaya failed"
    exit 0
fi

# Extract pipeline company names
COMPANIES=""
if [ -f "$PIPELINE" ]; then
    COMPANIES=$(grep -oP '\| [^|]+ \| [^|]+ \|' "$PIPELINE" | awk -F'|' '{print tolower($2)}' | sed 's/^ *//;s/ *$//' | grep -v '^$' | grep -v '^#' | grep -v '^company' | sort -u)
fi

# Hot keywords in subject
HOT_KEYWORDS="interview|shortlisted|offer|congratulations|selected|phone screen|technical round|final round|assessment invite|next steps in your application"

ALERTS=""

while IFS= read -r line; do
    # Skip header/separator lines
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^\|--  ]] && continue
    [[ "$line" =~ "FLAGS" ]] && continue

    # Extract subject and sender
    SUBJECT=$(echo "$line" | awk -F'|' '{print $4}' | sed 's/^ *//;s/ *$//')
    SENDER=$(echo "$line" | awk -F'|' '{print $5}' | sed 's/^ *//;s/ *$//')
    EMAIL_ID=$(echo "$line" | awk -F'|' '{print $2}' | sed 's/^ *//;s/ *$//')

    [ -z "$SUBJECT" ] && continue

    # Skip if already alerted
    if grep -qF "$EMAIL_ID" "$ALERT_LOG" 2>/dev/null; then
        continue
    fi

    SUBJ_LOWER=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')
    SENDER_LOWER=$(echo "$SENDER" | tr '[:upper:]' '[:lower:]')

    # Check hot keywords
    if echo "$SUBJ_LOWER" | grep -qiE "$HOT_KEYWORDS"; then
        ALERTS="${ALERTS}🚨 HOT: ${SUBJECT} (from: ${SENDER})\n"
        echo "$EMAIL_ID" >> "$ALERT_LOG"
        continue
    fi

    # Check if sender matches pipeline company
    while IFS= read -r company; do
        [ -z "$company" ] && continue
        [ ${#company} -lt 4 ] && continue
        if echo "$SENDER_LOWER" | grep -qF "$company"; then
            ALERTS="${ALERTS}📧 Pipeline match: ${SUBJECT} from ${SENDER} (company: ${company})\n"
            echo "$EMAIL_ID" >> "$ALERT_LOG"
            break
        fi
    done <<< "$COMPANIES"

done <<< "$EMAILS"

if [ -n "$ALERTS" ]; then
    echo "🚨 URGENT EMAIL ALERT"
    echo ""
    echo -e "$ALERTS"
    echo "Check your inbox immediately."
else
    echo "No urgent emails found."
fi

# Decision 4: LinkedIn post watchdog cross-check (runs at 11 AM+ Cairo)
HOUR=$(TZ=Africa/Cairo date +%H)
WATCHDOG="$WORKSPACE/data/linkedin-watchdog.json"
if [ "$HOUR" -ge 11 ] && [ -f "$WATCHDOG" ]; then
    CREATED=$(python3 -c "
import json, sys
from datetime import datetime
try:
    d = json.load(open('$WATCHDOG'))
    created = datetime.fromisoformat(d['created_at'])
    age = (datetime.now() - created).total_seconds() / 3600
    if age > 1.5:
        print(f\"STALE:{d.get('title','Unknown')}:{age:.0f}h\")
except: pass
" 2>/dev/null)
    if [[ "$CREATED" == STALE:* ]]; then
        STALE_TITLE=$(echo "$CREATED" | cut -d: -f2)
        STALE_AGE=$(echo "$CREATED" | cut -d: -f3)
        echo ""
        echo "🔴 LinkedIn post FAILED to publish!"
        echo "Title: $STALE_TITLE"
        echo "Prepared ${STALE_AGE} ago but never posted."
        echo "Check /tmp/linkedin-post-payload.json and post manually."
    fi
fi

# Cleanup: keep only last 200 entries in alert log
if [ -f "$ALERT_LOG" ] && [ $(wc -l < "$ALERT_LOG") -gt 200 ]; then
    tail -100 "$ALERT_LOG" > "$ALERT_LOG.tmp" && mv "$ALERT_LOG.tmp" "$ALERT_LOG"
fi
