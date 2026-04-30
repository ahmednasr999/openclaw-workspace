# OpenClaw Agent Workflow Blueprint

Source inspiration: `warpdotdev/oz-for-oss` inspection on 2026-04-29. This is a pattern extraction for OpenClaw/NASR, not copied implementation.

## Recommendation

Adopt the workflow pattern, not the product shape:

`request -> triage -> spec -> implementation -> review -> verification -> closeout`

Use it for non-trivial coding, prompt/governance, workflow automation, and external-action systems. Keep quick reversible tasks lightweight.

## Why this matters

Warp/Oz succeeds operationally because agents do not jump straight from issue to code. They move through explicit state gates, each with a bounded output and verification step. OpenClaw should use the same discipline for higher-risk work while preserving its advantage: personal orchestration, memory, scheduling, messaging, and multi-channel execution.

## Workflow states

| State | Purpose | Entry signal | Exit signal |
|---|---|---|---|
| Intake | Capture the request and constraints | User request, heartbeat finding, cron result, repo issue, system alert | Clear scope or triage needed |
| Triage | Classify, dedupe, estimate severity, identify owner | Non-trivial or ambiguous request | `needs-info`, `ready-to-spec`, or `ready-to-implement` |
| Spec | Define outcome before implementation | `ready-to-spec` | Product/behavior spec accepted or self-contained enough |
| Tech plan | Map implementation path and risks | Complex implementation or cross-file change | Concrete plan with files, tests, rollback/stop rules |
| Implement | Make the smallest complete change | `ready-to-implement` | Candidate change exists locally |
| Review | Independent critique against spec and diff | Candidate change exists | approve, approve-with-nits, or request-changes |
| Verification | Prove requested outcome exists | Review passed or fix applied | Test/build/lint/screenshot/direct inspection evidence |
| Closeout | Report outcome and residual risk | Verification complete | User-facing concise report and durable memory if warranted |

## State labels

Use labels conceptually even outside GitHub:

- `needs-info`: missing non-retrievable input blocks safe progress.
- `ready-to-spec`: problem is real but outcome/behavior is not defined enough.
- `ready-to-implement`: scope and success criteria are clear enough to change state.
- `blocked-external`: waiting on account, API, approval, human, or third-party state.
- `review-required`: external/public/destructive/high-risk or quality-sensitive output.
- `verified`: outcome inspected against the real source/artifact/delivery/user-visible state.

## Decision rule: when to require a spec

Require at least a short spec when any of these are true:

- multi-file or architecture change
- cron/automation that will recur
- external/public/destructive action path
- gateway/config/runtime behavior change
- job search/CV/application workflow change
- content/posting workflow with reputation risk
- user correction indicates previous ambiguity or quality miss
- more than one agent/session will work on the task

Skip formal spec for:

- one-file obvious fixes
- read-only analysis
- small reversible edits with clear success criteria
- urgent operational checks where delay is riskier than action

## Minimal specs

### Product/behavior spec

Use for what should happen.

```md
# Product Spec: <title>

## Problem
<what is broken or needed>

## Goal
<desired user-visible outcome>

## Non-goals
<what this will not solve>

## Success criteria
- <observable pass condition>
- <quality bar>

## Edge cases
- <case>

## Approval gates
- <external/public/destructive/high-risk approvals>
```

### Tech plan

Use for how to change it.

```md
# Tech Plan: <title>

## Current state
<files/systems inspected>

## Proposed change
<smallest complete change>

## Files likely touched
- `<path>`: <why>

## Verification
- <test/lint/build/manual inspection>

## Rollback / stop rules
- <when to stop and ask>
```

## Sub-agent dispatch model

Use sub-agents as role specialists, not vague parallel workers.

Recommended roles:

1. **Triage agent**
   - Classify issue, dedupe against known state, identify missing info, suggest label.
   - Must not edit files or take external actions.

2. **Spec agent**
   - Produce product/behavior spec and optionally a tech plan.
   - Must identify non-goals and approval gates.

3. **Implementation agent**
   - Implement only against the accepted spec/plan.
   - Must report files changed, tests run, unresolved risk.

4. **Review agent**
   - Critique diff/artifact against spec and quality bar.
   - Must not modify files unless explicitly asked.

5. **Verification agent**
   - Run/inspect final evidence.
   - Must distinguish tool success from outcome success.

## Default non-coding agent brief

```md
Objective: <specific outcome>

Context: <only necessary background and source paths>

Success criteria:
- <observable condition>
- <quality bar>

Scope:
- Read-only / edit allowed / external action forbidden unless approved.
- Do not change unrelated files.

Retrieval budget:
- Start with <source>. Search again only if required facts are missing or evidence is weak.

Verification:
- <required evidence before done>

Stop conditions:
- Ask/stop if <approval, missing input, destructive action, uncertainty>.

Final output:
- Decision/recommendation
- Evidence
- Remaining risk
```

## External-action gates

Never let an agent independently complete these without explicit approval:

- sending email
- posting publicly
- messaging third parties
- applying to jobs
- deleting/archiving important content
- changing gateway config/runtime
- merging/pushing to protected branches
- paid provider/account changes

For these, agents may prepare drafts, diffs, or recommendations, then stop.

## Self-improvement guardrail

For recurring agent improvement loops, use narrow write surfaces.

Pattern:

- Each self-improvement loop owns exactly one path family.
- The loop may propose changes only under that path family.
- Any changed file outside allowed prefixes aborts the run and requires human review.

Example ownership:

| Loop | Allowed surface |
|---|---|
| content visual quality | `skills/content-claw/`, `workspace-cmo/skills/*/eval/` |
| coding dispatch | `docs/agent-governance/`, `AGENTS.md` targeted anchors |
| tool gotchas | `TOOLS.md`, relevant skill docs |
| user preferences | `USER.md`, memory daily notes |
| gateway runtime | dedicated CTO docs/scripts only, approval-gated |

## OpenClaw implementation options

### Option A - lightweight now

Use this blueprint manually in current sessions and sub-agent briefs.

Pros: immediate, low risk.  
Cons: depends on discipline.

### Option B - file-backed workflow

Create reusable templates under `templates/workflows/`:

- `triage.md`
- `product-spec.md`
- `tech-plan.md`
- `implementation-brief.md`
- `review-brief.md`
- `verification.md`

Pros: reusable, low complexity.  
Cons: still manually invoked.

### Option C - automated state machine

Build a small script/skill that creates workflow folders and advances states:

```text
workflows/<id>/intake.md
workflows/<id>/triage.md
workflows/<id>/spec.md
workflows/<id>/plan.md
workflows/<id>/review.md
workflows/<id>/verification.md
```

Pros: durable operating system for complex work.  
Cons: more machinery; only worth it after repeated use.

## Recommended next action

Start with Option B.

Create a small template set and update the coding/non-coding dispatch docs to point to it. Do not build an automated state machine yet. Prove quality on real tasks first.
