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
5. Print a summary to stdout (count of results found, top roles). The cron system handles delivery automatically.

## Rules (NON-NEGOTIABLE)
- Do NOT send Telegram messages yourself. Just print the summary. Cron delivery handles it.
- Do NOT try to message any chat directly. If you attempt it, it will fail and mark the run as errored.

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

### Pipeline Auto-Save (NON-NEGOTIABLE)
After saving to `/tmp/google-jobs-YYYY-MM-DD.json`, you MUST also append new jobs to the pipeline:

1. Read `jobs-bank/applied-job-ids.txt` and `jobs-bank/pipeline.md` to identify already-applied companies/roles
2. Filter out duplicates (match by company name + similar title)
3. Filter out UAE-Nationals-only roles
4. Append new jobs to `jobs-bank/pipeline.md` under a `## YYYY-MM-DD - Google Jobs Pre-Fetch` section
5. Include: sequential # (continue from last entry), Company, Role, Location, Status (⭐ New for top picks, New for others, Review for below-level), Source (Google Jobs), Job URL as markdown link
6. Mark top 3 most aligned roles as ⭐ New (prefer: Digital Transformation Director/Officer, AI Strategy, Senior PMO Director, Head of PMO)
7. Save the permanent copy to `jobs-bank/scans/google-jobs-YYYY-MM-DD.json` (not just /tmp/)

This ensures the morning briefing can reference new jobs from the pipeline.

### Scanner Integration
Scanner (`linkedin-gulf-jobs.py`) reads `/tmp/google-jobs-YYYY-MM-DD.json` if it exists and merges results with LinkedIn/Indeed.

## Schedule
5:30 AM Cairo (before 6:00 AM scanner)

## Timeout
10 minutes (each browser task takes ~3 min)
