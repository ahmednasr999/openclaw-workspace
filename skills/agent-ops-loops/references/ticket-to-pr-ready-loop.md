# Ticket To PR Ready Loop

Use when a bug report, complaint, failing behavior, alert, or ticket needs to become a verified engineering change.

## Inputs

- Ticket or failure statement.
- Expected behavior and actual behavior.
- Smallest representative reproduction path.
- Relevant repo, service, or config owner.
- Tests/checks that can prove the fix.

## Loop

1. Restate the failure in one sentence and list assumptions.
2. Reproduce the failure in the smallest safe environment. For UI, use screenshot or recording evidence. For backend, use tests, logs, traces, or replay.
3. If reproduction fails, make one more serious attempt with a different angle. After two attempts, stop with evidence.
4. Trace root cause to specific code/config/data.
5. Make the smallest credible fix. Do not fold unrelated refactors into the patch.
6. Run the original reproduction and targeted regression checks.
7. If material code changed after review, rerun focused checks and review where appropriate.

## Stop States

- `success`: failure reproduced, fixed, and verified with before/after proof.
- `blocked`: cannot reproduce and no safe next evidence source exists.
- `approval-required`: fix requires external write, production action, credentials, destructive change, gateway restart, or public/user-facing commitment.
- `deferred`: root cause is clear but fix exceeds the current scope.

## Evidence

Close with cause, changed files, before proof, after proof, tests/checks, risk, and PR-ready summary. Match evidence to failure type: screenshot for UI, logs/tests for backend, benchmark for performance, sanitized trace for integrations.
