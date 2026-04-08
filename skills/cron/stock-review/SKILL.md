---
name: stock-review
description: "EGX portfolio quarterly review: check current prices vs baseline, calculate P&L, recommend actions."
---

# Stock Portfolio Review

EGX portfolio quarterly review.

## Prerequisites
- Baseline data (from cron context)
- Web search for current EGX prices

## Steps

### Step 1: Get current prices
```bash
echo "=== PORTFOLIO BASELINE ==="
echo "Checking baseline from cron context..."
# Baseline should be in cron context. If not, use these defaults:
# ELEC: 31,250 units
echo "Fetching current EGX prices via web search..."
```
Use web_search to find current prices for:
- ELEC (El Sewedy Electric)
- SWDY (El Sewedy Electric - verify ticker)
- Any other holdings from baseline

Search: "EGX [ticker] stock price today"

### Step 2: Calculate P&L
For each holding:
- Current price vs baseline price
- Total value change
- Percentage change

### Step 3: Market context
Search for:
- EGX 30 index performance this quarter
- Any news affecting portfolio holdings
- Sector trends (infrastructure, energy)

### Step 4: Recommendations
- Hold/sell/buy more for each position
- Portfolio rebalancing suggestions
- Risk assessment

### Step 5: Report
```
EGX Portfolio Review - [DATE]

Holdings:
  [TICKER]: [units] @ [current] (was [baseline]) = [+/-X%]
  Total value: [amount]
  P&L: [amount] ([percentage])

Market: EGX30 [direction] [%] this quarter

Recommendations:
1. [specific action]
```

## Error Handling
- If price data unavailable: Report "Cannot fetch current prices - check manually"
- If EGX market closed: Use last closing price

## Quality Gates
- Must use actual current prices, not estimates
- P&L calculation must be mathematically correct
- Must include EGX30 context

## Output Rules
- No em dashes. Hyphens only.
- All amounts in EGP
- Prices to 2 decimal places
