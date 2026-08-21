# checklist.md — CMO Agent Quality Checklist

Run this checklist weekly (every Friday before batch creation) and on-demand after any major workflow.
Each item is binary: ✅ PASS or ❌ FAIL. No partial credit.

---

## 1. Content Calendar Coverage

**Check:** Exactly 7 posts have Status=`Scheduled` across the next 7 calendar days, one on every date.

```bash
# Query Notion DB for Scheduled posts in the next 7 days
python3 scripts/notion-query.py --db 3268d599-a162-814b-8854-c9b8bde62468 \
  --filter '{"status": "Scheduled", "date_range": "next_7_calendar_days"}'
```

✅ PASS: 7 unique scheduled dates across the next 7 calendar days
❌ FAIL: Any missing date or duplicate date → trigger the cadence decision card.

---

## 2. Image Blocks Present

**Check:** The last 3 posts with Status=`Scheduled` each have a valid image block in their Notion page body.

**How to check:**
- Open each Scheduled Notion page
- Verify at least 1 block of type `file` or `image` exists in page body
- Signed S3 URL must be accessible (not expired)

✅ PASS: All 3 have valid image blocks
❌ FAIL: Any missing → generate image via `scripts/image-gen-chain.py` and attach to Notion page

---

## 3. Engagement Activity

**Check:** At least 3 comment approval messages sent to CEO DM (866838380) in the last 7 days.

**How to check:**
- Review `data/linkedin-engagement-pending.json` for posted entries with timestamps
- Count entries where `sent_for_approval_at` is within last 7 days

✅ PASS: 3+ approvals sent in last 7 days
❌ FAIL: <3 → check if engagement cron is running, check `logs/linkedin-engagement.log` for errors

---

## 4. No Stale Scheduled Posts

**Check:** No post has remained in Status=`Scheduled` for more than 48 hours past its Planned Date without being Posted.

**Exception:** Posts explicitly paused by Ahmed/CEO (must have a note in Notion `Notes` property)

```bash
# Find overdue scheduled posts
python3 scripts/notion-query.py --db 3268d599-a162-814b-8854-c9b8bde62468 \
  --filter '{"status": "Scheduled", "planned_date_before": "48h_ago"}'
```

✅ PASS: No stale posts (or all stale posts have explicit pause notes)
❌ FAIL: Any unexplained stale post → investigate cron failure, reschedule, alert CEO

---

## 5. Brand Voice Compliance

**Check:** Last 5 posted LinkedIn posts pass the brand voice test.

**Voice test (all 3 must be true):**
- [ ] No motivational quotes or platitudes ("Success is a journey..." → ❌)
- [ ] No generic advice that could apply to anyone ("Leaders must listen..." → ❌)
- [ ] Post contains a specific insight, data point, or personal angle from Ahmed's actual experience

**How to check:** Pull last 5 posts from Notion (Status=Posted), apply voice test manually or via AI review.

✅ PASS: All 5 pass the voice test
❌ FAIL: Any post fails → flag to CEO, add example to voice.md bad-examples section

---

## 6. Post URL Field Completeness

**Check:** Every post with Status=`Posted` has a non-empty `Post URL` field in Notion.

```bash
# Find Posted posts missing URL
python3 scripts/notion-query.py --db 3268d599-a162-814b-8854-c9b8bde62468 \
  --filter '{"status": "Posted", "post_url_empty": true}'
```

✅ PASS: All Posted entries have Post URL
❌ FAIL: Any missing → manually retrieve URL from LinkedIn and update Notion

---

## 7. Monthly Scorecard Delivered

**Check:** A monthly scorecard was generated and sent to CEO in the current or previous calendar month.

**Metrics to include:**
- Total posts published
- Engagement comments sent + approval rate
- Estimated reach
- New ontology Person entities (new connections)
- Follower growth delta
- Top performing topic
- Recommendation for next month

✅ PASS: Scorecard exists in `memory/` or was sent via sessions_send this month
❌ FAIL: Missing → generate and deliver immediately

---

## 8. Funnel Role Coverage

**Check:** Every post in the current posting week has a `Funnel Role`, and the approved or published mix matches the active cadence.

✅ PASS: Seven-post daily cadence = 2 Reach, 3 Authority, 2 Conversion
❌ FAIL: Any unclassified post or imbalanced mix → correct the planning slate before approval; do not add extra posts merely to repair the ratio

---

## Checklist Summary Template

```
CMO Quality Check — [YYYY-MM-DD]

1. Calendar coverage (5 days)     ✅/❌
2. Image blocks (last 3 posts)    ✅/❌
3. Engagement activity (3/week)   ✅/❌
4. No stale scheduled posts       ✅/❌
5. Brand voice compliance         ✅/❌
6. Post URL completeness          ✅/❌
7. Monthly scorecard delivered    ✅/❌
8. Funnel role coverage           ✅/❌

Score: X/8
Status: [PASS (8/8) | REVIEW NEEDED (<8/8)]
```

Send summary to CEO via sessions_send if any item is ❌ FAIL.
