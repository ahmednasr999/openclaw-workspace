---
name: governed-learning-loop
description: Capture verified workflow improvements as structured observations, combine repeated independent evidence into reviewable candidates, validate readiness, and stage explicit promotion requests without changing active skills. Use after a successful non-trivial workflow, repeated correction, verified solution, or when reviewing what should become a durable rule, script, test, or skill.
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

3. Validate a candidate before recommending it.

   ```bash
   python3 skills/governed-learning-loop/scripts/learning_loop.py validate --candidate glc-...
   ```

4. Request promotion only after Ahmed approves the exact candidate and target. This creates a receipt; it does not edit the target.

   ```bash
   python3 skills/governed-learning-loop/scripts/learning_loop.py request-promotion \
     --candidate glc-... \
     --target-path skills/example/SKILL.md \
     --approved-by "Ahmed Nasr" \
     --approval-ref "telegram-message-or-explicit-reference"
   ```

5. Implement the approved change as a separate task, run the target's tests, and record the result. Never treat `review` or `promotion-requested` as active.

## Gates

- Require a stable pattern key, concrete evidence, verification, source, and independent run ID.
- Deduplicate exact observations and candidates.
- Reject likely secrets and unsafe target paths.
- Keep generated artifacts under `data/learning-loop/` and `reports/learning-loop/`.
- Never mine raw sessions or hidden runtime context in v1.
- Never edit an active skill, core instruction, cron, runtime, credential, or external system.
- Prefer updating an existing rule or skill over creating a duplicate.
- Stop when evidence conflicts, verification is missing, or the requested target crosses another approval boundary.

Read [contract.md](references/contract.md) when reviewing readiness, schema, promotion receipts, or a policy exception.

