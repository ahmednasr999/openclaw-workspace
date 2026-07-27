# Production Workflow Contract

## Decision

Use a small persisted-stage contract for repeatable production workflows. Keep
judgment inside bounded stages; keep sequencing, retries, evidence, terminal
states, and approval boundaries deterministic.

Do not add a graph framework until this contract becomes insufficient in at
least two proven workflows.

## Required Run Manifest

Every governed run records:

- workflow and run identity;
- canonical input hash and ordered stage list;
- per-stage status, attempt count, timestamps, error classification, output
  path, and SHA-256;
- artifact paths, sizes, and SHA-256 values;
- independent deterministic judge result;
- terminal state and reason.

Stage outputs are immutable once completed. A resumed run verifies the stored
hash and reuses the output; it does not silently rerun or overwrite a completed
stage.

## Stage Rules

1. A stage cannot start until every predecessor is complete.
2. A completed stage is idempotently loaded after its evidence hash passes.
3. A failed stage may be retried once. Two failed attempts end in `exhausted`.
4. Resume inputs must exactly match the original canonical input hash.
5. External artifacts are recorded with hashes before final judgment.
6. The executor cannot report operational success when the judge fails.
7. Shared-resource locks must use a bounded acquisition timeout inside the
   stage that needs the resource. Lock contention is persisted as stage
   evidence; it must never block before checkpoint allocation.

## Terminal States

- `success`: the requested internal outcome is complete and independently
  verified.
- `clean_noop`: the source proves that no action was required.
- `blocked`: the current stage failed once or needs missing evidence/access and
  can be resumed safely.
- `approval_required`: every stage and the judge passed, but the next action is
  public, external, paid, credentialed, destructive, or otherwise gated.
- `exhausted`: the bounded attempt budget ended without proof.

## Judge Contract

The judge is read-only and separate from discovery/execution code. It reads the
manifest, persisted stage outputs, and final artifacts. It must be runnable as a
standalone command and return non-zero for any failed invariant.

Before trusting a judge, test it against deliberately broken fixtures:

- missing artifact;
- corrupt stage output or artifact hash;
- duplicate identity or idempotency key;
- missing required evidence;
- inconsistent run ID or command;
- false terminal success.

## LinkedIn Radar Reference Mapping

`source -> extract -> validate -> rank -> approval`

- `source`: authenticated feed/search evidence and browser events.
- `extract`: deduplicated candidate pool.
- `validate`: live permalink, author/content, comment-control, and draft
  evidence.
- `rank`: quality classification, uniqueness gates, and five-candidate target.
- `approval`: immutable report, card JSON, and approval pack.

A valid five-card run ends at `approval_required`. This does not authorize any
LinkedIn post, like, comment, message, or other external action.

The shared authenticated-browser lock is bounded at 30 seconds. If HR or
another approved LinkedIn workflow owns it, `source` ends as resumable
`blocked`, later stages remain pending, and no approval artifact is created.

## Rollout Rule

Prove the contract with isolated tests and one read-only live radar sample.
Only then reuse it in content publishing, JobZoom, or daily intelligence. Each
migration keeps its existing owner, business rules, and approval boundaries.
