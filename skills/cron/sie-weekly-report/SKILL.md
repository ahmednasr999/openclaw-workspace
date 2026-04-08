---
name: sie-weekly-report
description: "Weekly SIE summary: aggregate daily findings, track improvement trends, identify recurring issues."
---

# SIE Weekly Report

Aggregate the week's SIE 360 daily runs into a trend report.

## Steps

### Step 1: Get this week's SIE runs
```bash
openclaw cron runs --id 3c3ba638-8cb3-4a6a-a8f0-2ccd13e3aeed --limit 7 2>&1 | grep -v "^\[plugins\]" > /tmp/sie_weekly_runs.json

python3 << 'WEEKLY'
import json

with open("/tmp/sie_weekly_runs.json") as f:
    text = f.read()

decoder = json.JSONDecoder()
for i, ch in enumerate(text):
    if ch == '{':
        try:
            data, _ = decoder.raw_decode(text[i:])
            break
        except: continue

entries = data.get("entries", [])
print(f"SIE runs this week: {len(entries)}")

for e in entries:
    status = e.get("status", "?")
    duration = e.get("durationMs", 0) // 1000
    summary = e.get("summary", "")[:100]
    print(f"  [{status}] {duration}s - {summary}...")
WEEKLY
```

### Step 2: Trend analysis
From the daily summaries:
- Health score trend (improving/declining/stable)
- Recurring issues (same issue appearing 3+ days)
- Areas that improved
- New issues that appeared

### Step 3: Learnings status
```bash
cd /root/.openclaw/workspace
echo "=== LEARNINGS STATUS ==="
echo "Total: $(grep -c '^## 20' .learnings/LEARNINGS.md)"
echo "Enforced: $(grep -c '### Enforcement' .learnings/LEARNINGS.md)"
```

### Step 4: Report
```
SIE Weekly Summary - [DATE]

Runs: [X] this week
Health trend: [improving/declining/stable] ([lowest] to [highest])

Recurring issues: [list or "none"]
Resolved this week: [list or "none"]
New this week: [list or "none"]

Learnings: [X] total, [Y] enforced ([Z]%)

Recommendations for next week:
1. [specific]
```

## Error Handling
- If no runs this week: Report "No SIE runs - check if cron is enabled"
- If run data parsing fails: Report partial data

## Quality Gates
- Must include at least 5 days of data for meaningful trends
- Must identify recurring issues (not just list daily reports)
- Health score trend must be calculated, not guessed

## Output Rules
- No em dashes. Hyphens only.
- Trends from actual data, not vibes
