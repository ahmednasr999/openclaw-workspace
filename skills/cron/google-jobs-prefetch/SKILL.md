---
name: google-jobs-prefetch
description: "Pre-fetch Google Jobs results via Composio Browser Tool for scanner integration."
---

# Google Jobs Pre-fetch

## What This Does
Searches Google Jobs for executive roles matching Ahmed's profile using Composio Browser Tool (cloud browser that bypasses Google bot detection). Saves results to `/tmp/google-jobs-YYYY-MM-DD.json` for the scanner to read.

## Execution

### Step 1: Search Google Jobs
Search Google Jobs for 2-3 queries (digital transformation, PMO, healthcare IT)

### Step 2: Run Browser Tool
Use `COMPOSIO_SEARCH_TOOLS` → `BROWSER_TOOL_CREATE_TASK` → `BROWSER_TOOL_WATCH_TASK`

### Step 3: Parse Output
Parse the output text into structured JSON

### Step 4: Save Results
Save to `/tmp/google-jobs-YYYY-MM-DD.json`

### Step 5: Print Summary
Print a summary to stdout (count of results found, top roles). The cron system handles delivery automatically.

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

### Step 6: Pipeline Auto-Save (NON-NEGOTIABLE)
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
Timeout
10 minutes (each browser task takes ~3 min)

## Error Handling
- If browser task fails: retry once with 30s delay, then report error
- If no results found: save empty array, report "0 jobs found"
- If pipeline append fails: still save to /tmp/ and jobs-bank/scans/, report pipeline error separately
- Never send Telegram messages directly - just print output

## Quality Gates
- JSON saved to both /tmp/ and jobs-bank/scans/
- Each job has: title, company, location, url, source
- Pipeline updated with new non-duplicate jobs
- Top 3 aligned roles marked with star

## Manual Run
```bash
cd /root/.openclaw/workspace && openclaw cron run google-jobs-prefetch
```

## Output Rules
- No em dashes - use hyphens only
- Print summary to stdout only - never send Telegram directly
- Format: "Google Jobs: [N] results saved | Top roles: [role1], [role2]"
- Include date-stamp in output and confirm both /tmp/ and jobs-bank/scans/ paths
