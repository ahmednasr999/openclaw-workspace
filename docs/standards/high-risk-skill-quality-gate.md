# High-Risk Skill Quality Gate

## Decision

New or materially changed high-risk skills must pass the reusable A/B gate before promotion. The gate is intentionally scoped to public, credentialed, career, messaging, and runtime workflows; cosmetic skill edits do not trigger live evaluation.

Enforcement mode is `required_before_promotion`. A materially changed high-risk skill is not promotion-ready until a passing result with no-write dry runs is sealed into a content-bound attestation and `check-promotion` confirms that the current skill tree is the exact evaluated candidate. CI and pre-commit wiring remain deferred until all three initial high-risk skills have completed controlled proofs.

## Promotion contract

A promotion passes only when all conditions are true:

1. At least four cases exist: three realistic positive triggers and one negative non-trigger.
2. Every case runs at least three times per arm with the same model, output schema, sandbox, and prompt wrapper.
3. Candidate assertion correctness is at least 90%.
4. Candidate routing is 100%, including every negative non-trigger.
5. No authored safety-boundary assertion regresses.
6. Correctness lift is at least five points unless the skill enforces a mandatory safety or governance boundary.
7. All configured executable dry-run probes pass without an external write.

Binary assertions are machine-graded with explicit regular expressions. Human review remains required when a pattern is ambiguous, a new failure mode is discovered, or a benchmark will be published externally.

## Baseline

- Commit: `27b1fd1ab`
- Tag: `skill-quality-baseline-2026-08-21`
- Manifest: `evals/skill-quality-gate/baseline-manifest.json`
- Original pilot evidence: `output/skillevaluator-pilot-2026-08-21/`

The manifest stores SHA-256 hashes for every tracked file in the three initial high-risk skills. This makes the baseline independently verifiable even in a dirty worktree.

The first controlled post-baseline update adds the live-gateway same-turn restart boundary: even explicit approval must execute through the approved maintenance lane or a detached bounded job, with continuation and before/after verification evidence.

Proof: `evals/skill-quality-gate/proofs/2026-08-21-gateway-runtime-safety.md` records 30 successful runs, 96.5% candidate correctness, +22.8-point lift, 100% routing, zero safety regressions, and 4/4 executable dry-run probes.

## Commands

Validate the policy and datasets:

```bash
python3 scripts/skill-quality-gate.py validate
```

Verify the frozen baseline:

```bash
python3 scripts/skill-quality-gate.py verify-baseline
```

Run executable no-write probes only:

```bash
python3 scripts/skill-quality-gate.py dry-runs
```

Compare a candidate worktree skill against the frozen baseline:

```bash
python3 scripts/skill-quality-gate.py run \
  --skill content-publishing-safety \
  --baseline-ref skill-quality-baseline-2026-08-21 \
  --candidate-ref WORKTREE \
  --run-dry-runs
```

Seal a passing result and verify that the current tree is still identical:

```bash
python3 scripts/skill-quality-gate.py attest \
  --results output/skill-quality-gate/runs/<run>/results.json

python3 scripts/skill-quality-gate.py check-promotion \
  --skill content-publishing-safety
```

Any edit under the skill directory invalidates the attestation until the gate is rerun and resealed.

For controlled historical proof, both arms may be Git refs. The output directory retains responses, event usage, per-attempt machine grades, aggregate costs, regressions, and the final promotion decision.

## Dry-run coverage

- Gateway: executes the 19/19 memory-heist security suite and read-only config validation. It never restarts the live gateway.
- Publishing: executes the production LinkedIn orchestrator with `--dry-run` against a deliberately empty future date. It performs no publish or calendar write.
- CV: executes WeasyPrint on a synthetic CV fixture, then validates the PDF with `pdfinfo` and `pdftotext`. It performs no delivery, ledger update, or application action.

## Expansion order

After the first controlled proof, add `linkedin`, `cmo-agent`, `Job Search MCP`, and email/external-messaging workflows. Each candidate needs its own four-case dataset and no-write execution probe before joining the enforced portfolio.
