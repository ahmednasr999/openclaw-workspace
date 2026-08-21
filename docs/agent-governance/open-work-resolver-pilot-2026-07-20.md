# Open-Work Resolver Pilot - 2026-07-20

## Task Contract

- Outcome: create one deterministic, read-only Resolver for unfinished cross-agent work and pilot it on the live LinkedIn +30 application campaign.
- Constraints and non-goals: do not submit applications, restart workers, change prompts, weaken ATS/CV/role-fit gates, message third parties, or create a second source of truth.
- Definition of done: the Resolver independently reports owner, target, verified progress, next action, evidence, blocker, stale deadline, and verified closure; a deterministic schedule refreshes the report; the live pilot reconciles with the campaign's strict ledger and service state.
- Evidence required: the campaign strict-ledger audit, supervisor state, systemd service state, generated JSON/Markdown/briefing views, unit tests, and a live run.
- Authority and approval boundary: reversible workspace edits, a read-only local report, and a deterministic local cron are approved. External actions and production executor changes remain outside the Resolver's authority.
- Stop condition: success when tests pass and the live report agrees with the canonical campaign evidence; blocked if the strict ledger, supervisor state, or service state cannot be read; intervention required if those sources contradict or become stale.
- Owner: NASR owns the Resolver; HR owns the LinkedIn +30 executor.
- Review tier: substantial.

## State Contract

Every tracked outcome must expose:

`owner -> target -> verified progress -> next action -> evidence -> blocker -> stale deadline -> verified close`

Resolver states are bounded:

- `in_progress`: executor is active, evidence agrees, and the heartbeat is fresh.
- `progress`: verified count advanced since the prior Resolver snapshot.
- `intervention_required`: evidence conflicts, the worker is inactive, or the stale deadline passed.
- `approval_required`: the executor surfaced a decision that crosses an approval boundary.
- `blocked`: canonical evidence cannot be read.
- `verified_closed`: the target is met in the canonical strict ledger; executor prose or file creation alone cannot close the item.

## Pilot Evidence

The LinkedIn adapter reads only:

1. `/root/.openclaw/workspace-hr/tools/linkedin-plus30-status.py`, which uses the campaign's shared strict-ledger audit.
2. The dated supervisor state file and its heartbeat/counter.
3. The dated systemd service state and main PID.

The adapter fails closed on missing evidence, counter disagreement, inactive service before completion, stale heartbeat, or missing supervisor PID.

## User-Facing Brief Contract

`reports/open-work-resolver/briefing.json` contains only:

- progress and active outcomes,
- intervention or approval needs,
- verified closures.

It intentionally omits general narrative status. The internal Markdown and JSON snapshots exist for audit and troubleshooting, not as another user-facing daily report.

The existing deterministic morning brief reads this file and renders only those three buckets under `Open Work`.

## Rollout

This is a single-item pilot. Add another workflow only after the LinkedIn campaign demonstrates that stale detection, evidence reconciliation, and closure classification are trustworthy. The Resolver may recommend an action, but it may not execute one.
