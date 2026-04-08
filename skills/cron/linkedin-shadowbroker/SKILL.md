---
name: linkedin-shadowbroker
description: "Monitor specific LinkedIn posts for new comments, track engagement delta, alert on meaningful interactions."
---

# LinkedIn Shadowbroker Monitor

Track engagement on Ahmed's active LinkedIn posts. Alert on new comments needing responses.

## Prerequisites
- Camofox browser for authenticated LinkedIn access
- LinkedIn cookies: `~/.openclaw/cookies/linkedin.txt`

## Steps

### Step 1: Validate cookies
```bash
COOKIE_FILE=~/.openclaw/cookies/linkedin.txt
if [ -f "$COOKIE_FILE" ]; then
    LINES=$(wc -l < "$COOKIE_FILE")
    AGE_DAYS=$(( ($(date +%s) - $(stat -c %Y "$COOKIE_FILE")) / 86400 ))
    echo "Cookies: $LINES lines, ${AGE_DAYS}d old"
    if [ "$LINES" -lt 5 ] || [ "$AGE_DAYS" -gt 14 ]; then
        echo "ABORT: Cookies invalid or stale. Cannot monitor."
        exit 1
    fi
else
    echo "ABORT: No cookie file found"
    exit 1
fi
```

### Step 2: Load previous state
```bash
cat /root/.openclaw/workspace/.watchdog/linkedin-shadowbroker-last.json 2>/dev/null || echo '{"posts": []}'
```

### Step 3: Check target post
Navigate to the LinkedIn post URL (provided in cron context) using Camofox browser.
Capture: likes count, comments count, reposts count.

### Step 4: Compare with last check
Calculate deltas:
- New comments since last check
- New likes since last check
- New reposts since last check

### Step 5: Analyze new comments
For each new comment:
- From a recruiter or hiring manager? Flag as PRIORITY
- A question needing reply? Flag as NEEDS_REPLY
- From a connection? Note for engagement reciprocity

### Step 6: Save state and alert
Save current state to `.watchdog/linkedin-shadowbroker-last.json`.
If priority comments found, alert Telegram.
If no changes, exit silently.

## Error Handling
- If cookies expired: Report "LinkedIn session expired - need fresh cookies"
- If post not found: Report "Post URL may be deleted or private"
- If Camofox unavailable: Report "Browser automation not available"

## Quality Gates
- Must report exact engagement numbers, not estimates
- Must categorize each new comment
- Silent if no changes (don't send empty reports)

## Output Rules
- No em dashes. Hyphens only.
- Only alert if new comments exist. Silent if no changes.
- Include commenter name and comment snippet in alerts.
