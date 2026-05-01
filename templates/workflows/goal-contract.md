# Goal Contract Template

Use this for durable workstreams that need pause/resume state, verification evidence, and a clear owner. Keep it compact. Do not turn every small task into a goal.

## Goal

- Name:
- Owner:
- Status: active | paused | blocked | complete | retired
- Why it matters:
- Started:
- Review cadence:

## Success criteria

Done means:
- 

Not done if:
- 

## Permission profile

- Profile: read-only | local-write | external-write | runtime-change | disruptive/destructive
- Approval boundary:
- Safe continuation rule:

## Operating boundaries

Allowed without extra approval:
- read-only inspections
- workspace documentation updates
- non-destructive verification commands

Requires explicit approval:
- gateway config changes
- OpenClaw updates
- gateway restart/stop/start
- deleting queued/session artifacts
- external/public writes

## Current state

- Last verified:
- Evidence:
- Open risks:
- Next safe action:

## Pause/resume rule

Pause when:
- 

Resume when:
- 

## Stop/escalation rule

Escalate when:
- 

Retire when:
- 

## Verification contract

Before reporting progress or completion:
- inspect the actual artifact/outcome
- run the smallest relevant check
- record evidence, not just exit code
- state remaining risk

## Handoff note

If another agent/session takes over, include:
- current state
- source files
- latest evidence
- what not to touch
- next safe action
