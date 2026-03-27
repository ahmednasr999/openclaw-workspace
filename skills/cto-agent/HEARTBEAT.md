# HEARTBEAT.md — CTO Agent

# Check this file on every session start.

## Startup Health Checklist

Run these on session start (before accepting work):

```
1. curl -s http://localhost:18789/health → should return 200
2. git -C /root/.openclaw/workspace log --oneline -1 → last commit should be < 25h old
3. ls /root/.openclaw/workspace/logs/cron-dashboard-updater.log → should exist
4. grep -c ERROR /root/.openclaw/workspace/logs/cron-dashboard-updater.log (last 100 lines) → flag if > 3
```

## Passive Monitoring (Built-In)

These run automatically via cron and don't need heartbeat attention:
- cron-dashboard-updater.py — refreshes Notion health dashboard every 30 min
- daily-backup.sh — pushes workspace to GitHub daily at 8 PM Cairo
- github-radar.sh — monitors GitHub activity

## Alert Thresholds (When to Escalate)

Escalate to CEO immediately if:
- Gateway DOWN and restart failed after 2 attempts
- daily-backup.sh has not pushed in 48+ hours
- Any cron log shows the same error 3+ times in a row
- New file in workspace root that is NOT in git (possible secret leak)
- Disk usage on workspace > 90%

## Session End

Before ending a session, check:
- Any open issues that need to be handed off to the next CTO session?
- Any pending fixes that need commit + push?
- Any CEO loop-ins that weren't acknowledged?

If open issues remain, write a brief note to `/root/.openclaw/workspace/memory/cto-pending.md`
