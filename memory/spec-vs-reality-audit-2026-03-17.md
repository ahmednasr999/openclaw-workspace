---
description: Full spec-vs-reality audit of all scheduled systems, services, crons, and scripts
type: reference
topics: [system-ops]
updated: 2026-03-17
---

# Spec vs Reality Audit — March 17, 2026

## Summary

| Category | Total | OK | Issues |
|----------|-------|----|--------|
| OpenClaw crons (enabled) | 29 | 25 | 4 |
| OpenClaw crons (disabled) | 20 | - | 5 in error state |
| System crontab scripts | 17 | 15 | 2 |
| Systemd services | 5 | 2 | 3 |
| Delivery configs | 29 | 14 | 15 |
| Spec docs with no backing system | 2 | - | 2 |

---

## 🔴 CRITICAL: Things That Should Work But Don't

### 1. HEARTBEAT.md: Never Wired (FIXED tonight)
- **Spec:** HEARTBEAT.md describes hourly monitoring (10 checks)
- **Reality:** `openclaw.json` has no heartbeat config. No cron existed.
- **Status:** FIXED. Merged into Cron Watchdog (2h). 6/7 checks live.

### 2. calendar-webhook.service: Dead, Missing Script
- **Spec:** systemd service for calendar push notifications
- **Reality:** Script `/root/.openclaw/workspace/calendar-webhook.py` does NOT EXIST. Service crashed 74 times then gave up.
- **Action needed:** Either create the script or remove the service.

### 3. gog-calendar-watch.service: Crash Loop
- **Spec:** Watches Google Calendar for changes
- **Reality:** Exit code 2, in auto-restart loop. Never successfully running.
- **Action needed:** Debug why gog calendar watch serve fails.

### 4. github-webhook.service: Inactive, Never Started
- **Spec:** GitHub webhook receiver
- **Reality:** Inactive (dead). Never configured.
- **Action needed:** Decide if needed, otherwise remove service file.

### 5. quota-monitor.js: Missing File
- **System crontab:** Runs at midnight daily
- **Reality:** `/root/.openclaw/workspace/system-config/quota-monitoring/` directory does NOT EXIST.
- **Action:** Remove from crontab (dead cron running every night, failing silently).

---

## 🟡 WARNING: Delivery Config Issues (15 crons)

### Using 'target' instead of 'to' (will fail delivery):
1. **Memory Index**: `"target": "866838380"` should be `"to": "866838380"`
2. **LinkedIn Engagement Radar**: same issue
3. **linkedin-karpathy-loop**: same issue (this caused the error tonight)

### Missing 'to' field entirely (delivery goes nowhere):
4. Weekly Gateway Health Restart
5. weekly-memory-hygiene
6. claude-offpeak-reminder
7. linkedin-monthly-content-prep
8. Gmail Check 4h (disabled but broken)
9. codex-quota-reset-check (disabled but broken)
10. openclaw-update-check (disabled but broken)
11. Self-Healing Agent (disabled but broken)
12. linkedin-cookies-reminder (disabled but broken)
13. reminder-linkedin-pipeline-wire (disabled but broken)
14. [MERGED] Daily Job Email Summary (disabled)
15. Daily Delta (disabled)

---

## 🟡 WARNING: Duplicate Crons (System + OpenClaw)

### linkedin-gulf-jobs.py: RUNS TWICE
- **System crontab:** `0 6 * * *` runs the Python script directly
- **OpenClaw cron:** "LinkedIn Gulf Jobs Scanner v2.1" at 6 AM also runs it
- **Impact:** Double API calls, double rate limiting risk, duplicate notifications
- **Action:** Remove from system crontab (OpenClaw version is more feature-rich)

### morning-brief.sh vs Morning Briefing
- **System crontab:** `0 6 * * *` runs morning-brief.sh (old bash version, outputs to /tmp)
- **OpenClaw cron:** "Morning Briefing" at 7:30 AM runs orchestrator.py (new version with Google Docs)
- **Impact:** Old version runs silently, wastes CPU, output ignored
- **Action:** Remove from system crontab (superseded by OpenClaw version)

---

## 🟡 WARNING: Orphaned System Crontab Scripts

These 17 scripts run via system crontab, outside OpenClaw's visibility.
The Cron Watchdog cannot detect if they fail.

### High-frequency (potential resource waste):
1. **self-healing-agent.sh** (every 2 min): No log file found at expected path
2. **openclaw-watchdog.sh** (every 3 min): Log file empty/minimal
3. **context-watchdog.sh** (every 5 min): Runs outside workspace

