# checklist.md — CMO Agent Quality Checklist

Run this checklist weekly (every Friday before batch creation) and on-demand after any major workflow.
Each item is binary: ✅ PASS or ❌ FAIL. No partial credit.

---

## 1. Content Calendar Coverage

**Check:** At least 1 post has Status=`Scheduled` for each of the next 5 business days.

```bash
# Query Notion DB for Scheduled posts in next 5 days
python3 scripts/notion-query.py --db 3268d599-a162-814b-8854-c9b8bde62468 \
  --filter '{"status": "Scheduled", "date_range": "next_5_business_days"}'
```

✅ PASS: 5 posts scheduled across next 5 business days
❌ FAIL: Any gap in business days 1–3 → trigger the decision-card gap alert to CEO immediately; gap only in days 4–5 → log as backlog health warning and add to Friday batch/approval follow-up.

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

Score: X/7
Status: [PASS (7/7) | REVIEW NEEDED (<7/7)]
```

Send summary to CEO via sessions_send if any item is ❌ FAIL.
