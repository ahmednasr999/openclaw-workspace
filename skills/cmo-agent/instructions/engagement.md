# engagement.md — LinkedIn Engagement Runbook

## Overview
Daily agent that discovers high-value LinkedIn posts for Ahmed to comment on, scores them, drafts comments in his voice, and routes for CEO approval before posting.

## Key Files
- **Script:** `scripts/comment-radar-agent.py`
- **Pending state:** `data/linkedin-engagement-pending.json`
- **Log:** `logs/linkedin-engagement.log`

---

## Search Configuration

**Tool:** Exa only — Tavily credits are exhausted
**API key:** `EXA_API_KEY` from environment (`.env` or shell)
**DO NOT use Tavily for engagement discovery**

Search targets: fresh GCC posts, sector posts (AI, PMO, Strategy, Leadership, Healthcare, FinTech), C-Suite content, executive conversations

---

## PQS Scoring (Post Query Score, 0–130)

Each discovered post is scored across 5 dimensions:

| Dimension | Max | Description |
|-----------|-----|-------------|
| Career overlap | 30 | Topic matches Ahmed's expertise (AI, PMO, transformation, GCC) |
| Persona match | 25 | Audience matches Ahmed's target network (executives, decision-makers) |
| Comment gap | 25 | Post has <10 comments → opportunity to be among first |
| Brand fit | 25 | Post tone/topic aligns with Ahmed's brand (no trolls, no politics) |
| Freshness | 25 | Posted within last 24h = 25pts, 24–48h = 15pts, >48h = 0pts |

**Minimum threshold to proceed:** PQS ≥ 70
**Top 5 posts per day forwarded for approval**

---

## Comment Cooldown

- **Rule:** Do NOT comment on any person's post within 14 days of last comment
- **Tracking:** Ontology graph — `Person.last_commented` (date field)
- **Check before drafting:** Query ontology for `last_commented` on post author
- **On comment posted:** Update `Person.last_commented` + `Person.last_commented_post` (URL)
- **New persons:** Auto-create `Person` entity in graph when commenting on someone not yet tracked

---

## Workflow (Step by Step)

```
1. DISCOVER
   - Exa search: 30–50 candidate posts
   - Filter: min freshness (last 48h), English/Arabic only, no politics/religion

2. SCORE
   - Apply PQS rubric to each post
   - Filter: PQS ≥ 70
   - Check ontology cooldown: skip if author commented on in last 14 days
   - Select top 5

3. DRAFT
   - Write comment in Ahmed's voice (see voice.md)
   - Comment style: adds insight, agrees with nuance, asks a forward question
   - Max 300 chars — punchy, not sycophantic
   - No generic "Great post!" — every comment must have substance

4. SEND FOR APPROVAL
   - Send to CEO DM (chat: 866838380) via Telegram
   - Format: 5 separate messages, each with:
     - Post title + author + URL
     - PQS score
     - Drafted comment
     - Buttons: [✅ Post It] [✏️ Edit] [❌ Skip]
   - Store pending items in data/linkedin-engagement-pending.json

5. ON APPROVAL (✅ Post It)
   - Post comment on LinkedIn post
   - Like the post
   - Update ontology: Person.last_commented = today, Person.last_commented_post = URL
   - Remove from pending.json

6. ON EDIT (✏️ Edit)
   - CEO sends revised comment text in reply
   - Post revised version
   - Same ontology update

7. ON SKIP (❌ Skip)
   - Remove from pending.json
   - No ontology update (author cooldown not consumed)
```

---

## Cron Schedule

`0 7 * * 0-4` — 9 AM Cairo, Sun–Thu
Runs before working day to give Ahmed comments ready to approve each morning.

---

## Monthly Scorecard

Generate on the 1st of each month and send to CEO DM:

| Metric | Source |
|--------|--------|
| Total comments posted | Ontology graph (Person.last_commented count) |
| Approval rate | approved / (approved + skipped) |
| Estimated reach | Sum of commenter post views (approximated from Exa metadata) |
| New connections triggered | Person entities created this month |
| Follower growth | LinkedIn API (LINKEDIN_GET_MY_INFO — follower delta vs last month) |
| Top performing comment | Highest reply/reaction count (manual or scraped) |

Format: short Telegram message with numbers + trend vs prior month.

---

## Escalation

- If engagement cron fails 2 days in a row → alert CEO DM with error log
- If approval queue has >10 pending items → send reminder to CEO
- If no approvals received in 3 days → send nudge: "3 comments waiting for your approval"