### Daily maintenance (should be working):
4. **daily-backup.sh** (8 PM): Log shows git push failures
5. **daily-snapshot.sh** (11 PM): Working (last run confirmed)
6. **key-health-check.sh** (5 AM): No output/log found
7. **disk-health-check.sh** (9 AM): No log found (duplicates OpenClaw's Infrastructure monitor)
8. **github-radar.sh** (3 AM): Working (output confirmed)
9. **x-radar.sh** (2:30 AM): Working (output confirmed)
10. **retention-caches.sh** (3:15 AM): No verification
11. **retention-backups.sh** (8:30 PM): No verification
12. **retention-snapshots.sh** (11:30 PM): No verification
13. **archive-daily-notes.sh** (8 PM, 1st/month): No verification
14. **token-health-check.sh** (6 AM Sundays): No verification

### Confirmed broken:
15. **linkedin-gulf-jobs.py** (6 AM): DUPLICATE (remove)
16. **morning-brief.sh** (6 AM): SUPERSEDED (remove)
17. **quota-monitor.js** (midnight): MISSING FILE (remove)

---

## 🟡 WARNING: Disabled Crons in Error State

5 disabled crons have error as their last status (were broken before being disabled):
1. Calendar Check (error)
2. openclaw-update-check (error)
3. codex-quota-reset-check (error)
4. linkedin-cookies-reminder (error)
5. Weekly Self-Improvement Review (error)
6. reminder-linkedin-pipeline-wire (error)
7. Gmail Check 4h (error)

These should be either fixed and re-enabled, or deleted entirely.

---

## 🟢 OK: Enabled OpenClaw Crons Working

25 of 29 enabled crons are healthy:
- Cron Watchdog (2h) ✅
- SIE 360 Daily ✅
- LinkedIn Shadowbroker Monitor ✅
- Email Check Morning/Afternoon ✅
- LinkedIn Gulf Jobs Scanner ✅
- Morning Briefing ✅
- LinkedIn Daily Post ✅
- Meeting Prep ✅
- Memory Index ✅
- Weekly Pipeline Archive ✅
- Content Creator Weekly/Friday ✅
- Weekly Gateway Health ✅
- SIE Skill Audit ✅ (idle, never run yet)
- weekly-memory-hygiene ✅
- SIE Weekly Report ✅
- Weekly Job Search Report ✅
- Advisory Board Weekly ✅
- Infrastructure Monitor ✅
- Monthly Maintenance ✅
- Monthly Cache Cleanup ✅ (idle)
- Stock Portfolio Review ✅ (idle)
- codex-removal-reminder ✅ (idle)
- minimax-oauth-renewal ✅ (idle)
- linkedin-monthly-content-prep ✅ (idle)

4 enabled with issues:
- **LinkedIn Engagement Radar**: error (timed out, 3 consecutive)
- **linkedin-karpathy-loop**: error (delivery target issue)
- **claude-offpeak-reminder**: skipped (wrong payload kind)
- Plus: delivery config issues on several OK crons (will bite later)

---

## 🟢 OK: Systemd Services Working

1. **openclaw-gateway.service**: active ✅
2. **gog-gmail-watch.service**: active ✅

---

## STATE.yaml Accuracy Check

STATE.yaml last updated: 2026-02-28 (17 days stale)
- `active_pipeline: 35` — needs verification
- `interviews_pending: 1` (Delphi, Feb 24) — likely stale, interview was 3 weeks ago
- `applications_this_week: 12` — from Feb 28, not current
- `avg_ats_score: 89` — from Feb 28, not current
- **Action:** STATE.yaml should be updated or deprecated. It's misleading.

---

## Recommended Actions (Priority Order)

### Immediate (tonight or tomorrow):
1. Fix delivery configs: change `target` to `to` on 3 crons (Engagement Radar, Karpathy Loop, Memory Index)
2. Remove 3 dead entries from system crontab (quota-monitor.js, duplicate linkedin-gulf-jobs.py, superseded morning-brief.sh)
3. Fix claude-offpeak-reminder payload kind (message -> systemEvent)

### This week:
4. Delete or fix calendar-webhook.service (script missing)
5. Debug gog-calendar-watch crash loop
6. Fix daily-backup.sh git push failure
7. Audit the 3 high-frequency system scripts (self-healing, watchdog, context) for actual value vs resource cost
8. Fix disk-health-check duplicate (remove from crontab, OpenClaw has Infrastructure Monitor)
9. Clean up 7 disabled error-state crons (delete or fix)

### Optional:
10. Decide on github-webhook.service (needed or not?)
11. Update STATE.yaml or deprecate it
12. Add model fallback detection to watchdog (7th check)
