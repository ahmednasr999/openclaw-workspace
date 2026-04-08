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

## Status of Prior Fixes (2026-03-27)

These were identified and fixed before the CTO Agent went live. Confirm they are still healthy:

| Cron | Script | Was Fixed | Current Status |
|------|--------|-----------|----------------|
| daily-backup.sh | `scripts/daily-backup.sh` | ✅ Git pull-before-push strategy added | Verify: `tail -5 /tmp/openclaw-backup.log` |
| run-briefing-pipeline.sh | `scripts/run-briefing-pipeline.sh` | ✅ Timeout increased 900→1200s | Verify: check `--jobs-only` log timestamps |
| linkedin-engagement-agent.py | `scripts/linkedin-engagement-agent.py` | ✅ Exa fallback added (Tavily credits exhausted) | Verify: `tail -5 ~/.openclaw/logs/linkedin-engagement.log` |
| pam-telegram.py | `scripts/pam-telegram.py` | ✅ TypeError fix (interview_invite can be int 0) | Verify: check for TypeError in logs |
| comment-radar-agent.py | `scripts/comment-radar-agent.py` | ✅ Exa fallback added, NoneType fix | Verify: check for AttributeError in logs |

If any of these are failing again, check the Specific Fix Notes below before escalating.

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
- **Timeout:** Increase timeout in the script call (not the cron wrapper)
- **Git push failure:** Use `git pull --no-rebase && git push` strategy (never force push)
- **API rate limit (4xx):** Check credentials, add backoff/retry, check quota
- **Missing file/env:** Verify `.env` loaded, check file paths
- **Network error:** Check if gateway is up, check DNS
- **Notion 401:** Token was auto-revoked if GitHub secret scanning flagged it — new token needed from Ahmed

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
sessions_send agent:main:telegram:direct:866838380 "✅ Fixed <cron-name>: <one-line summary>"
```

---

## Specific Fix Notes (For Recurring Issues)

### daily-backup.sh — Git Push Failure
The fix (git pull --no-rebase before push) is already in the script. If it fails again:
- Check if GitHub secret scanning blocked the push (token in commit)
- Run `secret-scrub.sh` before committing: `bash /root/.openclaw/workspace/scripts/secret-scrub.sh`
- If secret scanning blocks: Ahmed must unblock at `https://github.com/ahmednasr999/openclaw-workspace/security/secret-scanning`

### run-briefing-pipeline.sh — Timeout
Timeout is set to 1200s in the script itself. If it times out again:
- Check which step is slow: `tail -50 /var/log/briefing/cron.log`
- Most likely: jobs-review.py (MiniMax is slow with 300+ jobs in batches)
- Consider: reduce batch size or skip jobs-review in `--jobs-only` mode if already done recently

### linkedin-engagement-agent.py — Search Failure
Tavily is exhausted (HTTP 433 = pay-as-you-go limit exceeded). Exa is the fallback.
- If Exa also fails: check `EXA_API_KEY` in systemd service env
- Ahmed needs to provide Exa key if not present

### Notion API — 401 Unauthorized
Notion tokens get auto-revoked when GitHub secret scanning detects them.
- Ahmed must generate a new token at https://www.notion.so/my-integrations
- Update `~/.openclaw/workspace/config/notion.json`
- Update `/etc/systemd/system/openclaw-gateway.service` env var

---

## Complete Cron Schedule (Live from crontab)

**Run `crontab -l` to confirm — this is the source of truth as of 2026-03-27.**

| Schedule (Cairo) | Script | Purpose | Owner | Log |
|-----------------|--------|---------|-------|-----|
| Hourly | cron-watchdog-v3.sh | Meta-cron that monitors other crons | CTO | watchdog/ |
| Hourly | run-briefing-pipeline.sh --data-only | Briefing data fetch | CEO | briefing/ |
| Hourly | run-briefing-pipeline.sh --jobs-only | Jobs scoring | PMO | briefing/ |
| Hourly | run-briefing-pipeline.sh --all | Full briefing pipeline | CEO | briefing/ |
| Hourly | run-briefing-pipeline.sh --learner | Learner digest | PMO | briefing/ |
| Hourly | cron-dashboard-updater.py | Notion health dashboard | CTO | cron-dashboard-updater.log |
| Every 2h | ontology-notion-sync.py | Ontology ↔ Notion sync | PMO | ontology-sync.log |
| Every 2h | ontology-pipeline-sync.py | Pipeline ↔ Notion sync | PMO | ontology-sync.log |
| 1 AM Sun | linkedin-autoresearch.py | LinkedIn post discovery | CMO | (logs to file) |
| 1 AM Sun-Thu | linkedin-engagement-agent.py | Comment drafts | CMO | linkedin-engagement.log |
| 2 AM Sun | autoresearch-job-review.py | Job research digest | HR | (logs to file) |
| 2:30 AM Daily | x-radar.sh | X/Twitter monitoring | CMO | x-radar.log |
| 2:50 AM Daily | sie-360-checks.py | SIE system checks | PMO | (logs to file) |
| 3 AM Daily | github-radar.sh | GitHub activity monitor | CTO | github-radar.log |
| 3:15 AM Daily | retention-caches.sh | Cache cleanup | CTO | (logs to file) |
| 5 AM Daily | key-health-check.sh | API key validation | CTO | (no log file) |
| 5 AM Sun | retention-backups.sh | Backup rotation | CTO | (logs to file) |
| 6 AM Sun | token-health-check.sh | Token validation | CTO | (no log file) |
| 6:30 AM Sun-Thu | rss-to-content-calendar.py | RSS → content ideas | CMO | rss-to-calendar.log |
| 7 AM Sun-Thu | content-factory-health-monitor.py | Content factory health | CMO | cf-health.log |
| 7 AM Sun-Thu | linkedin-engagement-agent.py | Daily engagement run | CMO | linkedin-engagement.log |
| 8 AM Sun | weekly-agent-review.py | Weekly agent review | CTO | cron-weekly-review.log |
| 8 PM Daily | daily-backup.sh | Git push workspace | CTO | openclaw-backup.log |
| 8:30 PM Daily | retention-backups.sh | Backup rotation | CTO | openclaw-retention-backups.log |
| 9:30 AM Sun-Thu | linkedin-auto-poster.py + cf-weekday-check.sh | Post LinkedIn content | CMO | linkedin-poster.log |

**Note:** 23 total crontab entries. The cron-dashboard-updater.py (hourly) is the primary monitoring tool. For missing log files (key-health-check, token-health-check), add logging before escalating.

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
| Notion token revoked (401 after valid key) | Escalate immediately — new token needed from Ahmed |
| GitHub push blocked by secret scanning | Tell Ahmed to unblock at GitHub secret scanning page |

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

## Health Check SLA

| Metric | Target |
|--------|--------|
| Critical crons success rate | >95% weekly |
| Max failure duration before escalation | 2 hours |
| Dashboard refresh lag | <1 hour |
| Backup recency | <25 hours |
