---
name: linkedin-comment-radar-cron
description: "Find fresh GCC LinkedIn posts worth commenting on, draft comments in Ahmed's voice, save picks for briefing."
---

# LinkedIn Comment Radar (Daily Cron)

## Purpose
Find 5-10 fresh LinkedIn posts from GCC executives worth commenting on. Draft comments. Save results for morning briefing.

## Model Strategy
- **Steps 1-2 (search + score):** Run on MiniMax-M2.5 (free)
- **Step 3 (draft comments):** Switch to Sonnet 4.6 for executive voice quality

## Steps

### Step 1: Search for fresh posts
Use EXA_SEARCH (via Composio) with these queries - set `includeDomains: ["linkedin.com/posts"]` and `startPublishedDate` to 2 days ago:

Run 4 parallel EXA_SEARCH calls via COMPOSIO_MULTI_EXECUTE_TOOL:
1. `query: "digital transformation leadership GCC region"`, `includeDomains: ["linkedin.com/posts"]`, `numResults: 8`
2. `query: "PMO program management leadership executive Middle East"`, same domain filter
3. `query: "AI artificial intelligence business strategy executive UAE Saudi"`, same domain filter  
4. `query: "CTO CIO technology leadership Dubai Riyadh executive transformation"`, same domain filter

All with `startPublishedDate` set to 2 days ago, `type: "neural"`.

### Step 2: Score and rank (PQS 0-100)
For each post, calculate Post Quality Score:
- **Freshness (30 pts)**: Last 24h = 30, last 48h = 15
- **Author signal (25 pts)**: C-suite/VP/Director = 25, Manager/Lead = 15
- **Topic fit (25 pts)**: Digital transformation, PMO, AI, healthcare = 8pts each (max 25)
- **GCC relevance (20 pts)**: Post mentions GCC country = 20

Threshold: PQS >= 40. Select top 10.

### Step 2b: Fetch post content
Use EXA_GET_CONTENTS_ACTION with the top 10 post URLs to get actual post text. This is critical for writing informed comments.

### Step 3: Draft comments (SWITCH TO SONNET 4.6) — DO NOT POST. Present to Ahmed for approval.
**Important: Use `session_status` to switch model to `sonnet46` before drafting.**
For each top pick, draft a 2-4 line comment in Ahmed's voice:
- Start with insight, never generic praise
- Include one concrete anchor (governance, cadence, metric, value)
- Add a sharp question ~40% of the time
- No em dashes
- Executive tone

### Step 4: Save results
```python
import json, os
from datetime import datetime, timezone, timedelta

cairo = timezone(timedelta(hours=2))
today = datetime.now(cairo).strftime("%Y-%m-%d")
engagement_dir = "/root/.openclaw/workspace/memory/engagement"
os.makedirs(engagement_dir, exist_ok=True)

results = {
    "date": today,
    "total_found": TOTAL_FOUND,
    "qualified": QUALIFIED_COUNT,
    "top_picks": [
        {
            "url": "https://linkedin.com/posts/...",
            "author": "Name",
            "title": "Post title/snippet",
            "pqs": 75,
            "gcc": True,
            "draft_comment": "Your drafted comment here..."
        }
    ]
}

with open(f"{engagement_dir}/{today}-radar.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Step 5: Report
Send to Content topic (topic 7):
```
📡 LinkedIn Comment Radar - {date}

Found {total} posts, {qualified} qualified (PQS>=40)
Top {len(picks)} comment opportunities:

1. [PQS:{score}] {author} - {title} 🌍GCC
   {url}
   💬 Draft: {comment}

2. ...

Goal: 5 comments today | Streak: {streak} days
```

## Error Handling
- If EXA_SEARCH returns no results: retry with broader query (drop domain filter), report "limited results"
- If model switch to Sonnet fails: draft comments on current model, flag in report
- If save to engagement dir fails: print results to stdout so cron captures them
- If fewer than 3 posts qualify (PQS >= 40): lower threshold to 30 and rerun scoring, note in report

## Comment Style Guide
- 2-4 lines, direct and practical
- Start with insight ("The governance gap you're describing...")
- Never start with: "Great post!", "Love this!", "So true!", "Couldn't agree more!"
- Include concrete anchor: a framework, metric, or operational detail
- ~40% should end with a genuine question
- Match Ahmed's executive tone (20+ years, PMO, digital transformation)

## Quality Gates
- Each post entry has: URL, author, topic, engagement metrics
- Comments drafted in Ahmed's voice (direct, strategic, no corporate speak)
- Top 10 ranked by freshness + engagement score
- Never post comments without Ahmed's explicit approval

## Manual Run
```bash
cd /root/.openclaw/workspace && openclaw cron run linkedin-comment-radar
```

## Output Rules
- No em dashes - use hyphens only
- Report to Content topic (topic 7), not main chat
- Include date, total found, qualified count, and top picks
- Each pick: PQS score, author, snippet, URL, and draft comment
- Keep total report under 3000 chars for Telegram delivery
