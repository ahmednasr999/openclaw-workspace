---
name: content-intelligence
description: "Research trending LinkedIn content in Ahmed's domains (AI, digital transformation, PMO, GCC) to inform next week's posts."
---

# LinkedIn Content Intelligence - Thursday Pre-Build Feed

Research what's working on LinkedIn this week. Provide data-driven content angles.

## Prerequisites
- Web search access (Brave/Tavily)
- Notion Content Calendar DB: `3268d599-a162-814b-8854-c9b8bde62468`
- Ahmed's domains: AI automation, digital transformation, PMO excellence, GCC market

## Steps

### Step 1: Research trending topics
```bash
cd /root/.openclaw/workspace

# Search for trending content in each domain
python3 << 'RESEARCH'
import subprocess, json

domains = [
    "LinkedIn AI automation enterprise trending this week",
    "LinkedIn digital transformation healthcare GCC trending",
    "LinkedIn PMO program management leadership trending",
    "LinkedIn Saudi Vision 2030 digital economy trending",
]

for query in domains:
    print(f"\n=== {query[:50]} ===")
    # Use web search - the agent should call web_search tool for each
    print(f"SEARCH: {query}")
RESEARCH
```
For each domain, use web_search tool to find 3-5 trending posts/topics.

### Step 2: Analyze last week's content
```bash
cd /root/.openclaw/workspace
# Check what Ahmed posted recently
python3 << 'RECENT'
import sys, json, urllib.request, datetime
sys.path.insert(0, "scripts")
from notion_client import NotionClient

nc = NotionClient()
url = f"https://api.notion.com/v1/databases/3268d599-a162-814b-8854-c9b8bde62468/query"
headers = {
    "Authorization": f"Bearer {nc.token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Get recent posts
body = json.dumps({"page_size": 10, "sorts": [{"property": "Date", "direction": "descending"}]}).encode()
req = urllib.request.Request(url, data=body, headers=headers, method="POST")
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    for r in data.get("results", []):
        title = r["properties"].get("Name", {}).get("title", [{}])
        name = title[0].get("plain_text", "?") if title else "?"
        status = r["properties"].get("Status", {}).get("select", {})
        s = status.get("name", "?") if status else "?"
        print(f"  [{s}] {name[:60]}")
except Exception as e:
    print(f"Could not fetch content calendar: {e}")
RECENT
```

### Step 3: Generate content angles
Based on research and recent posts, generate 5-7 angles:
- Each must connect to Ahmed's expertise (AI, PMO, digital transformation, GCC)
- Each must have a specific hook (first line)
- Each must suggest a format (story, listicle, hot take, case study)
- No duplicates from last 2 weeks' posts

### Step 4: Update Content Calendar
For each angle, create entry in Notion Content Calendar with:
- Title (the angle)
- Status: "Ideas"
- Format suggestion
- Research backing (why this will work)

### Step 5: Report
```
Content Intelligence - [DATE]

Research: [X] domains searched, [Y] trending topics found

Top Angles for Next Week:
1. [Topic] - [Format] - Hook: "[first line]"
2. ...

Recent posts: [X] published, [Y] in draft
Calendar updated: [X] new ideas added
```

## Error Handling
- If web search fails: Use knowledge of evergreen topics in Ahmed's domains
- If Notion unreachable: Save angles to `content-intel-backup.md`
- If no trending content found: Focus on evergreen themes

## Quality Gates
- Minimum 5 unique content angles
- Each angle must connect to Ahmed's expertise
- No duplicate topics from last 2 weeks
- Must include at least 1 GCC-specific angle
- Each angle must have a specific hook, not just a topic

## Output Rules
- No em dashes. Hyphens only.
- Angles must be specific ("How UAE hospitals cut wait times 40% with AI triage" = good, "AI is changing healthcare" = bad)
- Include source URLs where possible
