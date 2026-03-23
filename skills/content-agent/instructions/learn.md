# LEARN Layer — Performance Learning Loop

Inspired by the Carousel Growth Engine's `learnings.json` pattern. Every post teaches us what works. This layer turns data into next week's advantage.

## Weekly Review (Sunday 8 PM Cairo)

### Step 1: Fetch Performance Data

For each post published this week, collect:
- Reactions (likes, celebrates, etc.)
- Comments (count + quality assessment)
- Reposts/shares
- Impressions (if accessible via API)
- Profile views spike (day-over-day comparison)

Source: Composio LinkedIn tools + manual data if API is limited.

### Step 2: Update Performance Database

File: `references/content-performance.json`

Schema per post:
```json
{
  "date": "2026-03-23",
  "title": "First 5 words of post",
  "post_type": "expertise",
  "pillar": "pmo",
  "hook_style": "bold_claim",
  "hook_text": "Your PMO is measuring the wrong things.",
  "char_count": 987,
  "has_image": true,
  "image_genre": "framework_diagram",
  "reactions": 45,
  "comments": 12,
  "comments_substantive": 8,
  "reposts": 3,
  "engagement_rate": 4.2,
  "experiment_var": "posting_time_12pm",
  "experiment_value": "12:00",
  "repurpose_candidate": false,
  "notes": ""
}
```

### Step 3: Analyze Patterns

Compare this week vs. rolling 4-week average:

**By post type:**
- Which type got highest engagement rate?
- Which type got most substantive comments?
- Which type underperformed?

**By hook style:**
- Curiosity gap vs. bold claim vs. specific story — which wins?
- Track across 20+ posts for statistical significance

**By pillar:**
- Which content pillar resonates most?
- Any pillar consistently underperforming?

**By image genre:**
- Posts with images vs. without — engagement delta?
- Which image genre correlates with highest engagement?

**By timing:**
- 9:30 AM vs. any other tested time
- Day of week patterns (Sun vs. Thu)

### Step 4: Evaluate Experiment

Read `references/experiments.md` for this week's active experiment.

- Did we get enough data? (need 2+ posts per variant for any signal)
- Which variant won?
- Is the signal strong enough to declare a winner?
- If yes: update the relevant instruction file with the winning approach
- If no: extend experiment one more week

### Step 5: Check Content Mix

Read `references/content-mix.md`. Calculate actual ratio over last 4 weeks:

| Type | Target | Actual | Status |
|------|--------|--------|--------|
| Story | 30% | ? | over/under/on-target |
| Expertise | 25% | ? | |
| Opinion | 20% | ? | |
| Data | 15% | ? | |
| BTS | 10% | ? | |

If any type is >10% off target, flag it for next week's batch creation.

### Step 6: Flag Repurposing Candidates

Any post with engagement rate >5% gets flagged:
- Add `"repurpose_candidate": true` to performance JSON
- Suggest specific repurposing format (carousel, article, X thread, infographic)
- Add to next week's creation batch if Ahmed approves

### Step 7: Propose Next Experiment

One variable at a time. Each experiment runs 1-2 weeks.

**Experiment backlog** (prioritized by expected impact):
1. Hook type comparison (curiosity vs. bold vs. story)
2. Posting time (9:30 AM vs. 12:00 PM Cairo)
3. Post length (short <500 vs. medium <1300 vs. long <2000)
4. Image vs. no image
5. Question ending vs. statement ending
6. Hashtag count (3 vs. 5)
7. Pillar rotation speed (weekly vs. daily mix)

### Step 8: Generate Weekly Digest

Send to Ahmed via Telegram:

```
Content Performance — Week of [date]

Top performer: [title] — [X] reactions, [Y] comments, [Z]% engagement
Weakest: [title] — [X] reactions, [Y] comments, [Z]% engagement

This week's experiment: [variable] — [result/ongoing]
Next week's experiment: [proposed variable]

Content mix status: [on-track / Story underweight / etc.]
Repurposing candidates: [list or "none"]

Recommendation: [one specific change for next week]
```

## Rolling Memory

The performance database is cumulative. Never delete old entries. The learning system becomes more valuable over time as patterns emerge across 50, 100, 200+ posts.

After 30 posts: enough data to declare reliable winners for hook type and post type.
After 100 posts: enough data for multi-variable analysis (type + pillar + hook + time).
