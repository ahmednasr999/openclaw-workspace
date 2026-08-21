# Governed Outcome Loops - 2026-07-18

## Task Contract

- Outcome: add controlled outcome governance to JobZoom and the CMO content pipeline without changing their production decisions.
- Constraints and non-goals: preserve JobZoom's full scan, scoring prompts, CV generation, delivery, and applied-role exclusion; preserve CMO approval and publishing gates; do not add cron, public actions, runtime changes, or self-rewriting behavior.
- Definition of done: each workflow has an executor-independent, read-only verifier that reports execution metrics, real-outcome metrics, counter-metrics, evidence coverage, and a bounded adaptation recommendation.
- Evidence required: canonical JobZoom database, canonical career-pipeline database, CMO published-post ledger/metrics CSV, generated JSON and Markdown reports, unit tests, and one real-data shadow run per workflow.
- Authority and approval boundary: reversible local edits and read-only reports are approved. Production prompt, schedule, publishing, application, runtime, and external changes remain approval-required.
- Stop condition: success when both shadow reviews run on real data and prove they cannot modify production; warning when outcome evidence is incomplete; blocked when a canonical evidence source is unavailable.
- Owner: NASR coordinates; JobZoom and CMO retain lane ownership.
- Review tier: substantial.

## Control Pattern

Execute -> independently verify -> measure grounded outcome -> recommend bounded adaptation

The verifier is not allowed to call the executor, alter production records, change prompts, modify schedules, apply to jobs, or publish content. It reads evidence and writes a separate review report.

## Metrics Contract

| Workflow | Execution success | Grounded outcome | Counter-metric | Source of truth |
|---|---|---|---|---|
| JobZoom | 150-search run completed, report delivered, selected CV count reconciled, scoring calls parseable | applications, qualified responses, interviews, offers | failed searches, missing CVs/descriptions, failed scoring, mature no-response applications, missing pipeline attribution | `workspace-jobzoom/data/jobzoom.db` plus `workspace/data/nasr-pipeline.db` |
| CMO | expected cadence, public metrics captured, unique published identifiers | saves, sends, qualified profile visits, relevant new followers, qualified inbound conversations | retractions, duplicate identifiers, over-cadence, missing outcome capture | `workspace-cmo/data/linkedin-metrics-manual-capture.csv` plus published-post logs |

Internal scores, file creation, command success, impressions, reactions, and likes are diagnostic evidence. They are not the final outcome.

## Fixed Adaptation Boundary

The shadow verifiers may recommend only one of these states:

- `repair-evidence`: fix missing or contradictory measurement before judging performance.
- `hold-baseline`: keep current behavior while the sample matures.
- `review-experiment-candidate`: evidence is sufficient to propose one controlled experiment for Ahmed's approval.
- `continue-baseline`: the system is healthy, but no change has earned approval.

They may never implement the recommendation automatically.

Any later experiment must:

1. Change one variable at a time.
2. Preserve approval, salary, eligibility, duplicate, privacy, budget, and publishing gates.
3. Define a primary outcome and failure counter-metric before starting.
4. Use a fixed evaluation window and minimum sample.
5. Roll back on a counter-metric breach.
6. Require Ahmed's approval before production promotion.

## Initial Evidence Thresholds

- JobZoom: at least 20 attributable applications and at least 80% career-pipeline matching before conversion evidence may support an experiment candidate.
- CMO: at least 8 posts in a named cohort, at least 70% outcome-field coverage, and no duplicate/retraction/cadence breach before format or cadence evidence may support an experiment candidate.
- Thresholds are governance defaults, not proof of statistical significance. Human judgment remains the final authority.

## Rollout State

Phase 1 is shadow-only. No cron or automated production adaptation is authorized. Review two or more real shadow reports before deciding whether a weekly read-only schedule is useful.
