# LinkedIn Weekly Review - SKILL.md

## Purpose
Friday draft session: select 5 best posts, score them, send to Ahmed for approval, move approved to "Scheduled" for next week's auto-poster.

## Flow
1. **Friday 4 PM Cairo** (cron: `0 14 * * 5` or Sun-Thu at 16:00 depending on week start)
2. Script scrapes Notion Content Calendar for "Idea" and "Drafted" posts
3. Scores each with existing rubric (10 questions, max 13, min 8)
4. Selects top 5 by score
5. Sends review to Telegram (topic 7) with approval buttons
6. On approval → moves to "Scheduled" with next week's planned dates

## Cron Setup
```json
{
  "name": "linkedin-weekly-review",
  "schedule": {"kind": "cron", "expr": "0 14 * * 5", "tz": "Africa/Cairo"},
  "payload": {"kind": "agentTurn", "message": "Run the LinkedIn weekly review: cd /root/.openclaw/workspace && python3 scripts/linkedin-weekly-review.py. Send results to topic 7."},
  "sessionTarget": "isolated",
  "enabled": true
}
```

## Files
- Script: `scripts/linkedin-weekly-review.py`
- Batch state: `data/linkedin-weekly-batch.json`
- Notion DB: `3268d599-a162-814b-8854-c9b8bde62468`
- Telegram: topic 7 (CMO Desk)

## Approval Flow
1. Review arrives in topic 7 with 5 scored posts
2. Each post: score, pass/fail, hook preview, failed criteria
3. Ahmed replies:
   - "approve 1,2,3,4,5" → batch update Notion to Scheduled
   - "skip 3" → exclude #3, shift #6 up
   - "edit 2: change hook to..." → update content, then schedule
4. Approved posts → Notion Status = "Scheduled", Planned Date = next week Mon-Fri
5. Auto-poster (9:30 AM Sun-Thu) picks up Scheduled posts

## Rules
- NEVER skip the review step — even if scores are perfect
- NEVER auto-schedule without Ahmed's approval
- If fewer than 5 draft-worthy posts found, report "Only X posts ready this week"
- Posts below MIN_SCORE (8/13) are flagged as "Needs polish" — don't auto-reject, flag for Ahmed
