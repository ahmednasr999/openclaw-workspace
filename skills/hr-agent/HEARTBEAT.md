# HEARTBEAT.md — HR Agent

# Check this file on every session start AND every heartbeat poll.

## Priority 1 — Interview Invites (Check FIRST)

Check for interview invites in email (himalaya or pam-telegram.py output):
- Grep email history for: "interview", "invite", "schedule", "meet the team"
- If found → **IMMEDIATELY** alert CEO + start prep workflow (instructions/interviews.md)
- Do NOT proceed to other checks until this is cleared

## Priority 2 — SUBMIT Queue Review

```sql
SELECT COUNT(*) FROM jobs WHERE verdict = 'SUBMIT' AND status = 'discovered'
```

If count > 0:
1. Read `instructions/submit-review.md`
2. Pull all SUBMIT jobs
3. Run quality checks (duplicate, expired, tier match, geo fit)
4. Curate top 3-5 → post shortlist to topic 9
5. Loop in CEO

**Ahmed never sees raw SUBMIT dumps. HR curates first.**

## Priority 3 — Follow-Up Deadlines

```sql
SELECT * FROM jobs WHERE status = 'applied'
AND julianday('now') - julianday(applied_date) > 14
```

If stale apps found:
- Draft follow-up emails (read instructions/outreach.md + instructions/voice.md)
- Post drafts to topic 9 for Ahmed's approval
- Flag any >30 days for closure

## Priority 4 — Recruiter Responses

Check for recruiter messages (email scan):
- Positive response → alert CEO immediately
- Negative/rejection → update ontology, log, inform Ahmed

## Passive Monitoring (Handled by CTO Infrastructure)

These run automatically — HR doesn't manage them:
- jobs-review.py — scores and ranks jobs, flags SUBMIT (cron: 2/6/10/14 UTC)
- notion-pipeline-sync.py — syncs pipeline to Notion every 2 hours
- autoresearch-job-review.py — job research digest (Sunday 2 AM Cairo)
- application-lock.py — prevents duplicate applications (integrated in pipeline-sync)
- ontology-pipeline-sync.py — syncs to knowledge graph (daily 4:55 AM Cairo)

## Pipeline Health Targets

| Metric | Target | Alert if breached |
|--------|--------|-------------------|
| SUBMIT queue unreviewed | 0 | > 0 → run submit-review.md |
| Stale apps (>14 days) | 0 | > 0 → draft follow-up |
| Overdue outreach (>7 days no reply to follow-up) | 0 | > 0 → final nudge or close |
| Interview invites | Route in <5 min | Any new → CEO alert IMMEDIATELY |
| Recruiter positive responses | Route same day | Any new → CEO alert |
| Weekly discovery rate | 5+ jobs/week | < 5 → run job search across all platforms |

## Session End Checklist

Before ending any session:
- [ ] SUBMIT queue is 0 (all reviewed and posted/filtered)
- [ ] No stale apps without follow-up drafts
- [ ] No interview invites unprocessed
- [ ] No outreach follow-ups overdue
- [ ] Weekly summary posted (if Sunday)

If items remain → brief note to CEO DM before ending.
