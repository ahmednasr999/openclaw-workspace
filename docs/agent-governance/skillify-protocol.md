# NASR Skillify Protocol

## Purpose

Make agent improvement durable across CEO/NASR, HR, CTO, CMO, and JobZoom.

A failure should not only produce an apology or a memory note. If it can happen again, it must become a reusable rule, skill, deterministic script, test, or scheduled check.

## Scope

Applies to all agent workstreams:

| Agent | Owns skillifying |
|---|---|
| CEO / NASR | Strategy, routing, memory, cross-agent governance, user-facing quality, approval policy |
| HR | Job search, CV, ATS, recruiter/email, pipeline, application-lock, JobZoom handoffs |
| CTO | Gateway, config, scripts, runtime patches, health checks, tool behavior |
| CMO | LinkedIn, content, brand, image generation, posting workflows, engagement |
| JobZoom | Search coverage, dedupe, applied ledger, report delivery, protected daily full-scan lane |

NASR owns governance. Each lane owns its local fixes and tests.

## Trigger Conditions

Skillify when any of these happens:

1. Ahmed corrects the agent.
2. A command, tool, API, script, cron, post, or delivery fails.
3. A repeated workflow requires Ahmed to babysit.
4. A safety or approval boundary is wrong or noisy.
5. A deterministic task is being handled by model reasoning instead of code.
6. A working ad-hoc fix should become permanent.
7. A capability exists but is unreachable, duplicated, stale, or undocumented.

## Decision Ladder

Use the smallest durable fix that prevents recurrence:

1. **Memory note** - one-off fact or preference.
2. **Learning entry** - correction, error, best practice, or feature request.
3. **Workflow rule** - broad behavior in `AGENTS.md`, `TOOLS.md`, `SOUL.md`, or lane `SOUL.md`.
4. **Skill** - reusable procedure with clear trigger and owner.
5. **Deterministic script** - exact, repeatable logic that should not rely on model judgment.
6. **Test/eval/check** - proof the route or behavior stays fixed.
7. **Cron/doctor check** - recurring drift detection where time-based monitoring matters.

Do not overbuild from one minor incident, but do not leave repeated failures as notes.

## Minimum Skillify Closeout

For any promoted failure, close with:

- Incident: what failed or was corrected.
- Owner: CEO/NASR, HR, CTO, CMO, or JobZoom.
- Durable fix: memory, learning, workflow rule, skill, script, test, or cron.
- Verification: command, test, inspection, delivery proof, or named blocker.
- Residual risk: what can still fail.

## Skill Quality Gate

A real skillified fix should usually have:

1. Trigger: when the agent must use it.
2. Scope: what it does and does not own.
3. Deterministic path: script/tool/check when exactness matters.
4. Tests or smoke check: smallest proof it works.
5. Resolver/reachability: how the agent knows it exists.
6. DRY check: no duplicate skill/workflow owns the same lane.
7. Filing rule: where outputs, traces, reports, and memories belong.

If only steps 1-2 exist, call it a draft rule, not a finished skill.

## Required Behavior

- Prefer local lane paths. HR should not reach into CMO or main workspace helpers when a local helper should exist.
- Convert deterministic work into scripts or checks. Do not rely on model math, fragile memory, or prompt promises.
- Keep approval gates for outbound, public, destructive, paid, or config/runtime-changing actions.
- Routine local read-only inspection should not interrupt Ahmed.
- Verify real outcome before declaring the failure impossible to repeat.

## Audit Expectations

A periodic or on-demand audit should flag:

- Pending high-priority learnings older than 7 days.
- Errors without a suggested fix.
- Multiple lane learnings about the same failure class.
- Skills without `SKILL.md`.
- Scripts referenced by skills that no longer exist.
- Known runtime patches without post-update checks.

Run the advisory audit with:

```bash
python3 scripts/skillify-audit.py
python3 scripts/skillify-audit.py --json
python3 scripts/skillify-audit.py --fail-on high
```

The audit is advisory by default. Do not auto-fix public, destructive, credential, gateway, or external-write workflows without explicit approval.
