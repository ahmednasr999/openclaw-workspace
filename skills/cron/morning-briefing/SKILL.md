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
Use this EXACT format (no deviations, include ALL sections):

```
☀️ Morning Brief — [Day, Month DD]

📊 PIPELINE: [X] total | [Y] active | [Z] applied this week | [R]% response rate
- [Company - Role - Stage - Next Step]
- [Company - Role - Stage - Next Step]
- (show ALL active interviews)

🔍 SCANNER: [X] new jobs | Trend: [📈up/➡️stable/📉down] | Last: [date]
- [Top 3 job matches if any]

📧 EMAIL INTEL: [X] job-related flagged
- [Sender] - [Subject] - Action: [what to do]

📅 CALENDAR: [meetings or "Clear"]
- [Meeting] - [with who]

📈 DASHBOARD: Health [score] | Stale [X] | KPIs [green/yellow/red]

✅ TASKS: [X] overdue | [Y] due today | [Z] completed

📝 CONTENT CALENDAR: [X] scheduled | [Y] drafted | [Y] posted
- [Any posts needing attention]

🤖 SYSTEM: [X] crons | [errors or "all healthy"]

⚠️ ACTION ITEMS:
1. [Concrete action with owner]
2. [Concrete action]
3. [Concrete action]
```

### Step 4: Validate before sending
Quality gates (ALL must pass):
- [ ] Pipeline section has real numbers (not zeros unless truly zero)
- [ ] Scanner trend shows direction
- [ ] Email count is current (not stale)
- [ ] No placeholder text like "[X]" remaining
- [ ] Total length under 1500 chars for Telegram readability
- [ ] No em dashes (use hyphens)

### Step 5: Sync to Notion (FIRST output step)
Create page in Notion Daily Briefings DB with FULL content (ALL sections):
1. **Pipeline**: All stats + every active interview with company, role, stage, next step
2. **Scanner**: Jobs found, trends, top matches
3. **Email Intel**: Every flagged email with sender, subject, action
4. **Calendar**: Today's meetings
5. **Dashboard**: KPIs, stale alerts
6. **Tasks**: Overdue, due today, completed
7. **Content Calendar**: Scheduled, drafted, posted counts
8. **System**: Cron health, errors
9. **Action Items**: Full list with owners and dates

Use callout blocks with emoji, heading_2 for section headers, bullet lists for items.
Must have 10+ content blocks minimum - no short pages.

### Step 6: Deliver to Telegram
1. Send compact version to Telegram (chat 866838380)
2. Include any Notion stage changes detected by two-way sync

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

### Step 8: LinkedIn engagement
Check for recent LinkedIn post performance or draft engagement comments if content calendar has scheduled posts.

## Execution Order
1. Data gathering (Steps 1-2)
2. Format and validate (Steps 3-4)
3. Notion page creation (Step 5)
4. Telegram delivery (Step 6)
5. Dashboard stale alerts (Step 7)
6. LinkedIn engagement (Step 8)

**ALL steps must complete. Timeout is 600s (10 min). Do not skip any step.**

## Timeout: 600s (10 min)
This cron has a 600s timeout. All 8 steps must complete. No skipping.

## Error Handling
- If orchestrator script fails: Run steps manually, report which step failed
- If scanner data is stale (>24h): Show "Scanner: last run [time] - data may be stale"
- If Gmail IMAP fails: Show "Email: connection error - check himalaya config"
- If Notion is unreachable: Send Telegram-only briefing, note "Notion sync skipped"
- If calendar auth expired: Show "Calendar: auth expired - re-auth needed"
- If SIGTERM received mid-run: Notion page likely not created - SIE will detect and flag

## Output Rules
- Never use em dashes (—). Use hyphens (-) or commas instead.
- Numbers must be real data, never estimates
- If a section has no data, say "None" not "N/A"
- Tone: direct, executive, no fluff
