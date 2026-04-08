---
name: content-creator-prebuild
description: "Friday pre-build: generate next week's LinkedIn posts with images, hooks, and scheduling plan."
---

# Content Creator - Friday Pre-Build

Generate complete LinkedIn posts for next week. Quality over quantity.

## Prerequisites
- Notion Content Calendar DB: `3268d599-a162-814b-8854-c9b8bde62468`
- LinkedIn Writer skill: `skills/linkedin-writer/SKILL.md`
- Content Intelligence results (from Thursday run)

## Steps

### Step 1: Review available topics
```bash
cd /root/.openclaw/workspace
python3 << 'TOPICS'
import sys, json, urllib.request
sys.path.insert(0, "scripts")
from notion_client import NotionClient

nc = NotionClient()
url = f"https://api.notion.com/v1/databases/3268d599-a162-814b-8854-c9b8bde62468/query"
headers = {"Authorization": f"Bearer {nc.token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}

# Get ideas and outlines
body = json.dumps({
    "filter": {"or": [
        {"property": "Status", "select": {"equals": "Ideas"}},
        {"property": "Status", "select": {"equals": "Outline"}}
    ]},
    "page_size": 20
}).encode()
req = urllib.request.Request(url, data=body, headers=headers, method="POST")
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    for r in data.get("results", []):
        title = r["properties"].get("Name", {}).get("title", [{}])
        name = title[0].get("plain_text", "?") if title else "?"
        status = r["properties"].get("Status", {}).get("select", {}).get("name", "?")
        print(f"  [{status}] {name[:70]}")
    print(f"\nTotal available: {len(data.get('results', []))}")
except Exception as e:
    print(f"Error: {e}")
TOPICS
```

### Step 2: Select 3-5 posts for next week
Pick posts that:
- Mix formats (1 story, 1 insight, 1 practical tip minimum)
- Cover different domains (AI, PMO, GCC, career)
- Don't repeat last week's themes
- Align with job search positioning

### Step 3: Write each post
For each selected post, using Ahmed's voice (reference linkedin-writer skill):
- Hook: First 2 lines that stop the scroll
- Body: Value-driven, experience-based (150-250 words)
- CTA: Question or engagement prompt at the end
- Hashtags: 3-5 relevant, not generic

### Step 4: Schedule in Content Calendar
Update each post in Notion:
- Status: "Draft"
- Scheduled date (Mon-Fri, one per day)
- Full post content in page body

### Step 5: Report
```
Pre-Build Complete - [DATE]

Posts drafted: [X] for [Mon date] to [Fri date]

1. [Mon] "[Hook first line...]" - [format] - [topic]
2. [Tue] "[Hook first line...]" - [format] - [topic]
3. ...

Ready for Ahmed's review in Content Calendar.
```

## Error Handling
- If fewer than 3 topics available: Generate additional angles from Content Intelligence
- If Notion unreachable: Save drafts locally to `content-prebuild-backup.md` (optional, created at runtime)
- If linkedin-writer skill unavailable: Write in professional but human tone

## Quality Gates
- Each post must have hook + body + CTA
- No post over 300 words
- No duplicate themes from last 2 weeks
- All posts must align with executive positioning
- At least 3 posts for the week
- Hooks must be specific, not generic motivational quotes

## Output Rules
- No em dashes. Hyphens only.
- Posts must sound human, not corporate AI
- Each post must have a clear value proposition for the reader
