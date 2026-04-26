---
name: sie-weekly-report
description: "Weekly SIE summary: aggregate daily findings, track improvement trends, identify recurring issues."
---

# SIE Weekly Report

Aggregate the week's SIE 360 daily snapshots into a trend report.

## Steps

### Step 1: Get this week's SIE snapshots
Use git history for `data/sie-360.json`. The daily deterministic check overwrites that file each day, and the daily data commit preserves the history.

```bash
cd /root/.openclaw/workspace
python3 << 'WEEKLY'
import json
import subprocess
from collections import Counter
from datetime import datetime

log = subprocess.run(
    ["git", "log", "--since=8.days", "--format=%H", "--", "data/sie-360.json"],
    capture_output=True, text=True, check=True
)
commits = [c for c in log.stdout.splitlines() if c.strip()][:7]
if not commits:
    print("SIE snapshots this week: 0")
    raise SystemExit(0)

snapshots = []
for sha in commits:
    blob = subprocess.run(
        ["git", "show", f"{sha}:data/sie-360.json"],
        capture_output=True, text=True, check=True
    ).stdout
    data = json.loads(blob)
    snapshots.append(data)

snapshots.sort(key=lambda d: d.get("generated", ""))
print(f"SIE snapshots this week: {len(snapshots)}")
for s in snapshots:
    gen = s.get("generated", "?")
    score = s.get("health_score", "?")
    summary = s.get("summary", {})
    print(f"  {gen} | score={score} | ok={summary.get('ok','?')} warn={summary.get('warn','?')} alert={summary.get('alert','?')}")
WEEKLY
```

### Step 2: Trend analysis
From the daily snapshots:
- Health score trend (improving/declining/stable)
- Recurring issues (same issue appearing 3+ days)
- Areas that improved
- New issues that appeared

Use only evidence visible across the retrieved daily `data/sie-360.json` snapshots. Do not invent missing days.

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
- If no snapshots this week: Report "No SIE snapshots found in git history - check daily data commits"
- If git history lookup fails but `data/sie-360.json` exists: report that only the latest snapshot is available and trends are limited
- If snapshot parsing fails: report partial data and say which snapshot failed

## Quality Gates
- Must include at least 5 daily snapshots for meaningful trends
- Must identify recurring issues from repeated findings, not just list one day's output
- Health score trend must be calculated from snapshot data, not guessed

## Output Rules
- No em dashes. Hyphens only.
- Trends from actual data, not vibes
