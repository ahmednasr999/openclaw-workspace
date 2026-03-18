---
name: monthly-maintenance
description: "Monthly system maintenance: log rotation, dependency updates, config audit, performance review."
---

# Monthly System Maintenance Report

First-of-month system health and maintenance.

## Steps

### Step 1: Log rotation
Check and rotate logs in `/tmp/openclaw/`, clean old log files.

### Step 2: Dependency check
- Node.js version current?
- Python packages up to date?
- OpenClaw version check

### Step 3: Config audit
- Review openclaw.json for stale entries
- Check all API keys/tokens validity
- Verify cron schedules still appropriate

### Step 4: Performance review
- Average response time trends
- Cron success/failure rates this month
- Token usage summary

### Step 5: Disk cleanup
- Remove old temp files
- Archive old logs
- Clean npm/pip caches if needed

### Step 6: Report
Comprehensive monthly health report with recommendations.

## Error Handling
- If cleanup fails: Report which cleanup step failed, continue others

## Output Rules
- No em dashes. Hyphens only.
- Plain text, detailed but organized
