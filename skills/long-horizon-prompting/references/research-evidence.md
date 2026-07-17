# Research Evidence For Long-Horizon Briefs

Compiled from the upstream skill on 2026-07-13. Treat 2026 preprints as unreviewed and recheck primary sources before making consequential or model-specific claims.

## Give-Up Drift And Premature Termination

- **Diagnosing and Mitigating Context Rot in Long-horizon Search** (arXiv 2606.29718, June 2026): accumulated trajectory content shifts failures toward uncertainty and giving up. Summarization is preferable to blind truncation.
- **Push Your Agent / PushBench** (arXiv 2605.23574, May 2026): agents often make plausible local progress but stop before quantity or completion is verified. Externally maintained verified-progress ledgers materially outperformed prompt-only controllers in the reported experiments.
- **BudgetThinker** (arXiv 2508.17196, August 2025): a budget stated once decays in influence; periodic remaining-budget reminders improve adherence.
- **METR time-horizon work** (arXiv 2503.14499 and Time Horizon 1.1): longer useful horizons come largely from reliability and recovery, supporting checkpoints and externally verified progress.

Implication: use artifact-based stop conditions, harness-owned progress state, and budget re-injection. Do not rely on persistence wording alone.

## Verification Bottleneck

- **Large Language Monkeys** (arXiv 2407.21787): any-sample success scales with sample count, but selectors plateau where verification is weak.
- **Benchmark Test-Time Scaling of General LLM Agents** (arXiv 2602.18998): pass@K can rise while self-selection accuracy lags or falls.
- **QEDBench** (arXiv 2602.20629): frontier judges of proofs can reward rigorous-looking but incomplete work; generic checking instructions are insufficient.
- **Pseudo-Formalization for Automatic Proof Verification** (arXiv 2605.20531): locally self-contained modules improve error finding versus whole-artifact judging.
- **ProofBench / ProofGrader** (arXiv 2510.13888): rubrics and graded evaluation improve selection relative to binary verdicts.
- **Prover-Verifier Games** (arXiv 2407.13692 and successors): correctness optimization and checkability are separate; adversarial verification and legible artifacts complement each other.

Implication: invest in candidate selection, enumerate failure modes, modularize artifacts, and prefer deterministic or primary-source checks.

## Diversity Collapse

- **Diversity Collapse in Multi-Agent LLM Systems** (arXiv 2604.18005): dense communication and authority hierarchies can accelerate premature convergence.
- **Representational Collapse in Multi-Agent LLM Committees** (arXiv 2604.03809): agreement can tighten on harder problems and reflect shared bias rather than corroboration.
- **ParaThinker** (arXiv 2509.04475) and **OPE** (arXiv 2602.08344): parallel width and explicit solution-space partitioning can reduce sequential tunnel vision.
- **Scaling Test-time Compute for LLM Agents** (arXiv 2506.12928): selection method matters; reflection is more useful when triggered by evidence than by fixed cadence.

Implication: preserve early independence, organize routes by mechanism, treat fast consensus as a warning, and cross-pollinate late.

## Orchestration And Durable State

- **AOrchestra** (arXiv 2602.03786): dynamic per-task worker specifications outperformed static roles in the reported benchmarks.
- **DeLM** (arXiv 2606.10662): shared verified context containing findings, failures, and falsified hypotheses reduces repeated dead ends.
- **RL for LLM-based Multi-Agent Systems through Orchestration Traces** (arXiv 2605.02801): the survey found stopping decisions remained prompt and harness territory.

Implication: every worker needs an explicit task contract; blocked routes and rejected hypotheses belong in durable shared state; return predicates are load-bearing.

## Frontier Open-Problem Record

Generation claims become results only through external verification. Recent examples include collapsed claims that rediscovered existing literature, human-repaired proof sketches, formally checked components, and the still-unverified Cycle Double Cover candidate.

Implication: the launch brief should produce modular, checkable candidates for a separate verification pipeline. It should not treat plausibility, novelty, or multi-agent agreement as proof.

## Evidence-To-Design Mapping

| Brief element | Supporting evidence |
| --- | --- |
| Solvability framing and effort floor | Context-rot and premature-stopping work |
| Artifact-based return predicate | PushBench and stopping-gap surveys |
| Domain-specific adversarial audit | QEDBench, pseudo-formal verification, ProofBench |
| Early independence and late cross-pollination | Diversity and representational-collapse studies |
| Durable approach registry and blocked routes | DeLM shared falsified-hypothesis state |
| Per-worker task contracts | AOrchestra and vendor delegation guidance |
| External progress and budget state | PushBench and BudgetThinker |
| Verification investment | Selector-plateau and test-time-scaling studies |

Source adaptation: Muratcan Koylan, `Agent-Skills-for-Context-Engineering`, `skills/long-horizon-prompting/references/research-evidence.md`, merged 2026-07-13.
