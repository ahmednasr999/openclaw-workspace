# Cron Health Monitoring Runbook

## Overview
The CTO Agent is responsible for monitoring all scheduled cron jobs, diagnosing failures, and escalating to the CEO when human decisions are needed.

---

## Dashboard

- **Notion DB ID:** `3268d599-a162-8188-b531-e25071653203`
- **Dashboard script:** `/root/.openclaw/workspace/scripts/cron-dashboard-updater.py`

### Check dashboard status
```bash
python3 /root/.openclaw/workspace/scripts/cron-dashboard-updater.py --dry-run
```

### Update dashboard live
```bash
python3 /root/.openclaw/workspace/scripts/cron-dashboard-updater.py
```

---

## Known Failing Crons (as of 2026-03-27)

| Cron | Script | Failure Mode | Priority |
|------|--------|-------------|---------|
| daily-backup.sh | `scripts/daily-backup.sh` | Git race condition (concurrent push) | HIGH |
| run-briefing-pipeline.sh | `scripts/run-briefing-pipeline.sh` | Timeout (>5 min) | HIGH |
| linkedin-engagement-agent.py | `scripts/linkedin-engagement-agent.py` | Tavily HTTP 433 (rate limit / auth) | MEDIUM |
| *(check dashboard for full list)* | — | — | — |

**Total failing as of 2026-03-27:** 7 crons. Pull current state from Notion dashboard before actioning.

---

## Standard Fix Workflow

### Step 1: Identify failure
```bash
# Check cron logs
tail -100 /root/.openclaw/workspace/logs/<script-name>.log

# Check system cron log
grep CRON /var/log/syslog | tail -50

# Run dry-run check
python3 /root/.openclaw/workspace/scripts/cron-dashboard-updater.py --dry-run
```

### Step 2: Diagnose root cause
Common patterns:
- **Timeout:** Increase timeout or split job into smaller steps
- **Git race:** Add file lock (`flock`) around git operations
- **API rate limit (4xx):** Check credentials, add backoff/retry, check quota
- **Missing file/env:** Verify `.env` loaded, check file paths
- **Network error:** Check if gateway is up, check DNS

### Step 3: Fix
```bash
# Edit the failing script
nano /root/.openclaw/workspace/scripts/<script-name>

# Test manually before committing
python3 /root/.openclaw/workspace/scripts/<script-name> --dry-run
```

### Step 4: Commit and push
```bash
cd /root/.openclaw/workspace
git add scripts/<script-name>
git commit -m "fix(cron): fix <issue> in <script-name>"
git push origin main
```

### Step 5: Notify CEO
After fixing, send a brief update via `sessions_send`:
```
sessions_send agent:main:telegram:direct:866838380 "✅ Fixed <cron-name>: <one-line summary of what broke and fix>"
```

---

## Specific Fix Notes

### daily-backup.sh — Git Race Condition
**Root cause:** Two processes trying to push simultaneously.
**Fix:** Wrap git push in `flock`:
```bash
flock -n /tmp/git-backup.lock git push origin main || echo "Lock held, skipping"
```

### run-briefing-pipeline.sh — Timeout
**Root cause:** Some step (Notion fetch, LLM call) takes >5 min.
**Fix options:**
1. Increase cron timeout wrapper
2. Add `timeout 300 <command>` around slow step
3. Split into two sequential cron jobs

### linkedin-engagement-agent.py — Tavily 433
**Root cause:** Tavily rate limit or authentication rejection.
**Fix:**
1. Check `TAVILY_API_KEY` in `~/.env`
2. Add exponential backoff retry (3 attempts, 2s/4s/8s)
3. If key expired, rotate at https://app.tavily.com

---

## Escalation Rules

Escalate to CEO (`agent:main:telegram:direct:866838380`) via `sessions_send` when:

| Condition | Action |
|-----------|--------|
| Config change needed (new API key, cron schedule) | Escalate — cannot self-modify |
| Same cron fails for >2 hours despite fix attempts | Escalate with logs |
| Any data loss risk (backup not pushed, DB write failed) | Escalate immediately |
| All critical crons down simultaneously | Escalate immediately |
| Failure cause unknown after 30 min investigation | Escalate with findings |

### Escalation message template
```
🚨 CTO Escalation: <cron-name> failing

Root cause: <what you found>
Attempted fixes: <what you tried>
Risk: <data loss / service degradation / none>
Decision needed: <what Ahmed needs to decide>
Logs: <paste last 20 lines>
```

---

## Cron Schedule Reference

| Cron | Schedule | Purpose |
|------|----------|---------|
| daily-backup.sh | Daily 2 AM Cairo | Git push workspace to GitHub |
| run-briefing-pipeline.sh | Daily 7 AM Cairo | Morning briefing for Ahmed |
| linkedin-engagement-agent.py | 9 AM Cairo Sun-Thu | LinkedIn comment drafts |
| linkedin-auto-poster.py | 9:30 AM Cairo Sun-Thu | Post scheduled LinkedIn content |
| cron-dashboard-updater.py | Every 30 min | Refresh Notion cron dashboard |

*(Check actual crontab for live schedule: `crontab -l`)*

---

## Health Check SLA

| Metric | Target |
|--------|--------|
| Critical crons success rate | >95% weekly |
| Max failure duration before escalation | 2 hours |
| Dashboard refresh lag | <1 hour |
| Backup recency | <25 hours |
