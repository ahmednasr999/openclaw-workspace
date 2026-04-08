---
name: github-discovery
description: "GitHub radar: find fastest-growing repos globally, then filter for relevance."
---

# GitHub Discovery Radar v3

## Strategy
Search TRENDING GLOBALLY, then filter for relevance. Not narrow topic searches.

## Steps

### Step 1: Run Discovery Script
```bash
python3 scripts/github-discovery.py
```

What it does:
1. Fetches fastest-growing repos (last 7 days, sorted by stars)
2. Fetches today's breakout repos (last 48h)
3. Searches AI/agent/LinkedIn/MCP specific trending
4. Weekly: broader sweep (job search, browser, Notion, PDF tools)
5. Monthly: best-in-class per domain
6. Classifies all repos by relevance domain
7. Outputs: top 10 global + top 10 relevant to us

Output:
- `data/github-discovery.json` — structured data
- Stdout — formatted report for briefing

### Step 2: Read and Summarize
1. `cat data/github-discovery.json`
2. Pick top 3-5 most interesting/relevant
3. For each: one line on what it does + why it matters for us
4. Flag anything we should integrate or learn from

## Error Handling
- If script fails: report error, do not retry (GitHub API rate limits)
- If JSON output missing/invalid: report "Discovery data unavailable"
- If no interesting repos found: report "No standout repos this cycle"

## Quality Gates
- Output JSON saved to data/github-discovery.json
- Summary includes top 3-5 repos with relevance explanation
- Each repo entry has: name, stars, description, relevance

### Step 3: Archive Results
Save the final summarized picks (top 3-5 repos) to a dated archive file for trend tracking:
```bash
cp /root/.openclaw/workspace/data/github-discovery.json \
   /root/.openclaw/workspace/data/github-discovery-$(date +%Y-%m-%d).json
echo "Archived: github-discovery-$(date +%Y-%m-%d).json"
```
This allows weekly diffing to track which repos gained traction over time.

## Manual Run
```bash
cd /root/.openclaw/workspace && python3 scripts/github-discovery.py
```

## Output Rules
- No em dashes - use hyphens only
- Include run date and total repos scanned in header
- Each repo entry: name, star count, one-line relevance note
- Keep report under 2000 chars for Telegram delivery
- Flag "INTEGRATE?" for any repo directly useful to current stack
