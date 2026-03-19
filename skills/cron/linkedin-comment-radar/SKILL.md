---
name: linkedin-comment-radar-cron
description: "Find fresh GCC LinkedIn posts worth commenting on, draft comments in Ahmed's voice, save picks for briefing."
---

# LinkedIn Comment Radar (Daily Cron)

## Purpose
Find 5-10 fresh LinkedIn posts from GCC executives worth commenting on. Draft comments. Save results for morning briefing.

## Steps

### Step 1: Search for fresh posts
Use camofox Google search (or web_search if available) with these queries:

```
site:linkedin.com/posts "digital transformation" (UAE OR Saudi OR GCC) -jobs -hiring
site:linkedin.com/posts "program management" OR "PMO" (Dubai OR Riyadh OR Qatar) -hiring
site:linkedin.com/posts "AI" OR "artificial intelligence" (Saudi OR UAE OR MENA) executive -jobs
site:linkedin.com/posts "healthcare technology" OR "healthtech" (GCC OR Middle East) -hiring
site:linkedin.com/posts "leadership" OR "C-suite" (Dubai OR Riyadh OR Jeddah) -jobs
```

Filter results: only linkedin.com/posts URLs, posted within last 48 hours.

### Step 2: Score and rank (PQS 0-100)
For each post, calculate Post Quality Score:
- **Freshness (30 pts)**: Last 24h = 30, last 48h = 15
- **Author signal (25 pts)**: C-suite/VP/Director = 25, Manager/Lead = 15
- **Topic fit (25 pts)**: Digital transformation, PMO, AI, healthcare = 8pts each (max 25)
- **GCC relevance (20 pts)**: Post mentions GCC country = 20

Threshold: PQS >= 40. Select top 10.

### Step 3: Draft comments
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

## Comment Style Guide
- 2-4 lines, direct and practical
- Start with insight ("The governance gap you're describing...")
- Never start with: "Great post!", "Love this!", "So true!", "Couldn't agree more!"
- Include concrete anchor: a framework, metric, or operational detail
- ~40% should end with a genuine question
- Match Ahmed's executive tone (20+ years, PMO, digital transformation)
