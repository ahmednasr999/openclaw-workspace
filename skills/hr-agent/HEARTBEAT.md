# HEARTBEAT.md — HR Agent

# Check this file on every session start.

## Startup Health Checklist

Run these on session start:

```
1. Check Notion pipeline — any new SUBMIT jobs that need CV building?
2. Check data/nasr-pipeline.db — any applications with stale status (no update > 14 days)?
3. Check for interview invites in email (grep email history for interview-related)
4. Check outreach-queue.json — any pending outreach that's overdue?
```

## Passive Monitoring (Built-In Cron)

These run automatically and don't need heartbeat attention:
- jobs-review.py — scores and ranks jobs, flags SUBMIT
- notion-pipeline-sync.py — syncs pipeline to Notion every 2 hours
- autoresearch-job-review.py — job research digest (Sunday 2 AM)
- application-lock.py — prevents duplicate applications (always running at pipeline-sync)

## Pipeline Health Targets

| Metric | Target | Alert if below |
|--------|--------|----------------|
| SUBMIT queue | < 5 jobs waiting | > 5 waiting → CEO alert |
| Applications in "pending" > 14 days | 0 | > 0 → send follow-up |
| Interview invites | Route immediately | Any new → CEO alert immediately |
| Recruiter reach-outs | Route immediately | Any new → CEO alert immediately |

## Application Follow-Up Rules

If application status is "applied" with no response after 10 business days:
- Check if company is still hiring (quick web search)
- If yes: send follow-up email (draft through CEO)
- If company filled the role: update status to "closed" in pipeline

If application status is "interview" with no update after scheduled interview date:
- Update to "pending_result"
- Follow up with Ahmed (was there an outcome?)

## Alert Thresholds (When to Escalate)

Escalate to CEO immediately if:
- Interview invite received (needs Ahmed's calendar, preparation strategy)
- Recruiter reached out with salary/requirements questions
- Application rejected after interview (flag for CEO review + strategy adjustment)
- Duplicate application was attempted and blocked (informational only)
- Pipeline sync fails 2 days in a row

## Session End

Before ending a session, check:
- Any new SUBMIT jobs that need CV building?
- Any pipeline entries with stale status?
- Any interview prep items pending?
- Any outreach follow-ups overdue?

If items remain → brief note to CEO DM.
