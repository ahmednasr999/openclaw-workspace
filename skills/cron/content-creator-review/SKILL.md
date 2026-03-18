---
name: content-creator-review
description: "Weekly domain review of LinkedIn content performance, strategy alignment, and pipeline health."
---

# Content Creator - Weekly Domain Review

Friday review of Ahmed's LinkedIn content. Assess performance with real data.

## Prerequisites
- Notion Content Calendar DB: `3268d599-a162-814b-8854-c9b8bde62468`
- Notion LinkedIn Analytics DB: `3268d599-a162-811a-b028-e06c181bfd85`

## Steps

### Step 1: Pull this week's content data
```bash
cd /root/.openclaw/workspace
python3 << 'CONTENT'
import sys, json, urllib.request
sys.path.insert(0, "scripts")
from notion_client import NotionClient

nc = NotionClient()

# Query Content Calendar for recent posts
url = f"https://api.notion.com/v1/databases/3268d599-a162-814b-8854-c9b8bde62468/query"
headers = {"Authorization": f"Bearer {nc.token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
body = json.dumps({"page_size": 20, "sorts": [{"property": "Date", "direction": "descending"}]}).encode()
req = urllib.request.Request(url, data=body, headers=headers, method="POST")

try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    results = data.get("results", [])
    
    published = [r for r in results if r["properties"].get("Status", {}).get("select", {}).get("name") == "Published"]
    draft = [r for r in results if r["properties"].get("Status", {}).get("select", {}).get("name") == "Draft"]
    ideas = [r for r in results if r["properties"].get("Status", {}).get("select", {}).get("name") == "Ideas"]
    
    print(f"Published: {len(published)}")
    print(f"Draft: {len(draft)}")
    print(f"Ideas: {len(ideas)}")
    print(f"Total in calendar: {len(results)}")
    
    print("\nRecent published:")
    for r in published[:5]:
        title = r["properties"].get("Name", {}).get("title", [{}])
        name = title[0].get("plain_text", "?") if title else "?"
        print(f"  - {name[:70]}")
except Exception as e:
    print(f"Error: {e}")
CONTENT
```

### Step 2: Identify patterns
Based on content data:
- Which topics got the most engagement?
- Which formats worked best (story, listicle, insight)?
- Best posting times?
- What's Ahmed's current posting cadence?

### Step 3: Strategy alignment check
- Are posts supporting the job search narrative?
- Is the AI/PMO/transformation positioning consistent?
- Any missed opportunities this week?
- Does content align with target company interests?

### Step 4: Generate recommendations
Provide exactly:
- Top 3 things to keep doing (with evidence)
- Top 3 things to change (with reasoning)
- 1 experiment to try next week

### Step 5: Report
```
Content Review - [DATE]

Posts: [X] published this week, [Y] in draft, [Z] ideas queued

Performance:
- Best: "[title]" - [why it worked]
- Weakest: "[title]" - [why it underperformed]

Keep Doing:
1. [specific + evidence]
2. [specific + evidence]
3. [specific + evidence]

Change:
1. [specific + reasoning]
2. [specific + reasoning]
3. [specific + reasoning]

Experiment: [specific suggestion for next week]
```

## Error Handling
- If no posts this week: Review last 2 weeks, flag content gap as HIGH priority
- If analytics unavailable: Use qualitative assessment from content calendar
- If Notion unreachable: Report "Cannot access content data"

## Quality Gates
- Must reference specific post titles, not generic summaries
- Must provide 3+3+1 recommendations (keep/change/experiment)
- Must flag if posting cadence dropped below 3/week
- Must check alignment with job search strategy

## Output Rules
- No em dashes. Hyphens only.
- Specific numbers, not "good engagement"
- Reference actual post titles in recommendations
