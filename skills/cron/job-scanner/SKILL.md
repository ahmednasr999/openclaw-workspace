---
name: job-scanner
description: "Run LinkedIn Gulf Jobs Scanner to find new executive-level positions in GCC matching Ahmed's profile."
---

# LinkedIn Gulf Jobs Scanner

Automated job discovery scanning LinkedIn for VP/Director/C-suite roles in UAE, KSA, Qatar, and Oman.

## Prerequisites
- Script: `scripts/linkedin-gulf-jobs.py`
- LinkedIn cookies: `~/.openclaw/cookies/linkedin.txt` (must be fresh)
- Notion Scanner History DB: `3268d599-a162-8123-a867-d7231817f03d`
- Notion Job Pipeline DB: `3268d599-a162-81b4-b768-f162adfa4971`

## Steps

### Step 1: Run the scanner
```bash
cd /root/.openclaw/workspace && python3 scripts/linkedin-gulf-jobs.py
```
This script handles: LinkedIn search, filtering, dedup against pipeline, scoring.

### Step 2: Verify output
Check that the scanner produced results:
- Jobs found count (expect 5-30 per run)
- If 0 jobs found, check cookie freshness
- If <10 jobs for 3+ consecutive runs, trigger degradation alert

### Step 3: Sync to Notion
The script calls `sync_scanner_run()` automatically. Verify:
- Scanner History DB has new entry with today's date
- Any high-scoring jobs (80+) added to Job Pipeline

### Step 4: Report results
Output format:
```
🔍 Scanner: [X] jobs found | [Y] new matches | Cookie age: [Z] days
Top matches: [list top 3 by score]
Trend: [📈/➡️/📉] vs 7-day avg
```

## Error Handling
- If LinkedIn returns 429/rate limit: Wait 60s, retry once. If still fails, report and stop.
- If cookie expired (401/403): Alert "LinkedIn cookie expired - needs refresh"
- If script crashes: Check stderr, report error, do not retry
- If 0 results but no error: Report "No matching jobs found (filters may be too strict)"

## Quality Gates
- Scanner must complete within 5 minutes
- Results must include job title, company, location, and link
- Duplicate jobs (already in pipeline) must be filtered out

## Output Rules
- No em dashes. Use hyphens.
- Include trend direction in every report
- Flag cookie age if >5 days
