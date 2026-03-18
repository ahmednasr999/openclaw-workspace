---
name: offpeak-reminder
description: "Daily 8PM reminder about Claude API off-peak pricing window."
---

# Claude Off-Peak Reminder

## Steps

### Step 1: Check usage today
```bash
# Check if we used expensive models today
echo "Checking today's usage patterns..."
# The agent should check session_status or recent cron runs for model usage
```

### Step 2: Deliver reminder
If heavy model usage planned, remind:
```
Claude off-peak window: 8 PM - 8 AM Cairo (cheaper rates).
Schedule heavy Opus/Sonnet tasks for this window when possible.
Today's status: [heavy/light usage]
```
If no heavy tasks planned: Skip silently.

## Error Handling
- If usage data unavailable: Send generic reminder

## Quality Gates
- Only alert if there's actionable context (heavy tasks pending)
- Silent if nothing to report

## Output Rules
- No em dashes. Hyphens only.
