# Production Error Sweep

Use for scheduled or ad hoc reliability passes over OpenClaw, gateway, cron, Telegram, JobZoom, HR, CMO, Codex, or app logs.

## Inputs

- Agreed log window and systems.
- Known noise patterns and recent maintenance context.
- Repo/config paths that own the failing behavior.
- Safe test or probe commands.

## Loop

1. Read the actual logs for the agreed window. Do not rely on subjects, alerts, or counts alone.
2. Group repeated symptoms into likely incidents.
3. Classify each group:
   - actionable product/runtime defect
   - expected noise
   - transient upstream failure
   - already-known issue
   - needs more evidence
4. For each actionable issue, trace to owner code/config/data before changing anything.
5. Apply the smallest local fix only when the approval boundary allows it.
6. Verify with the narrowest meaningful test, probe, replay, or log check.
7. Repeat once if verification fails and the next fix is clear. After two failed attempts, stop and report the blocker.

## Stop States

- `success`: actionable error fixed and verified.
- `clean-noop`: no actionable errors found in the inspected window.
- `blocked`: logs, repo, credentials, or safe test path are unavailable.
- `approval-required`: fix requires gateway restart, production change, external message, credential, destructive action, or paid action.

## Evidence

Close with incident group, root cause, changed files if any, checks run, before/after evidence, and remaining risk. Sanitize tokens, credentials, private payloads, personal data, and customer/job data.
