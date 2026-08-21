# Governed Learning Loop Contract

## Stages

`observation -> candidate -> validated -> promotion-requested -> separately implemented -> verified`

Only the first four stages are implemented by the v1 script. Promotion and verification occur in a separately approved task because the target may be an active skill, core instruction, script, or test.

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

## Promotion receipt

`request-promotion` requires:

- a candidate that passes validation;
- the exact target path;
- approver identity;
- an explicit approval reference.

Allowed target paths are relative workspace paths under `skills/`, `scripts/`, `tests/`, or `docs/solutions/`, plus the exact core files `AGENTS.md`, `SOUL.md`, and `TOOLS.md`. The command records intent only and never writes the target.

## Ownership and rollback

- Owner: NASR/main.
- Registry: `data/learning-loop/registry.json`.
- Lock: `data/learning-loop/.lock`.
- Review report: `reports/learning-loop/latest.md`.
- Rollback: remove an unpromoted observation or candidate from the registry using a reviewed local edit, then rebuild. Never erase an already implemented change through this registry; revert the owning artifact through its normal workflow.

