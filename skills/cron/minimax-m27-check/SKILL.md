---
name: minimax-m27-check
description: "Check if MiniMax M2.7 is available on the minimax-portal API and notify Ahmed."
---

# MiniMax M2.7 API Availability Check

## Purpose
Check whether MiniMax M2.7 model is now available via the minimax-portal API for production use.

## Steps

### Step 1: Check API availability
Try to use the model via a simple test:
```
session_status with model minimax-portal/MiniMax-M2.7
```
Or check the MiniMax documentation/announcements at https://www.minimax.io

### Step 2: Check web announcements
Search for recent announcements about MiniMax M2.7 API access:
- https://agent.minimax.io
- MiniMax official channels
- AI news sites

### Step 3: Report findings
If **available**:
- Notify Ahmed: "MiniMax M2.7 is now available on minimax-portal. Model ID: `minimax-portal/MiniMax-M2.7`. Ready to upgrade default from M2.5."
- Suggest updating TOOLS.md model table

If **not available**:
- Reschedule this check for 3 days later: `openclaw cron edit minimax-m27-check --at "YYYY-MM-DDT08:00:00Z"`
- Brief message: "M2.7 not yet on portal API. Rescheduled check for [date]."

## Error Handling
- If API check (Step 1) fails: retry once after 30 seconds; if still fails, proceed to web search step
- If web search (Step 2) fails or returns no relevant results: report "unable to verify availability via web search"
- Always reschedule the check regardless of outcome (available or not) — do not let the cron die silently
- If rescheduling command fails: log error and report to Ahmed manually

## Quality Gates
- Must actually verify API availability (not just check a webpage)
- Must reschedule if not available (don't let the check die)

## Manual Run
```bash
cd /root/.openclaw/workspace && openclaw cron run minimax-m27-check
```

## Output Rules
- No em dashes - use hyphens only
- Report must state: available or not available, and next check date
- Include timestamp of check
- If available: include exact model ID string for TOOLS.md update
