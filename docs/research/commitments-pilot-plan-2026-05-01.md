# OpenClaw Commitments Pilot Plan - 2026-05-01

Source reviewed: `https://docs.openclaw.ai/concepts/commitments`

## Decision

Do not enable inferred commitments globally yet.

Run commitments as a controlled pilot only after explicit config-change approval. The feature is useful, but it adds hidden LLM extraction, heartbeat-delivered check-ins, and a risk of noisy follow-ups if left broad.

## What Commitments Are

Commitments are short-lived inferred follow-up memories. They sit between memory and cron:

- Memory: durable facts and preferences.
- Cron: exact reminders and scheduled automation.
- Commitments: inferred natural follow-ups from conversation context.

Examples that fit commitments:

- Ahmed mentions an interview tomorrow, check in afterward.
- Ahmed sounds exhausted, check in later if useful.
- The assistant says it will follow up when an open loop is due.
- A thread is waiting for an answer and should not silently disappear.

Examples that should not use commitments:

- JobZoom daily scan, use cron.
- Disk guard, use cron.
- Backups, use cron.
- Exact reminders like "ping me at 3 PM", use cron.
- Durable preferences like salary importance, use memory.

## Current State

Current config has no `commitments` block, so the feature is effectively disabled.

Schema fields:

```json
{
  "commitments": {
    "enabled": true,
    "maxPerDay": 1
  }
}
```

`commitments.enabled` enables hidden extraction, storage, and heartbeat delivery.
`commitments.maxPerDay` limits delivered inferred follow-ups per agent session in a rolling day. Default is 3.

## Recommended Pilot

Duration: 7 days.

Scope:

- Main agent only.
- Telegram DM behavior observed manually.
- `maxPerDay: 1` to prevent noisy check-ins.
- No use for exact reminders, operational jobs, or critical automation.

Config if Ahmed explicitly approves enabling:

```json
{
  "commitments": {
    "enabled": true,
    "maxPerDay": 1
  }
}
```

## Success Criteria

The pilot is useful only if it creates helpful check-ins without noise.

Pass signals:

- It remembers a real open loop Ahmed would value.
- It does not duplicate cron reminders.
- It does not create vague "just checking in" messages.
- It stays scoped to the right conversation/channel.
- It produces no private/internal-context leakage.

Fail signals:

- It nags.
- It triggers on weak or casual statements.
- It duplicates reminders or standing ops.
- It adds visible noise during busy work.
- It creates check-ins that Ahmed did not need.

## Operating Rules During Pilot

- Treat due commitments as optional prompts, not obligations to interrupt Ahmed.
- If the state is unchanged and the check-in is not useful, stay silent.
- Prefer decision-card check-ins: what loop is open, why it matters, recommended next action.
- Do not promote commitments into memory unless Ahmed states a durable preference or fact.
- Do not replace cron with commitments for exact timing.

## Review Method

During the pilot, inspect stored commitments when needed:

```bash
openclaw commitments --all
openclaw commitments --agent main
openclaw commitments --status pending
```

Dismiss noisy records if needed:

```bash
openclaw commitments dismiss <id>
```

At the end of 7 days, decide one of:

1. Keep enabled with `maxPerDay: 1`.
2. Increase to `maxPerDay: 2` only if value is proven.
3. Disable if noisy or redundant.

## Approval Boundary

Enabling commitments is a gateway config change. Do not enable it without explicit approval for the config change.

This plan creates no runtime, gateway, or config changes by itself.
