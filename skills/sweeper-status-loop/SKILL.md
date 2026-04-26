---
name: sweeper-status-loop
description: Use this whenever the user wants to sweep, triage, clean up, or monitor a backlog of items such as GitHub issues/PRs, JobZoom leads, CMO content queue rows, email action items, OpenClaw health findings, stale tasks, alerts, or review queues. This skill turns recurring review work into a conservative sweeper loop: scan items, write one markdown record per item, maintain a README/STATUS.md dashboard, separate propose from apply, and only auto-act on narrow evidence-backed categories.
---

# Sweeper Status Loop

Use this skill to turn a messy recurring queue into an auditable operating loop.

The core pattern:
1. Scan the source of truth.
2. Write or update one markdown record per item.
3. Maintain a live `README.md` or `STATUS.md` dashboard.
4. Separate **proposed action** from **applied action**.
5. Auto-apply only when the evidence standard is strict and the action is reversible or explicitly allowed.

This is inspired by the ClawSweeper operating pattern, but adapted for Ahmed's workflows: JobZoom, CMO calendar, email triage, OpenClaw health, and internal backlogs.

## When to use

Use this when the work is recurring, queue-based, or easy to lose track of:
- jobs/leads/applications
- content calendar rows
- email action items
- GitHub issues/PRs
- healthcheck findings
- stale docs/tasks
- pending approvals
- watchdog alerts

Do not use it for one-off creative work or simple direct answers.

## Non-negotiable safety stance

- Propose before applying.
- Never delete records as part of sweeping; archive with evidence instead.
- Never send emails, public posts, or external messages without explicit approval.
- Never close/apply ambiguous items automatically.
- Keep enough evidence in each record that a human can audit the decision later.
- If a source system has direct credentials, use direct access rather than creating new OAuth flows.

## Recommended directory structure

Create a local sweeper workspace near the workflow owner:

```text
<workflow>/sweeper/
├── README.md                 # live dashboard
├── items/
│   ├── <item-id>.md           # one regenerated record per source item
├── archive/
│   ├── <item-id>.md           # archived closed/applied records
├── data/
│   ├── latest-scan.json       # optional raw/normalized scan
├── logs/
│   ├── sweeper.log
└── config.json                # optional category/action policy
```

For shared/global prototypes, use:
`/root/.openclaw/workspace/sweepers/<workflow-name>/`

## Record format

Each item record should be regenerated from current evidence.

```markdown
# [Item title]

- Source ID: [id]
- Source URL: [url or n/a]
- Status: proposed_action | keep_open | applied | blocked | needs_human
- Proposed action: [close/archive/apply/keep/review/escalate]
- Confidence: high | medium | low
- Last checked: [ISO timestamp]

## Evidence
- [specific fact]
- [specific fact]

## Reasoning
[short explanation, no hidden chain-of-thought]

## Apply criteria
- [criterion met or not met]

## Next step
[the one next action]
```

## Dashboard format

The README/STATUS dashboard should be useful at a glance.

```markdown
# [Workflow] Sweeper Status

Last updated: [timestamp]
State: scan_only | review_ready | apply_ready | apply_in_progress | blocked

## Decision card
- Items scanned: [n]
- Proposed actions: [n]
- Safe to apply now: [n]
- Needs human review: [n]
- Blockers: [n]

## Recommended next action
[one action]

## Metrics
| Metric | Count |
|---|---:|
| Open/source items | 0 |
| Reviewed items | 0 |
| Proposed apply | 0 |
| Applied this run | 0 |
| Blocked/ambiguous | 0 |

## Recent items
| Item | Outcome | Confidence | Record |
|---|---|---|---|
```

## Close/apply policy

Create explicit categories before acting. Good categories are narrow and evidence-backed.

Examples:

### GitHub issues/PRs
Safe proposed-close categories:
- already implemented on current main
- cannot reproduce on current main after explicit verification
- belongs as skill/plugin/docs rather than core
- incoherent or unactionable
- stale beyond defined threshold with insufficient data

### JobZoom leads
Safe categories:
- duplicate of existing lead
- outside target geography or role level
- below ATS threshold after documented scoring
- expired/unavailable posting

Do not auto-reject strategic edge cases unless Ahmed has approved the rule.

### CMO content queue
Safe categories:
- duplicate topic
- stale draft needing refresh
- missing approval before publishing window
- published outside Notion and needs reconciliation

Do not auto-post. Propose schedule/approval actions only unless explicit posting automation is already approved.

### Email triage
Safe categories:
- newsletter/no action
- job alert/low priority
- interview/recruiter/customer action needed
- deadline/risk escalation

Never send replies without explicit approval.

### OpenClaw health
Safe categories:
- transient log noise
- repeated error needing investigation
- config drift needing approval
- failed cron requiring repair

Do not restart gateway casually from a user-facing run.

## Operating modes

### Scan-only
Use when first setting up or when rules are not approved. Produce records and dashboard only.

### Propose
Classify items and propose actions. No external writes.

### Apply
Only after approval or when policy explicitly allows. Apply in small batches and update records immediately.

### Watchdog
Scheduled mode. Update dashboard quietly. Alert only for decisions, risks, blockers, or meaningful state changes.

## Alert style

Use short decision cards, not process logs.

```text
🚨 [Workflow] sweeper - action needed
🎯 Action required
• Problem: [what is blocked or risky]
• Evidence: [1-2 facts]
• Next: [specific next action]
✅ Bottom line: [decision]
```

If nothing needs attention, stay silent or write only to the dashboard.

## Helper script

Use `scripts/render_dashboard.py` to create/update a README dashboard from item markdown files.

Example:

```bash
python3 scripts/render_dashboard.py --items ./items --output ./README.md --title "JobZoom Sweeper Status"
```

## Completion checklist

Before saying done:
- [ ] Source of truth inspected or clearly marked unavailable
- [ ] One markdown record exists per reviewed item, if item-level output was requested
- [ ] README/STATUS dashboard updated
- [ ] Proposed vs applied actions are clearly separated
- [ ] Any external write was explicitly approved or policy-backed
- [ ] Verification evidence is included
