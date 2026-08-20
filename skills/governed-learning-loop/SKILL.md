---
name: governed-learning-loop
description: Capture verified workflow improvements, combine independent evidence into candidates, and gate bounded proposals with baseline-versus-candidate replay, locked tests, regression and cost limits, retained negative evidence, and explicit promotion approval. Use after a successful non-trivial workflow, repeated correction, verified solution, skill optimization, or any request to turn learning into an active rule, script, test, solution, or skill change.
---

# Governed Learning Loop

Turn proven work into reusable organizational capability while keeping active behavior human-governed.

## Workflow

1. Capture only a verified, reusable method. Do not capture routine completion, unverified advice, raw transcript text, credentials, or personal data.

   ```bash
   python3 skills/governed-learning-loop/scripts/learning_loop.py capture \
     --pattern-key workflow.example \
     --summary "Describe the reusable method and the failure it prevents." \
     --run-id "stable-independent-run-id" \
     --source "memory/YYYY-MM-DD.md" \
     --evidence "path/to/artifact-or-report" \
     --verification "Exact check and grounded result" \
     --target-type skill-update
   ```

2. Build candidates. A candidate needs at least two observations from distinct runs with distinct evidence.

   ```bash
   python3 skills/governed-learning-loop/scripts/learning_loop.py build
   ```

3. Validate a candidate before drafting an implementation.

   ```bash
   python3 skills/governed-learning-loop/scripts/learning_loop.py validate --candidate glc-...
   ```

4. Prepare a bounded proposal with one to four edits. Lock the exact baseline artifact/configuration, candidate artifact/configuration, and a curated, sanitized suite containing separate `validation` and `locked-test` tasks. Every suite needs at least two independent runs, a minimum improvement threshold, a candidate cost ceiling, a cost-increase ratio, and at least one critical task.

   ```bash
   python3 skills/governed-learning-loop/scripts/learning_loop.py create-proposal \
     --candidate glc-... \
     --target-path skills/example/SKILL.md \
     --baseline-artifact reports/learning-loop/baselines/example.md \
     --baseline-config reports/learning-loop/baselines/example-config.json \
     --artifact skills/example/SKILL.md \
     --candidate-config reports/learning-loop/candidates/example-config.json \
     --suite skills/example/evals/replay-suite.json \
     --edit "Add the first bounded change." \
     --edit "Add the second bounded change."
   ```

5. Replay the same tasks against those exact locked baseline and candidate artifacts/configurations outside this registry script. Copy all four proposal hashes plus the suite hash into the result packet, record scores and costs for every task in every run, then apply the gates. An accepted result requires exact hash matches, the threshold in every run, no locked-test regression, zero regression on critical tasks, and all cost limits to pass.

   ```bash
   python3 skills/governed-learning-loop/scripts/learning_loop.py evaluate-proposal \
     --proposal glv-... \
     --results reports/learning-loop/evaluations/glv-....json
   ```

   A rejection remains in `negative_evidence`; do not delete it or silently retry with easier tasks.

6. Request promotion only after the proposal passes replay and Ahmed approves the exact proposal, accepted evaluation, target, and replay hash set. The approval workflow must create a JSON receipt and sign its unchanged bytes with an OpenSSH key whose principal is pinned in `config/governed-learning-approval-signers`. The private key stays outside this skill. This creates a promotion receipt; it does not edit the target.

   ```bash
   python3 skills/governed-learning-loop/scripts/learning_loop.py request-promotion \
     --proposal glv-... \
     --target-path skills/example/SKILL.md \
     --approval-receipt reports/learning-loop/approvals/glv-....json \
     --approval-signature reports/learning-loop/approvals/glv-....json.sig
   ```

7. Implement the approved change as a separate task, run the target's tests, inspect real behavior, and record verification plus rollback evidence.

   ```bash
   python3 skills/governed-learning-loop/scripts/learning_loop.py record-implementation \
     --promotion-request glp-... \
     --verification "Focused and regression checks passed; real artifact inspected." \
     --rollback "Restore the approved target from the recorded baseline snapshot."
   ```

Never treat `review`, `evaluation-pending`, `evaluation-passed`, or `promotion-requested` as active behavior.

## Gates

- Require a stable pattern key, concrete evidence, verification, source, and independent run ID.
- Deduplicate exact observations and candidates.
- Limit each proposal to one to four explicit edits.
- Bind evaluation to exact baseline/candidate artifact and configuration hashes, the curated suite hash, and the result packet hash.
- Accept promotion only from a signed, artifact-bound approval receipt verified against the fixed operator trust root.
- Require repeated independent runs and separate validation and locked-test splits.
- Enforce minimum improvement, zero critical regression, and bounded candidate cost.
- Retain rejected evaluations as negative evidence.
- Reject likely secrets and unsafe target paths.
- Keep generated artifacts under `data/learning-loop/` and `reports/learning-loop/`.
- Never mine raw sessions or hidden runtime context.
- Never deploy, edit, or execute the candidate through the registry script.
- Prefer updating an existing rule or skill over creating a duplicate.
- Stop when evidence conflicts, verification is missing, or the requested target crosses another approval boundary.

Read [contract.md](references/contract.md) when preparing evaluation packets, reviewing readiness, recording promotion or implementation receipts, or considering a policy exception.
