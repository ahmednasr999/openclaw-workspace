---
name: job-hunter-review
description: "Weekly Sunday review of job hunting domain: pipeline health, application quality, target company analysis."
---

# Job Hunter - Weekly Domain Review

Sunday pipeline domain review. Deeper than weekly-job-search - focuses on strategy and quality.

## Prerequisites
- Notion Job Pipeline DB: `3268d599-a162-81b4-b768-f162adfa4971`
- Notion Job Dossiers DB: `3268d599-a162-8123-8584-d64a9477f887`
- Master CV data: `memory/master-cv-data.md`

## Steps

### Step 1: Pipeline by company tier
```bash
cd /root/.openclaw/workspace
python3 << 'TIERS'
import sys
sys.path.insert(0, "scripts")
try:
    from notion_sync import read_pipeline_from_notion
    jobs = read_pipeline_from_notion()
except:
    print("Could not read pipeline"); exit(0)

# Categorize
active = [j for j in jobs if j.get("stage") not in ["Rejected", "Closed", "Withdrawn"]]
rejected = [j for j in jobs if j.get("stage") in ["Rejected", "Closed"]]
interviews = [j for j in jobs if "Interview" in j.get("stage", "")]

print(f"Active applications: {len(active)}")
print(f"In interview: {len(interviews)}")
print(f"Rejected/Closed: {len(rejected)}")
print(f"Total pipeline: {len(jobs)}")

# Show active by company
print("\nActive applications:")
for j in sorted(active, key=lambda x: x.get("company", "")):
    print(f"  {j.get('company','?')} - {j.get('role','?')} [{j.get('stage','?')}]")
TIERS
```

### Step 2: Application quality audit
```bash
cd /root/.openclaw/workspace

# Check CVs sent this week
echo "=== CVs in archive ==="
ls -lt archive/cvs/ 2>/dev/null | head -10

# Count tailored CVs
echo "Total tailored CVs: $(ls archive/cvs/ 2>/dev/null | wc -l)"

# Check if any recent CVs match active applications
echo ""
echo "=== Recent CV activity ==="
find archive/cvs -name "*.pdf" -mtime -7 -exec echo "  Last 7d: {}" \; 2>/dev/null
find archive/cvs -name "*.pdf" -mtime -14 -mtime +7 -exec echo "  7-14d: {}" \; 2>/dev/null
```

### Step 3: Target company research
```bash
cd /root/.openclaw/workspace
python3 << 'TARGETS'
import sys
sys.path.insert(0, "scripts")
try:
    from notion_sync import read_pipeline_from_notion
    jobs = read_pipeline_from_notion()
except:
    print("Could not read pipeline"); exit(0)

# Companies with multiple applications
from collections import Counter
companies = Counter(j.get("company", "Unknown") for j in jobs)
multi = [(c, n) for c, n in companies.most_common() if n > 1]
if multi:
    print("Companies with multiple applications:")
    for c, n in multi:
        print(f"  {c}: {n} applications")

# Geographic distribution
locations = Counter(j.get("location", "Unknown") for j in jobs if j.get("location"))
if locations:
    print("\nBy location:")
    for loc, n in locations.most_common(10):
        print(f"  {loc}: {n}")
TARGETS
```

### Step 4: Recommendations
Based on findings, provide:
1. Top 3 actions for next week (specific companies/roles)
2. Roles to stop pursuing (3+ weeks stale, bad fit)
3. New search angles based on pipeline gaps
4. Networking targets (companies where we have no applications but should)

### Step 5: Report
Format:
```
Job Hunter Domain Review - [DATE]

Pipeline Health:
  Active: [X] | Interviews: [X] | Rejected: [X] | Total: [X]

Application Quality:
  CVs tailored this week: [X]
  CVs in archive: [X] total

Geographic Spread: [top 3 locations]
Multi-application companies: [list]

Recommendations:
1. [specific action with company name]
2. [specific action]
3. [specific action]
```

## Error Handling
- If Notion unreachable: Report from local data
- If no recent CVs: Flag as "No applications sent this week - pipeline stalling"
- If pipeline empty: Report "Pipeline needs seeding - run job scanner"

## Quality Gates
- Must list every active application by company name
- Must provide at least 3 specific recommendations
- Must flag if zero applications sent in last 7 days
- Geographic analysis must be included

## Output Rules
- No em dashes. Hyphens only.
- Real company names, never generics
- Specific recommendations, not "apply to more jobs"
