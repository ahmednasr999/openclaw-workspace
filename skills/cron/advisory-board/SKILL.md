---
name: advisory-board
description: "Weekly strategic advisory report: market positioning, competitive analysis, and career strategy recommendations."
---

# Advisory Board Weekly Strategy Report

High-level strategic analysis and career recommendations.

## Prerequisites
- Script: `advisory-board/phase3_engine.py`
- Pipeline and market data

## Steps

### Step 1: Run advisory engine
```bash
cd /root/.openclaw/workspace && python3 advisory-board/phase3_engine.py --mode weekly
```

### Step 2: Read and analyze output
Parse the generated report for key insights.

### Step 3: Synthesize recommendations
- Market positioning update
- Competitive landscape changes
- Strategic pivots to consider
- Networking priorities for next week

### Step 4: Deliver
Send summary to Telegram. Full report to Notion.

## Error Handling
- If engine script fails: Generate manual analysis from available data
- If data insufficient: Flag gaps and provide partial report

## Output Rules
- No em dashes. Hyphens only.
- Executive tone. Strategic, not tactical.
