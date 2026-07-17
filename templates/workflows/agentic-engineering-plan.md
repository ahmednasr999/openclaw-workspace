# Agentic Engineering Plan

Use for non-trivial coding, automation, workflow, recovery, or delegated engineering. Write it so a fresh-context executor can act without the planning conversation. Keep it proportionate: one plan for one coherent outcome.

## Plan Metadata

- Status: draft | ready | in-progress | blocked | complete | superseded
- Owner:
- Planned at: commit `<short-sha>` on `<YYYY-MM-DD>` | non-git snapshot `<identifier>`
- Depends on: none | `<plan/path or prerequisite>`

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat <planned-at-sha>..HEAD -- <in-scope-paths>`
> If an in-scope path changed, compare current source with the evidence anchors below. Refresh or supersede the plan before execution when the intended change or verification no longer matches.

## Objective

- Target outcome:
- User-visible success condition:
- Why this matters:

## Evidence And Current State

- Source anchors: `<file:line>` - `<fact established by direct inspection>`
- Existing convention to follow: `<file:line>` - `<pattern>`
- Reproduction or baseline:
- Raw evidence to preserve:

Do not copy secret values into this plan. Cite only the location and credential type.
The plan owner must personally verify every cited anchor before handoff. Helper findings are leads, not source-of-truth evidence.

## Scope

- In scope:
- Files likely touched:
- Do not touch:
- Non-goals:

## Authority And Safety

- Permission profile: read-only | local-write | external-write | runtime-change | destructive
- Approval boundary:
- Rollback path:
- External/public/credential/paid/runtime action involved: yes/no

## Owner And Helpers

- Owning session/agent:
- Helpers, if explicitly permitted:
- Independent assignment and expected evidence for each helper:
- Maximum concurrency: 4

## Ordered Implementation Steps

### Step 1: `<imperative outcome>`

- Files:
- Change:
- Preserve:
- Verify command/check:
- Expected result:

### Step 2: `<imperative outcome>`

- Files:
- Change:
- Preserve:
- Verify command/check:
- Expected result:

## Test Plan

- Existing tests to run:
- New or changed tests:
- Original reproduction after implementation:
- Actual artifact or behavior to inspect:

## Stop Conditions

- An evidence anchor or in-scope file has materially drifted.
- A required dependency or approval is missing.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires out-of-scope files or a new external/runtime/destructive action.

## Done Criteria

- [ ] Every ordered step completed or explicitly skipped with evidence.
- [ ] Focused tests and original reproduction pass.
- [ ] Actual user-visible or operational outcome inspected.
- [ ] Changed files remain inside scope.
- [ ] Accepted review findings repaired and reverified.
- [ ] Remaining risk and rollback evidence recorded.

## Review Handoff

- Diff base and target:
- Reviewer focus:
- Known trade-offs:
- Deliberately deferred work:

## Closeout

- Files/artifacts changed:
- Commands/checks and results:
- Deviations from plan:
- Evidence of success:
- Residual risk:

Validate a completed plan before handoff or execution:

```bash
python3 scripts/check-agentic-engineering-plan.py <plan.md>
```
