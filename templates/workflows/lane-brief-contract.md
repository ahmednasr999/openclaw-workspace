# Lane Brief Contract

Use this for recurring CEO/NASR, HR/JobZoom, CTO, or CMO briefs. The brief should keep one lane warm without becoming a universal daily report.

## Workflow

- Lane: CEO/NASR | HR/JobZoom | CTO | CMO
- Owner:
- Cadence:
- Delivery target:
- Permission profile:
- Approval boundary:

## ROLE

Act as the lane owner. Report only material changes, decisions, risks, blockers, and safe next work for this lane.

## READ SOURCES

Required:
- Current lane state file or latest report.
- Relevant memory owner file.
- Latest verified logs/artifacts for the lane.

Optional:
- External sources only when the lane contract already allows them.

Before writing the brief:
- Read durable lane state first.
- Compare new evidence against the last known state.
- Ignore noise that does not change a decision, risk, blocker, or next action.

## WORKFLOW

1. Read current state and last report.
2. Inspect only the minimum fresh evidence needed to detect material deltas.
3. Classify each delta as decision, risk, blocker, completed action, or noise.
4. Draft safe next work, but stop before any external, public, destructive, paid, credential, or runtime action.
5. Write back only durable decisions, open loops, and stable facts that meet the memory rule.

## OUTPUT

```markdown
## Decision
<one sentence: whether Ahmed needs to act>

## What changed
- <2-4 material deltas only>

## Evidence
- <source path, log line, message state, or artifact>

## Risk / blocker
<severity and cause, or "None">

## Draft safe next work
<drafted reply, recommended action, or "None">

## Memory writeback
<what was written and where, or "None">

## Needs Ahmed
No | <one decision required>
```

## DRAFT SAFE NEXT WORK

Allowed:
- Draft replies, briefs, status notes, recovery steps, CV/report artifacts, or content variants.
- Recommend the next approval-gated action.

Forbidden without approval:
- Sending emails or messages to third parties.
- Publishing posts.
- Applying to jobs.
- Deleting data.
- Changing credentials.
- Restarting/stopping live gateway/runtime services.
- Spending money or changing paid subscriptions.

## MEMORY WRITEBACK

Allowed:
- New decision.
- Corrected preference.
- Open loop with owner and next checkpoint.
- Stable project/person/workflow fact.
- Verified completed recovery or external action.

Targets:
- CEO/NASR: `memory/YYYY-MM-DD.md`, `MEMORY.md`, `USER.md`, `SOUL.md`, or lane report as appropriate.
- HR/JobZoom: `workspace-hr/reports/`, HR memory files, or protected JobZoom ledgers.
- CTO: `workspace-cto/reports/`, `TOOLS.md`, `AGENTS.md`, or trace files when a technical lesson was learned.
- CMO: `workspace-cmo/reports/`, content calendar state, `TOOLS.md`, or content workflow docs.

Rules:
- Use the smallest correct target.
- Prefer a pointer plus conclusion over raw copied private content.
- Do not create duplicate state if a canonical ledger or report exists.
- Do not write speculation as memory.

## TERMINATION

Stop when:
- Required sources were checked or explicitly marked unavailable.
- The brief is under 400 words unless a real incident needs more.
- Drafted work is clearly marked draft/recommendation only.
- Memory writeback is complete or explicitly "None".
- Approval-gated actions are left as `Needs Ahmed`.

## FORBIDDEN

- Do not expand the brief into a general dashboard.
- Do not include stale metrics without comparison or timestamp.
- Do not claim completion from a tool exit code alone.
- Do not send, post, apply, delete, restart, or change credentials from the brief.
- Do not notify Ahmed on green/no-action noise.
- Do not write raw sensitive source bodies into memory.
