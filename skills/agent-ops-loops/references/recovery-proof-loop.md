# Recovery Proof Loop

Use when backup existence is not enough and we need proof that OpenClaw, JobZoom, or another system can actually recover.

## Inputs

- Recovery scenario and success criteria.
- Eligible backup or rollback point.
- Isolation plan for clean-room testing.
- RPO/RTO target if known.
- Data sensitivity constraints.

## Loop

1. Select a real eligible recovery point. Prefer current rollback artifacts unless the task asks for historical coverage.
2. Restore only inside a disposable isolated environment. Never overwrite production.
3. Use documented materials first. Record any hidden dependency or tribal step.
4. Verify integrity, representative reads, representative writes where safe, service start, config validity, plugin/runtime compatibility, and user-visible behavior where relevant.
5. Measure actual recovery time and recovery point freshness when possible.
6. Repair one blocker only if local and reversible, then destroy the environment and retry from a fresh restore.
7. Stop after the required consecutive success streak or when an exception requires explicit acceptance.

## Stop States

- `success`: every required scenario restores and passes verification from a fresh recovery point.
- `blocked`: backup missing, clean-room unavailable, credentials unavailable, or restore would expose sensitive data.
- `approval-required`: production failover, production overwrite, credential rotation, or external data exposure would be needed.
- `exception-accepted`: Ahmed explicitly accepts a documented recovery gap.

## Evidence

Close with backup path, scenario, restore method, RPO/RTO observed, verification checks, blocker/fix history, and destruction/cleanup confirmation for restored data.
