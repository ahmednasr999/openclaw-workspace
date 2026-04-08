---
name: weekly-job-search
description: "Sunday evening pipeline health check: application stats, stage transitions, follow-up reminders, stale rate analysis."
---

# Weekly Job Search Report

Ahmed's Sunday evening pipeline health check. Run commands, report real data.

## Prerequisites
- Notion Job Pipeline DB: `3268d599-a162-81b4-b768-f162adfa4971`
- Pipeline file: `coordination/pipeline.json` or `jobs-bank/pipeline.md`
- Script: `scripts/notion_sync.py` with `read_pipeline_from_notion()`

## Steps

### Step 1: Pull pipeline data
```bash
cd /root/.openclaw/workspace

# Read from Notion via script
python3 << 'PIPELINE'
import sys
sys.path.insert(0, "scripts")
from notion_sync import read_pipeline_from_notion

jobs = read_pipeline_from_notion()
print(f"Total jobs: {len(jobs)}")

# Count by stage
stages = {}
for j in jobs:
    stage = j.get("stage", "Unknown")
    stages[stage] = stages.get(stage, 0) + 1

for stage, count in sorted(stages.items(), key=lambda x: -x[1]):
    print(f"  {stage}: {count}")
PIPELINE
```
If script fails, fall back to:
```bash
# Fallback: count from pipeline.md
grep -c "^|" jobs-bank/pipeline.md 2>/dev/null || echo "No pipeline.md found"
```

### Step 2: Stale application analysis
```bash
cd /root/.openclaw/workspace
python3 << 'STALE'
import sys, datetime
sys.path.insert(0, "scripts")
try:
    from notion_sync import read_pipeline_from_notion
    jobs = read_pipeline_from_notion()
except:
    print("Could not read pipeline from Notion")
    exit(0)

now = datetime.datetime.now()
stale = []
for j in jobs:
    stage = j.get("stage", "")
    applied_date = j.get("applied_date", "")
    if stage in ["Applied", "Discovered"] and applied_date:
        try:
            d = datetime.datetime.fromisoformat(applied_date.replace("Z",""))
            days = (now - d).days
            if days > 14:
                stale.append({"company": j.get("company","?"), "role": j.get("role","?"), "days": days})
        except:
            pass

print(f"Stale applications (14+ days, no response): {len(stale)}")
for s in sorted(stale, key=lambda x: -x["days"])[:10]:
    print(f"  {s['company']} - {s['role']} ({s['days']}d)")

total = len(jobs)
stale_rate = len(stale) / total * 100 if total else 0
print(f"Stale rate: {stale_rate:.0f}%")
STALE
```

### Step 3: This week's activity
```bash
cd /root/.openclaw/workspace
python3 << 'WEEKLY'
import sys, datetime
sys.path.insert(0, "scripts")
try:
    from notion_sync import read_pipeline_from_notion
    jobs = read_pipeline_from_notion()
except:
    print("Could not read pipeline"); exit(0)

now = datetime.datetime.now()
week_ago = now - datetime.timedelta(days=7)

new_this_week = [j for j in jobs if j.get("created","") > week_ago.isoformat()[:10]]
print(f"New applications this week: {len(new_this_week)}")
for j in new_this_week:
    print(f"  {j.get('company','?')} - {j.get('role','?')}")
WEEKLY
```

### Step 4: Follow-up recommendations
Based on the data from Steps 1-3, recommend:
- Top 3 applications to follow up on (applied 7-14 days ago)
- Applications to close (30+ days stale, no signal)
- New search angles based on pipeline gaps

### Step 5: Report
Format:
```
Weekly Job Search Report - [DATE]

Pipeline: [X] total
  Applied: [n] | Interview: [n] | Offer: [n] | Rejected: [n]

This Week: [X] new applications
Stale Rate: [X]% ([Y] applications, 14+ days no response)

Follow-Up Needed:
1. [Company] - [Role] - [X]d since applied
2. ...

Recommendations:
1. [specific action]
2. [specific action]
```

## Error Handling
- If Notion unreachable: Use local pipeline.md as fallback
- If no pipeline data: Report "No pipeline data available" and skip analysis
- If script import fails: Use web fetch to query Notion API directly

## Quality Gates
- Must report exact job counts by stage
- Must identify stale applications with specific company names
- Must provide at least 3 actionable recommendations
- Stale rate must be calculated from real data

## Output Rules
- No em dashes. Hyphens only.
- Use real company names and roles, never generics
- Every number from actual pipeline data
- Include specific days-since-applied for follow-ups
