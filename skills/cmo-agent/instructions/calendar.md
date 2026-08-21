# calendar.md — Content Calendar Management Runbook

## Source of Truth
- **Notion DB:** `3268d599-a162-814b-8854-c9b8bde62468`
- **Status flow:** `Ideas` → `Outline` → `Draft` → `Scheduled` → `Posted`

---

## Weekly Batch (Every Friday)

**Trigger:** Every Friday (automated or on-demand)
**Output:** 7 complete post packages for the first seven uncovered calendar dates after the live scheduled queue, plus 2 reserve ideas

### Process
1. Review last 4 weeks of posted content (avoid topic repetition)
2. Check trending GCC/executive topics via Exa search
3. Generate 7 posts across the active daily cadence:
   - 2× AI/Technology angle
   - 1× PMO/Operational excellence
   - 1× Leadership/Strategy
   - 1× Healthcare transformation
   - 1× FinTech/digital payments
   - 1× Personal insight or current executive signal
4. Read the live scheduled queue, then create 7 Notion pages for the first seven dates that are not already covered:
   - Status: `Draft`
   - Planned Date: one unique date per calendar day, including Friday and Saturday
   - Title: compelling hook (not just topic)
   - Topic tag: one of the 10 canonical topics
5. Prepare the matching inspected visual for each post and send the seven-item batch to Ahmed for approval. Only approved rows move to `Scheduled`.

### Batch Summary Format (to CEO)
```
📅 Daily content batch ready:
[date 1]: [title] — [topic] — [funnel role]
...
[date 7]: [title] — [topic] — [funnel role]
+ 2 reserve ideas: [titles]

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

**Planning target:** Keep exactly one approved `Scheduled` post for each of the next seven calendar days.

**Alert threshold:** Alert Ahmed when any of the next seven calendar days lacks a `Scheduled` post, or when any date has more than one scheduled row.

**Check frequency:** Daily (run by cmo-desk-agent.py at startup and at 8 AM Cairo)

**Alert format (sessions_send + topic 7 message):**
Use a short decision-card that leads with the action, not a paragraph:

```
🚨 Content Gap Alert - [High|Medium]

🎯 Action required
[Specific approve/schedule action and deadline]

📌 Situation
- Window at risk: [dates]
- Scheduled: [count] posts
- Cadence shortfall: [count]

📝 Ready queue
- [date]: [title] ([status])

✅ System checks
- Notion direct access: working
- Publishing watchdog: [clean|issue]
- Pending approvals: [count]
- Engagement-log errors: [none|count]

Bottom line: this is an approval/scheduling gap, not a system failure.
```

When possible, generate the alert with:
`python3 /root/.openclaw/workspace-cmo/scripts/heartbeat_check_current.py | python3 /root/.openclaw/workspace-cmo/scripts/format_content_gap_alert.py`

**Do not auto-schedule** content without CEO approval. Alert only.

---

## Streak Rules (GCC Executive Visibility)

- **Active cadence:** 7 posts per week, one on every calendar day including Friday and Saturday
- **Standard time:** 9:30 AM Cairo. If Ahmed starts or restores cadence after that day's slot, an already-approved post may publish manually the same day.
- **Never post twice in one day** — spacing matters more than volume

If any day in the next seven-day window lacks a scheduled post:
→ Alert Ahmed with the exact gap and the best approval-ready replacement.

---

## Executive Funnel Balance

Every `Draft`, `Scheduled`, and `Posted` row must have one `Funnel Role`: `Reach`, `Authority`, or `Conversion`.

- Seven-post daily cadence: 2 Reach, 3 Authority, 2 Conversion.
- Conversion means a natural invitation to a qualified GCC executive, recruiter, hiring leader, advisory, partnership, or peer conversation. It never means a hard pitch.

Pillars control what Ahmed is known for. Funnel roles control what each post should accomplish. Do not substitute topic diversity for funnel balance.

---

## Rescheduling Protocol

**Trigger:** Post in `Scheduled` status fails to go out (Composio error, network failure, etc.)

**Steps:**
1. Log failure to `logs/linkedin-auto-poster.log`
2. Keep Notion status as `Scheduled` (do NOT change to Failed or Draft)
3. Update `Planned Date` to the next free calendar day, including Friday or Saturday, without creating a two-post collision.
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
- Funnel mix: Reach/Authority/Conversion counts and unclassified posts
- Role-specific outcomes, with qualified conversations reported separately from impressions
- Ideas in backlog: count
- Recommendation: topics to double down on next month
