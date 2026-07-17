# The Cycle Double Cover Prompt, Annotated

Status and provenance as of 2026-07-13:

- OpenAI published a candidate proof of the Cycle Double Cover Conjecture on 2026-07-10 together with the full GPT-5.6 Sol Ultra prompt.
- Prompt: `https://cdn.openai.com/pdf/04d1d1e4-bc75-476a-97cf-49055cd98d31/cdc_prompt.pdf`
- Candidate proof: `https://cdn.openai.com/pdf/04d1d1e4-bc75-476a-97cf-49055cd98d31/cdc_proof.pdf`
- The run reportedly used up to 64 concurrent agents and completed in under one hour, below the prompt’s eight-hour effort floor.
- At publication, the candidate had no independent peer review, formalization in Lean or Coq, or arXiv posting. Treat the prompt structure as the useful artifact and the mathematical claim as unverified.
- No public ablation isolates which prompt elements contributed to the candidate.

## 1. Definitions

The prompt defines graph, bridge, cycle, and cycle double cover before stating the task. It explicitly settles parallel edges, two-edge cycles, and multiplicity. These definitions close loopholes rather than teach the domain.

General pattern: define every load-bearing term and the degenerate cases a solver might exploit.

## 2. Exact Success Predicate

The prompt requires a complete proof for every finite bridgeless loopless multigraph and explicitly forbids narrowing assumptions such as cubicity, planarity, connectivity, or higher edge-connectivity. It also settles disconnected and edgeless cases.

General pattern: state the predicate with full scope, then name the attractive special cases that do not satisfy it.

## 3. Non-Counting Outcomes

The prompt rejects:

- proofs for special graph classes
- covers where edges occur other than exactly twice
- bounded-length or prescribed-cycle variants
- reductions to another unproved conjecture
- verification through any fixed graph size
- counterexamples without a complete nonexistence certificate

General pattern: predict the answer-shaped near misses the domain invites and exclude them by name.

## 4. Orchestration Policy

The prompt uses heuristics instead of fixed worker quotas:

- start with substantially different formulations and invariants
- keep most early workers blind to the favored route
- maintain a registry keyed by mathematical idea, not wording
- treat a reduction to an equally hard lemma as no progress
- mark theorem-strength gaps blocked and reopen them only for a materially new mechanism
- keep incompatible routes alive and cross-pollinate late

General pattern: engineer structural diversity and preserve rejected-route evidence.

## 5. Verification And Reporting

Auditors receive a specific failure-mode list: exact-two multiplicity, repeated-edge trails masquerading as cycles, parallel-edge two-cycles, disconnected graphs, cutvertices, bridges introduced by reductions, and circular use of an equivalent statement.

Workers must return concrete lemmas, constructions, equations, or counterexamples. Status reports, vague optimism, and claims that a global compatibility step is “routine” are rejected.

General pattern: replace “check the work” with a domain-specific hunt list and artifact contract.

## 6. Return Condition And Effort Floor

The root repeatedly synthesizes, challenges, redirects, and launches new rounds. A successful return requires a complete artifact that survives adversarial audit. The effort floor removes permission to quit early but does not set a schedule or cost ceiling.

The published prompt contains a tension: it allows the strongest rigorous partial derivation if no proof is found, then later forbids partial returns. A cleaner brief permits incomplete output only when an externally enforced budget is exhausted.

## 7. Contamination Guard

Public search is limited to ordinary background and named theorems, not the exact conjecture or benchmark solution.

General pattern: define retrieval scope whenever the result must remain independent of existing answers.

## Negative Space

The prompt contains no fixed personas, detailed proof method, emotional pressure, or prompt-only cost control. It specifies acceptance and search discipline while leaving the route open.

Source adaptation: Muratcan Koylan, `Agent-Skills-for-Context-Engineering`, `skills/long-horizon-prompting/references/cdc-prompt-annotated.md`, merged 2026-07-13.
