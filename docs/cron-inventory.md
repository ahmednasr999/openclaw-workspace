# OpenClaw Cron Inventory

Last managed update: 2026-07-11.

The installed root crontab is mirrored in `config/root-crontab.managed`. Before each managed install, the previous root crontab is backed up in `config/root-crontab.backup-*.bak`.

## Operating Rules

- Long-running OpenClaw jobs use `flock` locks under `/var/lock/openclaw`.
- OpenClaw cron logs should go under `/root/.openclaw/workspace/logs` or the owning workspace log directory, not `/tmp`.
- Temporary campaign jobs need a retirement date or a hard date guard.
- Network-backed dashboard sync must leave a local summary even when Notion is slow or unavailable.

## Managed Jobs

- `daily-backup.sh`: daily 20:00, persistent log `logs/openclaw-backup.log`, locked.
- `archive-daily-notes.sh`: monthly day 1 20:00, persistent log `logs/cron/archive-daily-notes.log`, locked.
- `daily-snapshot.sh`: daily 23:00, persistent log `logs/cron/daily-snapshot.log`, locked.
- `retention-backups.sh`: daily 20:30, persistent log `logs/cron/retention-backups.log`, locked.
- `retention-snapshots.sh`: daily 23:30, persistent log `logs/cron/retention-snapshots.log`, locked.
- `retention-caches.sh`: daily 03:15, persistent log `logs/cron/retention-caches.log`, locked.
- `disk-health-check.sh`: daily 09:00 Cairo/system local time, report-only disk status, locked.
- `direct-cron-runner.py disk-guard`: daily 07:07 Cairo, triggers at 75% root usage, runs maximum safe cleanup automatically, and alerts Ahmed only when triggered or failed. Internally locked.
- `job-radar.sh`: daily 06:00, restored as a wrapper around Job Radar v3, locked.
- `morning-brief.sh`: daily 06:10, staggered after job radar, locked.
- `clear-stale-context-maintenance.py`: every 5 minutes, persistent log, locked.
- `repo-maintainer-watch.py`: every 5 minutes, persistent log `logs/cron/repo-maintainer-watch.log`, locked; detects repo maintenance signals and dispatches at most one bounded CTO worker turn without push/merge/runtime authority.
- `cron-watchdog-v3.sh`: every 2 hours, persistent watchdog log, locked.
- OpenClaw native `session-watchdog`: every 3 hours via CTO, runs `scripts/session-watchdog.sh`, rotates oversized session JSONL logs and writes `reports/agent-lane-stall-latest.md`; prints a summary when CMO/HR stalled or interrupted sessions need attention.
- `sie-360-checks.py`: daily 01:50, persistent log, locked.
- `direct-cron-runner.py session-cleanup`: daily 03:00 Cairo, internally locked.
- `direct-cron-runner.py weekly-self-health`: Sundays 09:00 Cairo, internally locked.
- `backup-restore-smoke-test.sh`: Sundays 10:00 Cairo, verifies latest backup signal and latest snapshot readability, locked.
- `approved-14day-post` and `approved-14day-engagement`: May 15-28, 2026 only; cleanup is scheduled for May 28, 2026 at 12:20 Cairo.
- `cron-dashboard-updater.py`: hourly at minute 7, locked; Notion timeouts are warnings while the local summary remains authoritative.
- `jobzoom_daily_launch.sh`: daily 05:00 Cairo, locked.
- `skill-discovery-pilot`: Sundays 11:15 Cairo, bounded to eight GitHub repositories, writes inert quarantine evidence and a local review report only; no install, execution, promotion, or messaging.

## System Jobs Left As-Is

- `model-guardian.timer`: every six hours near 00:00, 06:00, 12:00, and 18:00 Cairo with up to five minutes randomized delay. This is the sole Model Guardian scheduler; the duplicate root-cron entry was retired on 2026-07-17. Its quota-only probe reads the protected Codex OAuth file and calls the fixed ChatGPT usage endpoint directly, avoiding the heavyweight full-runtime status scan.

- `/etc/crontab` periodic jobs for hourly, daily, weekly, and monthly maintenance.
- `/etc/cron.d/sysstat` activity collection.
- `/etc/cron.d/e2scrub_all` filesystem scrubbing fallback jobs.
- `/etc/cron.d/docker-image-prune` daily image pruning. Current disk pressure justifies keeping the aggressive prune policy for now.

- `0 15 * * *` CMO LinkedIn Comment Radar, via `direct-cron-runner.py linkedin-comment-radar-1500`, writes `logs/cron/linkedin-comment-radar-1500-cron.log`, sends draft pack for approval only.
