---
name: morning-briefing
description: "Generate Ahmed's daily morning briefing with job search pipeline, LinkedIn metrics, calendar, email intelligence, scanner trends, and active tasks."
---

# Morning Briefing - Jobs + LinkedIn + Calendar

Ahmed's daily command center summary delivered via Telegram (compact) and Notion (full detail). Must be readable in ~3 minutes.

## Prerequisites
- Scripts: `scripts/morning-briefing-orchestrator.py` must exist
- Notion: All databases accessible (daily_briefings, job_pipeline, active_tasks)
- Himalaya: Gmail connected via IMAP for email summary
- Timezone: Africa/Cairo (all times in Cairo)

## Steps

### Step 1: Run the orchestrator
```bash
cd /root/.openclaw/workspace && python3 scripts/morning-briefing-orchestrator.py
```
This script handles ALL data gathering: pipeline stats, scanner trends, Notion sync, task sync, cron health.

### Step 2: Gather supplementary data
- Check email via himalaya: `himalaya envelope list --account ahmed --folder INBOX --page-size 20`
- Count unread job-related emails (recruiter responses, interview invites)
- Check if any emails have "Action Required" in Email Intelligence DB

### Step 3: Format the Telegram briefing
Use this EXACT format (no deviations):

```
☀️ Morning Brief — [Day, Month DD]

📊 Pipeline: [X] total | [Y] active | [Z] new today
[Top 3 active applications with company + stage]

🔍 Scanner: [X] new jobs found | Trend: [📈/➡️/📉]
[Top 3 matches if any]

📧 Email: [X] unread | [Y] action needed
[Any urgent items]

📅 Calendar: [meetings today or "Clear schedule"]

✅ Tasks: [X] overdue | [Y] due today | [Z] completed yesterday

🤖 System: All [X] crons healthy | [errors if any]
```

### Step 4: Validate before sending
Quality gates (ALL must pass):
- [ ] Pipeline section has real numbers (not zeros unless truly zero)
- [ ] Scanner trend shows direction
- [ ] Email count is current (not stale)
- [ ] No placeholder text like "[X]" remaining
- [ ] Total length under 1500 chars for Telegram readability
- [ ] No em dashes (use hyphens)

### Step 5: Deliver
1. Send compact version to Telegram (chat 866838380)
2. Sync full version to Notion Daily Briefings DB
3. Include any Notion stage changes detected by two-way sync

### Step 7: Update Dashboard Stale Alerts
```bash
cd /root/.openclaw/workspace
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from notion_sync import compute_stale_alerts, update_stale_alerts
alerts = compute_stale_alerts()
update_stale_alerts(alerts)
print(f'Stale alerts: {len(alerts)} items')
"
```

## Error Handling
- If orchestrator script fails: Run steps manually, report which step failed
- If scanner data is stale (>24h): Show "Scanner: last run [time] — data may be stale"
- If Gmail IMAP fails: Show "Email: connection error — check himalaya config"
- If Notion is unreachable: Send Telegram-only briefing, note "Notion sync skipped"
- If calendar auth expired: Show "Calendar: auth expired — re-auth needed"

## Output Rules
- Never use em dashes (—). Use hyphens (-) or commas instead.
- Numbers must be real data, never estimates
- If a section has no data, say "None" not "N/A"
- Tone: direct, executive, no fluff
