# HEARTBEAT.md — CMO Agent

# Check this file on every session start.

## Startup Health Checklist

Run these on session start:

```
1. Check Notion content calendar — any posts scheduled for today that haven't posted?
2. Check data/linkedin-engagement-pending.json — any pending approvals that need follow-up?
3. tail -20 logs/linkedin-engagement.log — any errors from the engagement agent?
4. Check content calendar for posts marked "Scheduled" that missed their date
```

## Passive Monitoring (Built-In Cron)

These run automatically and don't need heartbeat attention:
- linkedin-autoresearch.py — 1 AM Sunday, discovers post opportunities
- comment-radar-agent.py — runs with engagement agent, drafts comments
- linkedin-engagement-agent.py — 7 AM and 9 AM Sun-Thu, sends approval queue
- linkedin-auto-poster.py — 9:30 AM daily, posts approved content
- rss-to-content-calendar.py — 6:30 AM Sunday, fills content calendar
- content-factory-health-monitor.py — 7 AM Sun-Thu

## Alert Thresholds (When to Escalate)

Escalate to CEO immediately if:
- LinkedIn posting fails 2 days in a row (Composio issue — escalate to CTO too)
- Approval queue has > 10 pending items (too many drafts backed up)
- Any of the next 7 calendar days lacks one scheduled post
- Any post gets significant negative engagement (flag for CEO review)
- Engagement agent fails 2+ days (search/rate-limit issue)

## Content Calendar Health

Minimum viable calendar:
- 7 calendar days of content ahead (not including today)
- Exactly 1 scheduled post per calendar day
- At least 2 posts per week should be original insight (not just reposts)

Alert threshold vs planning target:
- Alert Ahmed immediately when any of the next 7 calendar days lacks a `Scheduled` post or contains a duplicate scheduled row.

If the seven-day daily-cadence threshold is breached → alert Ahmed with a short decision-card, not a paragraph:

```
🚨 Content Gap Alert - [High|Medium]

🎯 Action required
[Specific approve/schedule action and deadline]

📌 Situation
- Window at risk: [dates]
- Scheduled: [count] posts
- Gap days: [dates]

📝 Ready queue
- [date]: [title] ([status])

✅ System checks
- Notion direct access: working
- Publishing watchdog: [clean|issue]
- Pending approvals: [count]
- Engagement-log errors: [none|count]

Bottom line: this is an approval/scheduling gap, not a system failure.
```

Use `/root/.openclaw/workspace-cmo/scripts/format_content_gap_alert.py` with the JSON from `heartbeat_check_current.py` when possible.

## Session End

Before ending a session, check:
- Any posts awaiting approval in the pending queue?
- Any posts scheduled for today that haven't been confirmed?
- Any gap in the content calendar that needs flagging?

If gaps exist → write brief note to CEO DM.
