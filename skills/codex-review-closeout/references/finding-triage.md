# Finding Triage

Classify every finding before acting.

## Accepted

Accept when the finding identifies a real bug, regression, security issue, missing verification, broken behavior, or maintainability problem in the edited scope.

Required action:
- fix the smallest real issue
- rerun focused tests/checks
- rerun review if the fix materially changed code

## Rejected

Reject when the finding is speculative, contradicts source-of-truth code, requests unrelated refactor, expands scope, or weakens an approval/safety boundary.

Required action:
- record the reason briefly
- do not perform unrelated cleanup to satisfy the review

## Deferred

Defer only when the issue is real but outside the current request or requires a separate approval/risk decision.

Required action:
- name the risk and recommended follow-up
- do not present the task as fully fixed if the deferred item affects the requested outcome

## Quality bar

Never claim “Codex said OK” as proof. Proof is changed files inspected, checks run, and findings resolved or consciously rejected.
