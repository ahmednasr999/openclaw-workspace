# calendar.md — Content Calendar Management Runbook

## Source of Truth
- **Notion DB:** `3268d599-a162-814b-8854-c9b8bde62468`
- **Status flow:** `Ideas` → `Outline` → `Draft` → `Scheduled` → `Posted`

---

## Weekly Batch (Every Friday)

**Trigger:** Every Friday (automated or on-demand)
**Output:** 5 new content ideas for the following week

### Process
1. Review last 4 weeks of posted content (avoid topic repetition)
2. Check trending GCC/executive topics via Exa search
3. Generate 5 ideas across topic spread:
   - 2× AI/Technology angle
   - 1× PMO/Operational excellence
   - 1× Leadership/Strategy
   - 1× Personal insight or industry trend
4. Create 5 Notion pages in DB with:
   - Status: `Ideas`
   - Planned Date: spread Mon–Thu next week (skip Friday)
   - Title: compelling hook (not just topic)
   - Topic tag: one of the 10 canonical topics
5. Send batch summary to CEO via sessions_send + topic 7 Telegram message

### Batch Summary Format (to CEO)
```
📅 Content batch ready for next week:
Mon: [title] — [topic]
Tue: [title] — [topic]
Wed: [title] — [topic]
Thu: [title] — [topic]
+ 1 reserve idea: [title]

Move any from Ideas → Scheduled to approve for auto-posting.
```

---

## Topic → Image Routing

| Topic Category | Image Source Priority |
|---------------|----------------------|
| AI, Digital Transformation, HealthTech, FinTech, Data, Innovation | Gemini Flash → FLUX.1 → SD XL → Stock → PIL |
| PMO, Strategy, Leadership, Business, Healthcare | Stock → Gemini Flash → FLUX.1 → SD XL → PIL |
| Default / Other | Gemini Flash → FLUX.1 → Stock → SD XL → PIL |

Script: `scripts/image-gen-chain.py` handles routing automatically based on `Topic` property.

---

## Gap Detection (Non-Negotiable)

**Rule:** If no post has Status=`Scheduled` for the next 5 calendar days → alert CEO immediately.

**Check frequency:** Daily (run by cmo-desk-agent.py at startup and at 8 AM Cairo)

**Alert format (sessions_send + topic 7 message):**
```
⚠️ Content gap detected: No posts scheduled for the next 5 days.
Last scheduled post: [title] on [date]
Action needed: Move at least 3 posts from Draft/Ideas → Scheduled
```

**Do not auto-schedule** content without CEO approval. Alert only.

---

## Streak Rules (GCC Executive Visibility)

- **Minimum:** 3 posts per week (Sun–Thu)
- **Optimal:** 4–5 posts per week
- **Never post on Friday/Saturday** (low GCC engagement)
- **Best times:** 9:00–10:00 AM or 12:00–1:00 PM Cairo (auto-poster handles timing)
- **Never post twice in one day** — spacing matters more than volume

If streak would break (fewer than 3 posts this week by Wednesday):
→ Alert CEO with specific gap + suggestion from `Ideas` backlog

---

## Rescheduling Protocol

**Trigger:** Post in `Scheduled` status fails to go out (Composio error, network failure, etc.)

**Steps:**
1. Log failure to `logs/linkedin-auto-poster.log`
2. Keep Notion status as `Scheduled` (do NOT change to Failed or Draft)
3. Update `Planned Date` to next business day (Mon–Thu, skip Fri/Sat/Sun)
4. Alert CEO DM (866838380):
   ```
   ⚠️ Post failed: "[title]"
   Error: [brief error message]
   Rescheduled to: [new date]
   ```
5. On next cron run, post will be picked up automatically

**Never silently drop a failed post.** Always reschedule + notify.

---

## Content Lifecycle Governance

| Status | Who Sets It | What It Means |
|--------|------------|---------------|
| Ideas | CMO agent (Friday batch) | Raw idea, no draft yet |
| Outline | CMO agent or Ahmed | Hook + 3 key points drafted |
| Draft | CMO agent | Full post written, not yet approved |
| Scheduled | Ahmed (manual) or CEO approval | Approved, will auto-post on Planned Date |
| Posted | Auto-poster (cron) | Live on LinkedIn, Post URL written |

**Only Ahmed or CEO can move a post to `Scheduled`.** The agent proposes; the human approves.

---

## Monthly Content Review

On the 1st of each month, generate and send to CEO:
- Posts published: count + list
- Top performing topic: by estimated reach/engagement
- Content mix: breakdown by topic category
- Ideas in backlog: count
- Recommendation: topics to double down on next month
