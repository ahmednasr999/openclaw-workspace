# Governed Product Learning Pilot - 2026-08-19

## Decision

Adopt the useful part of the self-learning-app pattern as a shadow-only evidence bridge. Do not allow analytics, an AI agent, or generated learning material to change an OpenClaw workflow automatically.

## Control Flow

`aggregated evidence -> one friction lesson -> one bounded intervention -> fixed measurement window -> success | inconclusive | rollback-required | insufficient-evidence -> existing governed learning registry`

The bridge is `scripts/governed-product-learning.py`. It complements, rather than replaces, `skills/governed-learning-loop/scripts/learning_loop.py`.

## Boundaries

- Input must be aggregated, sanitized, and explicitly PII-free.
- Analysis selects one adequately sampled friction point using a locked dropoff/error formula.
- Every step classifies exits as `friction` or `intentional-filter`; intentional editorial filtering is recorded but excluded from the drop-off score.
- The selected output is an unknown to investigate, not a fabricated root cause.
- Each experiment changes exactly one named variable.
- A primary metric, at least one guardrail, minimum sample, fixed window, and rollback action are locked before evaluation.
- Every experiment locks an explicit paired control/treatment or matched pre/post comparator. Evaluation uses measured comparator values, not an unpaired baseline change.
- Production mode remains `approval-required` until explicit text approval is attached to the exact experiment.
- The bridge never executes, deploys, schedules, promotes, or rewrites a workflow.
- Only a measured `success` is eligible to become an observation in the existing governed learning registry. It still needs independent evidence, replay evaluation, exact promotion approval, separate implementation, and verification.
- `inconclusive` is a valid terminal state. Guardrail failure returns `rollback-required`.

## Data Sources

Preferred live source: an aggregated PostHog export or equivalent workflow telemetry. Session content, prompts, credentials, personal data, and raw transcripts are out of scope.

The PostHog connector was suggested during setup but was not installed in this turn. Until a live aggregated snapshot is available, the pilot is control-verified but not production-evidence-verified.

## Usage

1. Copy `templates/workflows/governed-product-learning-snapshot.json`, replace it with an aggregated real snapshot, and analyze it:

   ```bash
   python3 scripts/governed-product-learning.py analyze \
     --snapshot reports/product-learning/snapshot.json \
     --output reports/product-learning/lesson.json
   ```

2. Copy `templates/workflows/governed-product-learning-experiment.json`, bind it to the lesson ID, lock one change and its metrics, then stage it:

   ```bash
   python3 scripts/governed-product-learning.py stage \
     --lesson reports/product-learning/lesson.json \
     --spec reports/product-learning/experiment-spec.json \
     --output reports/product-learning/staged-experiment.json
   ```

3. Execute only within the authority stated by the staged record. Measure externally, bind the result to the staged-file SHA-256, and evaluate:

   ```bash
   python3 scripts/governed-product-learning.py evaluate \
     --stage reports/product-learning/staged-experiment.json \
     --result reports/product-learning/result.json \
     --output reports/product-learning/outcome.json
   ```

4. If and only if the outcome is `success`, capture it with a distinct run ID and concrete evidence in the existing governed learning registry. Do not promote from one run.

## Verification State

- Control fixture only: synthetic and explicitly not evidence of user behavior.
- Live evidence: pending an aggregated PostHog or equivalent snapshot.
- Production workflow mutation: none.
- Cron/runtime/external changes: none.

## First Shadow Trial

- Workflow: Daily Executive Intelligence.
- Source: retained local aggregated collector data only; no PostHog connection and no raw prompts, messages, or personal data.
- Control: replay the frozen candidate pool through the current ranking and balance gates.
- Treatment: replay the same pool after requiring corroboration from two credible, distinct source domains.
- Primary metric: share of selected actionable signals supported by two credible sources.
- Guardrails: processing latency, source diversity, candidate coverage, and a deterministic false-positive proxy.
- Window: seven days with at least 50 paired candidate signals.
- Delivery: shadow artifacts only under `reports/product-learning/daily-executive-intelligence/`; the live brief, cron, configuration, and publishing state remain unchanged.
