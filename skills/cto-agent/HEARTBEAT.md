# HEARTBEAT.md — CTO Agent

# Check this file on every session start.

## Startup Health Checklist

Run these on session start (before accepting work):

```
1. curl -s http://localhost:18789/health → should return 200
2. git -C /root/.openclaw/workspace log --oneline -1 → record age as context only; age alone is not a warning
3. ls /root/.openclaw/workspace/logs/cron-dashboard-updater.log → should exist
4. grep -c ERROR /root/.openclaw/workspace/logs/cron-dashboard-updater.log (last 100 lines) → flag if > 3
5. Check critical dirty paths in both repos → warn only with the specific unreviewed paths
```

## Passive Monitoring (Built-In)

These run automatically via cron and don't need heartbeat attention:
- cron-dashboard-updater.py — refreshes Notion health dashboard every 30 min
- daily-backup.sh — disabled per Ahmed; do not treat stale daily-backup status as a blocker while the managed crontab line remains commented out
- github-radar.sh — monitors GitHub activity

## Alert Thresholds (When to Escalate)

Escalate to CEO immediately if:
- Gateway DOWN and restart failed after 2 attempts
- daily-backup.sh is enabled in the managed crontab and has not pushed in 48+ hours
- Any cron log shows the same error 3+ times in a row
- New file in workspace root that is NOT in git (possible secret leak)
- Disk usage on workspace > 90%

Warn, without treating the system as down, when unreviewed changes exist in critical paths:
- Runtime repo: `openclaw.json`, `cron/jobs.json`, active agent system prompts, or active extension sources
- Main workspace: `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `USER.md`, or `config/root-crontab.managed`
- List the paths that need review. Do not warn merely because the latest commit is older than 25 hours or because generated logs/data changed.

## Session End

Before ending a session, check:
- Any open issues that need to be handed off to the next CTO session?
- Any pending fixes that need commit + push?
- Any CEO loop-ins that weren't acknowledged?

If open issues remain, write a brief note to `/root/.openclaw/workspace/memory/cto-pending.md`
