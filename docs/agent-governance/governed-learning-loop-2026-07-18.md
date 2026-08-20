# Governed Learning Loop

## Decision

Adopt a staged organizational learning loop in local shadow mode:

`verified workflow -> structured observation -> repeated-evidence candidate -> bounded proposal -> baseline/candidate replay -> explicit promotion request -> separate implementation and verification`

The loop does not autonomously execute or edit candidates, active skills, prompts, core instructions, runtime jobs, credentials, or external systems.

## Why this design

The workspace already captures daily lessons and has automation that can suggest or directly append skill improvements. What was missing was a durable boundary between evidence and active behavior. The governed loop makes that boundary explicit and auditable.

The loop uses explicit structured observations and curated sanitized replay suites instead of raw transcript mining. That reduces prompt-injection, privacy, hidden-context, false-success, and credential leakage risks. Candidate quality is measured against a hashed suite without granting execution or promotion authority to the registry.

## Gates

| Stage | Required evidence | Write boundary |
|---|---|---|
| Observation | stable pattern key, independent run ID, source, evidence, verification | registry only |
| Candidate | 2+ observations, 2+ runs, 2+ evidence sets, consistent target type | registry and report only |
| Validation | candidate still matches current registry and passes all gates | none |
| Proposal | 1-4 edits, target, exact baseline/candidate artifact and configuration hashes, suite hash, curated validation and locked tasks | registry only |
| Replay | packet-bound baseline/candidate artifact and configuration hashes, 2+ independent runs, minimum improvement, zero critical regression, locked-test and cost gates | evaluation and negative-evidence records only |
| Promotion request | accepted proposal, exact target/evaluation/hash set, signed approval receipt from a pinned approver principal | receipt only |
| Implementation | separate scoped task and target-specific tests | approved target only |
| Verification | real behavior or artifact check plus rollback evidence | implementation receipt only |

## Operating rules

- Capture methods that prevent failure or measurably improve repeat execution, not routine task summaries.
- Prefer updating an existing owner artifact over creating a second source of truth.
- Treat recurrence as necessary but insufficient. Human judgment still checks generality, side effects, and ownership.
- Test the same bounded candidate against both baseline and candidate configurations; do not weaken the locked suite after seeing results.
- Require every independent run to clear the improvement threshold and reject any critical-task regression.
- Keep proposal cost within both the absolute ceiling and relative baseline ratio.
- Retain rejected evaluations as negative evidence even if a later revision passes.
- Keep promotion separate from candidate discovery.
- Fail closed unless the approval receipt verifies against the external operator-managed OpenSSH allowed-signers trust root at `/root/.config/openclaw/governed-learning-approval-signers`; caller-supplied approver text is not approval evidence.
- Add scheduling only after multiple manual samples are useful and low-noise.
- Do not feed raw session transcripts, hidden runtime instructions, credentials, or personal data into the registry.

## Ownership and artifacts

- Owner: NASR/main.
- Skill: `skills/governed-learning-loop/`.
- Registry: `data/learning-loop/registry.json`.
- Report: `reports/learning-loop/latest.md`.
- Tests: `tests/test_governed_learning_loop.py`.
- Weekly build: existing Saturday scheduler job, converted to a deterministic local command with silent success delivery.
- Promotion remains an explicit, separately verified task.

## Initial success criteria

1. Two independently verified observations produce exactly one reviewable candidate.
2. Replaying capture and build is idempotent.
3. Candidate validation passes only with distinct runs and evidence.
4. A promotion request records a receipt but leaves the target untouched.
5. A bounded shadow proposal passes two independent replay runs with no critical regression and zero automatic deployment.
6. Skill validation and focused tests pass.

## Deferred work

- Model-assisted session extraction or raw-transcript mining.
- Automatic draft generation in an isolated sandbox.
- Model-assisted scheduled observation capture.
- Branchable remote workspaces.
- Credential brokering beyond current OpenClaw controls.
