# Spec: NASR Doctor

## What
A single command (`nasr-doctor`) that checks the health of the entire NASR system and reports status in a clean, actionable format.

## Why
Currently health checks are scattered across cron watchdogs. No unified "is everything working?" command exists. Inspired by ACFS's `acfs doctor`.

## Requirements

### Checks (in order)
1. **OpenClaw Gateway** — running? PID alive? WebSocket responding?
2. **Disk Space** — % used, warn if >80%
3. **Cron Jobs** — list all, last run time, last status (ok/error), next scheduled
4. **API Connections**
   - Firehose API (tap token valid?)
   - Composio LinkedIn (connection active?)
   - Gmail IMAP (can connect?)
5. **Key Scripts** — exist and executable? (firehose-monitor.py, email-agent.py, linkedin-auto-poster.py)
6. **Pipeline Status** — count of New/Applied/Review jobs in pipeline.md
7. **Memory Files** — MEMORY.md, active-tasks.md, today's daily note exist?
8. **Git Status** — clean? uncommitted changes?

### Output Format
```
🩺 NASR Doctor — System Health Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ OpenClaw Gateway    PID 3070576, uptime 4d 12h
✅ Disk Space          59% used (41% free)
⚠️  Cron: email-check  Last run: ERROR (2h ago)
✅ Cron: linkedin-post  Last run: OK (6h ago)
✅ Firehose API        Connected (5 rules)
❌ Gmail IMAP          Connection refused
✅ Pipeline            16 New, 204 Applied
✅ Git                 Clean (last commit 2m ago)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: 6 ✅  1 ⚠️  1 ❌
```

### Non-functional
- Must complete in <10 seconds
- Pure Python, no external dependencies beyond stdlib
- Exit code 0 if all pass, 1 if any warnings, 2 if any errors
- Can be run as `python3 scripts/nasr-doctor.py` or symlinked to `/usr/local/bin/nasr-doctor`
