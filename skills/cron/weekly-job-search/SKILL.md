---
name: weekly-job-search
description: "Sunday evening pipeline health check: application stats, stage transitions, follow-up reminders, stale rate analysis."
---

# Weekly Job Search Report

Ahmed's Sunday evening pipeline health check.

## Prerequisites
- Notion Job Pipeline DB
- Pipeline data: `coordination/pipeline.json`
- Script: `scripts/notion_sync.py` with `read_pipeline_from_notion()`

## Steps

### Step 1: Pull pipeline data
Read all jobs from Notion pipeline. Calculate:
- Total applications, by stage (Applied/Interview/Offer/Rejected/Stale)
- New applications this week
- Stage transitions this week
- Stale rate (no response after 14+ days)

### Step 2: Follow-up analysis
Identify applications that need follow-up:
- Applied 7+ days ago with no response
- Interview stage with no update in 5+ days
- Companies that viewed profile but no response

### Step 3: Win/loss analysis
- Rejections this week (common reasons if known)
- Positive signals (interviews, callbacks)
- Pipeline velocity (average days per stage)

### Step 4: Recommendations
- Top 3 applications to follow up on
- Roles to stop pursuing (3+ weeks stale)
- New search angles to try

### Step 5: Report
Send comprehensive Telegram report with all sections. Sync to Notion.

## Error Handling
- If pipeline data stale: Use last known data, flag freshness
- If Notion unreachable: Generate from local pipeline.md

## Output Rules
- No em dashes. Hyphens only.
- Real numbers, no estimates. Specific company names.
