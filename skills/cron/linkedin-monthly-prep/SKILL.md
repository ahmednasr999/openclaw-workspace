---
name: linkedin-monthly-prep
description: "Monthly LinkedIn content strategy: themes, calendar, performance review, next month planning."
---

# LinkedIn Monthly Content Prep

Monthly planning for next month's LinkedIn content strategy.

## Prerequisites
- Notion Content Calendar DB: `3268d599-a162-814b-8854-c9b8bde62468`
- Last month's post data

## Steps

### Step 1: Review last month's performance
```bash
cd /root/.openclaw/workspace
python3 << 'REVIEW'
import sys, json, urllib.request, datetime
sys.path.insert(0, "scripts")
from notion_client import NotionClient

nc = NotionClient()
url = f"https://api.notion.com/v1/databases/3268d599-a162-814b-8854-c9b8bde62468/query"
headers = {"Authorization": f"Bearer {nc.token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
body = json.dumps({"page_size": 50, "sorts": [{"property": "Date", "direction": "descending"}]}).encode()
req = urllib.request.Request(url, data=body, headers=headers, method="POST")

try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    results = data.get("results", [])
    
    published = [r for r in results if r["properties"].get("Status", {}).get("select", {}).get("name") == "Published"]
    print(f"Total posts in calendar: {len(results)}")
    print(f"Published: {len(published)}")
    
    # Show recent published
    for r in published[:10]:
        title = r["properties"].get("Name", {}).get("title", [{}])
        name = title[0].get("plain_text", "?") if title else "?"
        print(f"  - {name[:60]}")
except Exception as e:
    print(f"Error: {e}")
REVIEW
```

### Step 2: Set monthly theme
Based on:
- Job search priorities (which roles are targeted?)
- Industry trends from web research
- Seasonal relevance (hiring cycles, conferences)
- GCC market context

### Step 3: Plan weekly themes
Design 4 weekly themes that build on each other.

### Step 4: Generate content calendar
Create 12-16 post slots in Notion Content Calendar:
- 3-4 posts per week
- Mix of formats
- Status: "Ideas"

### Step 5: Report
"Monthly content plan: [X] posts planned across [themes]. First pre-build this Friday."

## Error Handling
- If analytics unavailable: Plan based on qualitative assessment
- If Notion unreachable: Save plan locally

## Quality Gates
- Minimum 12 post slots for the month
- Each week must have a coherent theme
- Mix of at least 3 formats across the month
- At least 25% GCC-focused content

## Output Rules
- No em dashes. Hyphens only.
- Themes must be specific, not vague
- Include rationale for each weekly theme
