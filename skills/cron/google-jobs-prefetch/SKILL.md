---
name: google-jobs-prefetch
description: "Pre-fetch Google Jobs results via Composio Browser Tool for scanner integration."
---

# Google Jobs Pre-fetch

## What This Does
Searches Google Jobs for executive roles matching Ahmed's profile using Composio Browser Tool (cloud browser that bypasses Google bot detection). Saves results to `/tmp/google-jobs-YYYY-MM-DD.json` for the scanner to read.

## Execution

1. Search Google Jobs for 2-3 queries (digital transformation, PMO, healthcare IT)
2. Use `COMPOSIO_SEARCH_TOOLS` → `BROWSER_TOOL_CREATE_TASK` → `BROWSER_TOOL_WATCH_TASK`
3. Parse the output text into structured JSON
4. Save to `/tmp/google-jobs-YYYY-MM-DD.json`
5. Report summary (count of results found, top roles) - delivery handled automatically by the cron system

## Search Queries
- `director digital transformation UAE OR Saudi OR Qatar` (udm=8, gl=ae)
- `PMO head program management UAE OR Saudi OR Qatar OR Bahrain` (udm=8, gl=ae)

## Output Format
```json
[
  {"title": "...", "company": "...", "location": "...", "url": "...", "source": "Google Jobs"}
]
```

## Integration
Scanner (`linkedin-gulf-jobs.py`) reads `/tmp/google-jobs-YYYY-MM-DD.json` if it exists and merges results with LinkedIn/Indeed.

## Schedule
5:30 AM Cairo (before 6:00 AM scanner)

## Timeout
10 minutes (each browser task takes ~3 min)
