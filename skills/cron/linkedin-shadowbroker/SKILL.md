---
name: linkedin-shadowbroker
description: "Monitor specific LinkedIn posts for new comments, track engagement, and alert on meaningful interactions."
---

# LinkedIn Shadowbroker Monitor

Track engagement on Ahmed's active LinkedIn posts. Alert on new comments that need responses.

## Prerequisites
- Camofox browser or LinkedIn cookies for authenticated access
- LinkedIn skill: `skills/linkedin/SKILL.md` for browser automation patterns

## Steps

### Step 1: Check the target post
Navigate to the LinkedIn post URL provided in cron context.

### Step 2: Scrape current engagement
Capture: likes count, comments count, reposts count, impressions if visible.

### Step 3: Compare with last check
Read previous state from `.watchdog/linkedin-shadowbroker-last.json`.
Detect new comments since last check.

### Step 4: Analyze new comments
For each new comment:
- Is it from a recruiter or hiring manager? → Flag as priority
- Is it a question? → Flag as needs reply
- Is it from a connection? → Note for engagement reciprocity

### Step 5: Alert if needed
If priority comments found, send Telegram alert:
"💬 [X] new comments on your post. [Y] need replies. Top: [commenter - snippet]"

### Step 6: Save state
Update `.watchdog/linkedin-shadowbroker-last.json` with current counts.

## Error Handling
- If LinkedIn login required: Report "LinkedIn session expired"
- If post not found: Report "Post URL may be deleted or private"
- If rate limited: Wait and retry once

## Output Rules
- No em dashes. Hyphens only.
- Only alert if new comments exist. Silent if no changes.
