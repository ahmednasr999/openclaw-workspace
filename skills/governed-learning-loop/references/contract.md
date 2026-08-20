# Governed Learning Loop Contract

## Stages

`observation -> candidate -> validated -> bounded proposal -> replay evaluated -> promotion-requested -> separately implemented -> verified`

The registry script records evidence and receipts only. It never executes a candidate, edits an approved target, deploys behavior, schedules work, or contacts an external system.

## Observation requirements

Each observation contains:

- `pattern_key`: stable semantic identity, such as `verification.compile-after-patch`
- `summary`: one reusable method, not a narrative of the session
- `run_id`: an independent execution, incident, or workflow identifier
- `source`: local evidence origin
- `evidence`: one or more local artifacts, reports, test names, or grounded references
- `verification`: the check and result that prove the method worked
- `target_type`: `rule`, `skill-update`, `new-skill`, `script`, `test`, or `solution`
- `occurred_at`: ISO-8601 timestamp

The script rejects common credential assignments, bearer values, private keys, and long token-like strings. The operator must still avoid personal data and hidden runtime instructions.

## Candidate gate

A candidate is reviewable only when all are true:

1. At least two observations share the same `pattern_key`.
2. At least two distinct `run_id` values exist.
3. At least two distinct evidence fingerprints exist.
4. Every observation has a non-empty verification result.
5. Target types do not conflict.

Candidate status `review` means evidence is ready for human judgment. It does not mean the method is correct for every workflow or approved for deployment.

## Bounded proposal and replay gate

A proposal binds one candidate to:

- one exact approved target path;
- one candidate artifact hash;
- one curated and sanitized evaluation-suite hash;
- one to four explicit edits;
- separate validation and locked-test tasks;
- at least two independent replay runs;
- a minimum absolute improvement threshold;
- a candidate cost ceiling and maximum cost-increase ratio;
- at least one critical task with zero permitted regression.

The result packet must contain each locked task exactly once in every run. Every run must meet the improvement threshold. Locked-test averages cannot regress, and no critical task can score below its baseline in any run. Candidate cost must remain within both cost gates.

The suite uses `data_policy: curated-sanitized`. Raw transcripts, hidden runtime instructions, credentials, personal data, and candidate-selected test substitutions are outside the contract.

An evaluation is `accepted` only when every gate passes. A rejected evaluation remains in `negative_evidence` with its result hash and failure reasons. A later accepted result does not erase earlier negative evidence.

## Promotion receipt

`request-promotion --proposal` requires:

- a candidate that passes readiness validation;
- a bounded proposal with an accepted replay evaluation;
- the exact target path;
- approver identity;
- an explicit approval reference.

Allowed target paths are relative workspace paths under `skills/`, `scripts/`, `tests/`, or `docs/solutions/`, plus the exact core files `AGENTS.md`, `SOUL.md`, and `TOOLS.md`. New promotion receipts always require an evaluation-passed proposal; legacy candidate-only receipts remain readable but cannot authorize a new implementation record. The command records intent only and never writes the target.

## Implementation record

Implementation occurs only as a separate task within the target's normal authority boundary. After target-specific tests and a real artifact or behavior check pass, `record-implementation` requires the live target hash to match the proposal's approved artifact hash, then records the target hash, verification evidence, and rollback method against the promotion receipt. It does not make the change itself.

## Ownership and rollback

- Owner: NASR/main.
- Registry: `data/learning-loop/registry.json`.
- Lock: `data/learning-loop/.lock`.
- Review report: `reports/learning-loop/latest.md`.
- Evaluation packets: `reports/learning-loop/evaluations/`.
- Rollback: remove an unpromoted observation or candidate from the registry using a reviewed local edit, then rebuild. Never erase negative evidence or an implemented change through this registry; revert the owning artifact through its normal workflow and retain the receipt trail.
