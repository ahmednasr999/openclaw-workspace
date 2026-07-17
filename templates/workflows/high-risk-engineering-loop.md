# High-Risk Engineering Loop

Use for runtime patches, migrations, security-sensitive changes, large refactors, production integrations, or changes whose failure could corrupt data, break delivery, or destabilize an owned workflow. Routine low-risk edits use the normal inspect, edit, verify path.

## Contract

- Outcome:
- Owner:
- Scope and do-not-touch boundary:
- Permission profile:
- Approval boundary:
- Original reproduction or acceptance test:
- Rollback path:
- Executor-ready plan: `templates/workflows/agentic-engineering-plan.md` or task-specific plan path
- Planned-at revision and drift check:

## Work Queue

Convert concrete failures into a bounded queue. Valid queue sources are compiler errors, failing tests, reproducible defects, static-analysis findings, or accepted review findings. Do not add speculative cleanup.

## Loop

1. Capture before evidence with the smallest safe reproduction.
2. Validate the executor-ready plan and rerun its drift check. Refresh or stop if in-scope evidence changed materially.
3. Implement the smallest credible change. Every changed file must trace to an authorized plan step.
4. Run focused tests and the original reproduction.
5. Review A, correctness and regression mandate:
   - inspect changed code, tests, error paths, compatibility, and regression risk;
   - record findings as `accept`, `reject`, or `needs evidence`.
6. Review B, adversarial safety and operability mandate:
   - challenge assumptions, permissions, failure recovery, observability, rollback, and user-visible impact;
   - record findings independently of Review A.
7. Repair accepted findings only. Maximum two repair rounds.
8. After every material repair, rerun focused tests, the original reproduction, and any affected review checks.
9. Inspect the real outcome and complete the evidence record.

Reviews may be performed by separate agents only when the task explicitly permits delegation. Otherwise run two clearly separated local review passes with different mandates.

## Required Evidence

- Before evidence:
- Plan validation and drift-check evidence:
- Changed files:
- Focused tests:
- Original reproduction after fix:
- Review A findings and disposition:
- Review B findings and disposition:
- Repairs and retest evidence:
- Actual outcome inspected:
- Rollback evidence:
- Remaining risk:

## Stop States

- `success`: reproduction passes, both reviews are complete, accepted findings are repaired, and the real outcome is inspected.
- `clean-noop`: evidence shows no change is required.
- `blocked`: required evidence or access is unavailable after two bounded attempts.
- `approval-required`: next step crosses the named approval boundary.
- `exhausted`: two repair rounds completed without proof.

## Forbidden

- Do not let implementers merge, publish, restart, delete, or change production unless separately authorized.
- Do not treat two copies of the same review as independent reviews.
- Do not waive a failing test because another check passed.
- Do not mix unrelated refactors into the repair.
- Do not declare success from compilation, exit code, file creation, or reviewer confidence alone.

## Completion Gate

Validate the filled record with:

```bash
python3 scripts/check-high-risk-engineering-record.py <record.md>
```
