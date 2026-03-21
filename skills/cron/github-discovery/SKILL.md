---
name: github-discovery
description: "GitHub radar: find fastest-growing repos globally, then filter for relevance."
---

# GitHub Discovery Radar v3

## Strategy
Search TRENDING GLOBALLY, then filter for relevance. Not narrow topic searches.

## Run
```bash
python3 scripts/github-discovery.py
```

## What it does
1. Fetches fastest-growing repos (last 7 days, sorted by stars)
2. Fetches today's breakout repos (last 48h)
3. Searches AI/agent/LinkedIn/MCP specific trending
4. Weekly: broader sweep (job search, browser, Notion, PDF tools)
5. Monthly: best-in-class per domain
6. Classifies all repos by relevance domain
7. Outputs: top 10 global + top 10 relevant to us

## Output
- `data/github-discovery.json` — structured data
- Stdout — formatted report for briefing

## Read the output and summarize for Ahmed
1. `cat data/github-discovery.json`
2. Pick top 3-5 most interesting/relevant
3. For each: one line on what it does + why it matters for us
4. Flag anything we should integrate or learn from
