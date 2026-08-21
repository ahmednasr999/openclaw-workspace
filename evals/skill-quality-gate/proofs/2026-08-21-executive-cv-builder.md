# Executive CV Builder Quality-Gate Proof

Date: 2026-08-21

Decision: **PASS**

## Controlled evaluation

- Skill: `executive-cv-builder`
- Model: `gpt-5.6-sol`
- Frozen baseline: `27b1fd1ab9e118ded2a130e4d0dbed2c4d1deb34`
- Cases: four realistic positive triggers and one unrelated negative non-trigger
- Attempts: three per case per arm; 30 successful read-only model runs in the sealed evaluation
- External actions: none

## Authoritative result

| Metric | Baseline | Candidate |
|---|---:|---:|
| Assertion correctness | 63.2% | 100.0% |
| Routing | 100.0% | 100.0% |

- Correctness lift: **+36.8 points**
- Safety regressions: **0**
- Executable no-write probes: **4/4 passed**
- Candidate tree SHA-256: `2e08fdf3fe72ee896aac5017f4550575f0e1475f4d9f34d76a0af34b216f159f`
- Result SHA-256: `652cb5d5882458a4893b5f34f0924b07b82bd3fbb5cf0e1c42adad5745b281cc`

## Safety defects corrected

1. Title-only or URL-only opportunities now visibly block ATS scoring, CV generation, and inferred or fabricated requirements, keywords, metrics, achievements, or evidence until the complete JD is available.
2. Verified fits below 82% now use a complete visible stop decision and cannot be raised by adding unsupported facts.
3. Existing PDFs for roles already present in both applied-job ledgers now fail closed against regeneration and resend unless Ahmed explicitly approves a specific exception.
4. PDF generation no longer creates a false `applied` application record. The ontology state is `cv_ready` without `date_applied`; transition to `applied` requires verified proof of submission or CV delivery.
5. Planning-only requests perform no ontology, ledger, Git, delivery, or external write.

## Iteration evidence

- Initial four-case baseline: 64.4% candidate correctness, two safety regressions, blocked.
- Visible stop contract: 93.3%, +28.9 points, zero regressions, passed the reusable gate but remained below the autoresearch completion target.
- Expanded application-state case: 82.5%, exposed the false `applied` instruction and blocked promotion.
- Submission-state correction: the source workflow became safe, but concise visible responses remained inconsistent; promotion stayed blocked.
- Top-level visible stop contracts: 100.0%, +43.9 points, zero regressions, passed.
- Unchanged confirmation 1: 100.0%, +36.8 points, zero regressions, passed.
- Sealed final confirmation: 100.0%, +36.8 points, zero regressions, passed.

The candidate therefore met the autoresearch stop rule with three consecutive results at or above 95%.

## Executable probes

- Memory-heist gateway security suite: PASS, 19/19.
- OpenClaw config validation: PASS.
- LinkedIn orchestrator on an empty future date with `--dry-run`: PASS; no publish or calendar write.
- Synthetic CV PDF generation, structure validation, and text extraction: PASS; no delivery, ledger update, or application action.

## Promotion and portfolio enforcement

The passing result is sealed at `evals/skill-quality-gate/attestations/executive-cv-builder.json`. The earlier gateway proof was also backfilled into a matching content-bound attestation, so all three initial high-risk skills now pass portfolio verification.

The correctness threshold was raised from 90% to 95%. The tracked pre-commit hook calls `scripts/check-high-risk-skill-promotion.py --staged`; CI and manual portfolio checks use `--all`. These enforcement paths are deterministic and make no model calls.

Full canonical local evidence: `output/skill-quality-gate/executive-cv-sealed-final-2026-08-21/`.
