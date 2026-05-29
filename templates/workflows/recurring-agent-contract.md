# Recurring Agent Contract

Use this before turning a repeated workflow into a skill, slash command, cron job, or agent routine. Keep the contract short enough to run repeatedly without interpretation drift.

## Workflow

- Name:
- Owner: CEO/NASR | HR | CTO | CMO | JobZoom
- Cadence: manual | scheduled | event-triggered
- Permission profile: read-only | local-write | external-write | runtime-change | disruptive/destructive
- Approval boundary:

## ROLE

Name the role that limits the work. Examples: chief of staff, audit-only reviewer, research coordinator, content repurposer, recovery reporter.

## READ SOURCES

List only the sources the workflow may read.

Required:
- <source>

Optional:
- <source>

Unavailable source behavior:
- Fail loudly when a required source is missing.
- Do not silently skip required evidence.

## WORKFLOW

Use bounded steps. Each step should produce evidence or a decision.

1. <step>
2. <step>
3. <step>

## OUTPUT

Define the exact sections and their maximum size.

```markdown
## Decision

## What changed

## Evidence

## Risk / blocker

## Action taken / next

## Needs Ahmed
```

## DRAFT SAFE NEXT WORK

Define what the workflow may prepare but not execute.

Allowed draft work:
- <draft/recommendation>

Approval boundary:
- Do not send, post, apply, delete, purchase, publish, restart, or change credentials unless the workflow has an explicit pre-approved path.

## MEMORY WRITEBACK

Define what durable context may be written after the output is verified.

Allowed writeback:
- Decisions that should survive the thread.
- Open loops that need future follow-up.
- Stable project/person/workflow facts.
- Corrections Ahmed made to the workflow.

Writeback target:
- <memory file, report file, or none>

Writeback bans:
- Do not store raw private source content when a short fact or pointer is enough.
- Do not create new memory locations when an existing owner file fits.
- Do not write speculative conclusions as facts.

## TERMINATION

Use a condition the agent can verify by inspecting the output or source state.

Examples:
- Stop when all required sources are processed and the output is under 400 words.
- Stop when each target has all required fields filled.
- Stop at one page. If it does not fit, drop lower-priority detail.
- Stop at the timebox. Do not start another pass after the timebox expires.

## FORBIDDEN

State the behaviors that would make the workflow unsafe or noisy.

Default bans:
- Do not invent metrics or sources.
- Do not send external messages, emails, applications, posts, or public updates without approval.
- Do not add bonus sections.
- Do not predict when the workflow is audit-only.
- Do not summarize a summary.
- Do not repeat content across channels with the same opening hook.
- Do not execute drafted work without approval.
- Do not write durable memory unless it matches the writeback rule.
- Do not declare success from tool exit code alone.

## Verification

Before reporting completion:
- Inspect the actual artifact, message, report, or state.
- Quote or link the evidence used.
- State remaining uncertainty.
- Log a trace if the workflow failed, drifted, or required correction.
