---
name: codex-review-closeout
description: Use after non-trivial code edits, PR fixes, branch reviews, or when Ahmed asks for Codex review, second-pass review, autoreview, or coding closeout verification.
metadata:
  owner: CTO
  status: active
---

# Codex Review Closeout

Use this skill after non-trivial code edits or PR/comment fixes, before claiming coding work is done, shipped, or ready to merge. Do not use it for tiny obvious one-line edits unless risk is high or Ahmed asks for review.

## Outcome

Produce a verified coding closeout with tests/checks, structured autoreview findings, accepted/rejected decisions, and remaining risk.

## Operating rule

Review is evidence, not authority. Inspect source-of-truth repo state first, run focused checks, run the installed `autoreview` helper on the actual diff, inspect every finding manually, fix only real issues, and verify again before closeout. The helper must keep the selected model; Sol failures are reported and never silently routed to Terra.

## Tool ladder

1. Inspect repo state and the actual diff.
2. Run the smallest meaningful tests/checks for the edited area.
3. Run `skills/autoreview/scripts/autoreview` with the smallest truthful target (`local`, `branch`, or `commit`).
4. Read review findings and classify each as accepted, rejected, or deferred.
5. Fix accepted findings, rerun focused checks, and rerun review when material code changed.

## Approval boundary

Local code review, tests, and reversible workspace edits are allowed when coding work is in scope. External writes, commits, pushes, releases, PR comments, deployment, destructive cleanup, credential changes, and gateway/runtime changes require the existing approval path.

## References

- `references/review-targets.md` - which diff/branch to review.
- `references/autoreview-command.md` - command patterns, target selection, and failure behavior.
- `references/finding-triage.md` - accepted/rejected/deferred classification.
- `references/approval-boundaries.md` - what review work can and cannot do.

## Checklists

- `checklists/pre-review.md` - before running review.
- `checklists/finding-resolution.md` - while handling findings.
- `checklists/final-closeout.md` - before reporting done.

## Done means

- The actual edited diff was inspected.
- Focused tests/checks were run or a real blocker is named.
- Structured autoreview was run, or the exact unavailable status is stated.
- Findings are classified, not blindly applied.
- Accepted fixes were verified.
- The final closeout names files changed, checks run, review result, and remaining risk.
