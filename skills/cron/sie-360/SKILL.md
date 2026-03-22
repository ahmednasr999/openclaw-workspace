---
name: sie-360
description: "SIE 360 daily summary: read pre-computed checks from data/sie-360.json and deliver structured report."
---

# SIE 360 Daily Report

The deterministic checks already ran at 3:50 AM via `scripts/sie-360-checks.py`.
Your job is to read the results, summarize them, and deliver the report.

### Step 1: Read the data
```bash
cat /root/.openclaw/workspace/data/sie-360.json
```

### Step 2: Deliver the report

Format the report exactly as:
```
SIE 360 Daily - [DATE from generated field]
Health Score: [health_score]/100
Checks: [sum of ok+warn+alert] areas | OK: [ok] | WARN: [warn] | ALERT: [alert]

WORKSPACE
- Root files: [workspace.root_files] | Disk: [disk_percent]% ([disk_used]/[disk_total]) | RAM: [ram_used]/[ram_total]
- Sessions: [session_mb]MB
[List large_files if any]

LEARNINGS
- Enforcement: [enforced]/[total] ([pct]%)
[List unenforced_list if any]

INTEGRATIONS
- Gmail: [gmail] | Notion: [notion] ([notion_databases] DBs) | LinkedIn: [linkedin] | Gateway: [gateway]

CRONS
- Total: [total] | Enabled: [enabled] | Disabled: [disabled]
- Skill-first: [skill_first]/[total] ([skill_first_pct]%)
[List raw_prompt_list if any]
[List failing crons if any]

BRIEFING DELIVERY
- Notion page for [today]: [exists -> "EXISTS" or "MISSING - ALERT"]

FINDINGS
[List each finding as: [LEVEL] [category]: [message]]

Auto-Fixed ([count]):
[list auto_fixed items with checkmark emoji]

Needs Attention ([count]):
[list needs_attention items with warning emoji]
```

### Step 3: Update Dashboard KPI (if script exists)
```bash
cd /root/.openclaw/workspace
if [ -f scripts/notion_sync.py ]; then
  python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
with open('data/sie-360.json') as f:
    d = json.load(f)
score = d['health_score']
from notion_sync import update_dashboard_kpi
update_dashboard_kpi(score)
print(f'Dashboard KPI updated: {score}')
"
fi
```

## Output Rules
- No em dashes. Hyphens only.
- Every number comes from sie-360.json - no estimates.
- Gmail App Password = HEALTHY. Do not flag it as an issue.
- NEVER print tokens, passwords, or API keys. Say "configured" or "present".
- NEVER include NO_REPLY in output. Your output IS the report.

## Error Handling
- If `data/sie-360.json` is missing: report "SIE 360 data missing - checks script may not have run (expected at 3:50 AM). Run: python3 scripts/sie-360-checks.py" and stop
- If JSON is malformed or missing required keys: report "SIE 360 data corrupt - [parse error]" and stop; do not attempt to deliver partial report
- If Dashboard KPI update fails (Step 3): log the error but still deliver the report - KPI update is non-blocking
- If Telegram delivery fails: retry once after 10 seconds; if still fails, write report to `/root/.openclaw/workspace/memory/cron-recovery.log`

## Quality Gates
- All report fields sourced from sie-360.json - never estimated or hardcoded
- Health score present and numeric (0-100) before delivery
- ALERT-level findings always listed in Needs Attention section
- Briefing page existence check included (EXISTS or MISSING - ALERT)
- No tokens, passwords, or API keys printed in output
