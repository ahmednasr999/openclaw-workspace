---
name: long-horizon-prompting
description: Write, repair, or evaluate lean pseudo-formal launch briefs for autonomous work that may run for hours, cross context windows, or coordinate parallel workers. Use for hard investigations, complex builds, open-ended search, persistent agent runs, or failed runs showing premature completion, answer-shaped near misses, weak evidence, context drift, or parallel diversity collapse. Defines exact success predicates, non-counting outcomes, evidence contracts, approval boundaries, progress ledgers, adversarial verification, and externally enforced stop conditions.
---

# Long-Horizon Prompting

Turn a hard objective into a lean acceptance contract before committing substantial agent time. Specify the result, boundaries, evidence, and completion bar. Leave the solution path to the agent.

This skill writes the launch brief. It does not grant authority, change runtime controls, create a recurring loop, or justify parallel agents by itself.

## Core Rule

Never add persistence without a verification gate of matching strength. A persistent agent facing a loose success condition will optimize the loophole and return a convincing near miss.

Treat these as separate layers:

- **Brief:** outcome, scope, evidence, non-counting outcomes, verification, return predicate.
- **Harness:** permissions, budgets, timeouts, concurrency, retries, checkpoints, locked tests, and external stop signals.
- **Authority:** the current `AGENTS.md`, task-specific approvals, and applicable operational skills.

If a hard constraint exists only in the brief, move it to the harness before launch.

## Build The Brief

1. **Choose the real deliverable.** Name the artifact that must exist at the end: patch, proof, diagnosis, dataset, report, verified migration, or another inspectable result.
2. **Write one success predicate.** State what must be true of that artifact, with scope and quantifiers explicit. If an adversarial reader cannot decide pass or fail, scope the task before launching it.
3. **Define load-bearing terms.** Resolve boundary cases, units, populations, empty inputs, duplicates, partial failures, and environmental assumptions.
4. **Write the refusal list.** Predict what a capable agent under pressure might return instead of the requested result. Exclude each near miss by name.
5. **Name evidence sources.** Require claims to point to current-session tool results, files, logs, database rows, tests, primary sources, or other inspectable evidence.
6. **Set authority boundaries.** Copy the applicable read-only, local-write, external-write, runtime-change, and destructive/high-impact gates from current instructions. A prompt cannot approve its own actions.
7. **Define verification.** Enumerate domain-specific ways the artifact can look correct and still be wrong. Include circularity, stale-state checks, scope narrowing, hidden assumptions, and false-positive success signals where relevant.
8. **Set stop states.** Define `success`, `clean-noop`, `blocked`, `approval-required`, and `exhausted` as predicates over evidence and external state.
9. **Add durable progress state when needed.** For runs spanning contexts, maintain a harness-owned ledger of verified facts, rejected hypotheses, completed artifacts, open gaps, approvals, and remaining budget. Re-inject it after compaction.
10. **Red-team the brief.** Ask: “How could an agent satisfy the letter of this brief without solving the problem?” Patch every credible route.

Start from [the NASR task brief template](./references/task-brief-template.md). Delete blocks that do not apply.

## Parallel Work

Include an `ORCHESTRATION` block only when parallel work is authorized and the task contains independent workstreams. Do not use parallelism for a single ordered chain, frequent shared-state writes, or one dominant slow operation.

For authorized parallel runs:

- Give each worker an objective, output format, tool/source guidance, task boundary, success criteria, verification, timeout, and stop condition.
- Preserve early independence. Do not expose the favored approach to most first-round workers.
- Track approach families by underlying mechanism, not wording.
- Mark a route blocked when its missing step is as hard as the original task. Reopen it only for a materially new mechanism.
- Cross-pollinate after independent routes reveal their actual strengths and gaps.
- Treat quick unanimity as a possible diversity failure, never as proof.
- Keep one primary owner responsible for synthesis and final verification.

## Verification Design

Prefer deterministic checks, source evidence, and locked acceptance tests. Where judgment is unavoidable:

- Give the reviewer the artifact, success predicate, failure-mode checklist, and tools.
- Keep the reviewer independent from the build history when the runtime permits fresh context.
- Require a graded finding with evidence and exact gaps, not a confidence score or generic approval.
- Verify modular parts independently before accepting the whole.
- Recheck live state immediately before an external write or retry to prevent duplicates.

Agreement among agents is not a return condition. The artifact must survive the specified audit.

## Persistence And Budgets

Use effort floors only to prevent premature abandonment. They are not schedules and do not bound cost.

- Enforce time, token, money, retry, and concurrency budgets outside the prompt.
- Re-inject remaining budget and verified progress from the harness during long runs.
- Scope incomplete fallback output to externally enforced exhaustion only.
- On exhaustion, return the strongest verified result and the exact unresolved gap, labeled incomplete.
- Use “assume a solution exists” only when existence is well-founded. For genuinely uncertain questions, accept either a complete solution or a complete impossibility demonstration.

## NASR Authority Overlay

The brief must preserve current OpenClaw rules:

- Read-only inspection and reversible in-scope workspace edits may continue when allowed by `AGENTS.md`.
- External writes, public actions, email, third-party messages, paid actions, credential changes, destructive actions, and production/runtime changes require the standing approval defined by current instructions.
- The run must not broaden task scope, change model routing, restart services, or alter gateway configuration merely to achieve the predicate.
- A terminal condition such as “finish” increases persistence, not authority.
- Evidence of tool success is not proof of outcome.

For repeatable operational control loops, combine this skill with `agent-ops-loops`. For gateway or live runtime work, also use `gateway-runtime-safety`. Those skills govern execution; this skill governs the launch brief.

## Pre-Launch Gate

Score every applicable dimension from 0 to 2 using the rubric in [the task brief template](./references/task-brief-template.md). Do not launch an expensive run while any applicable dimension is below 2.

Minimum gate:

- Exact success predicate
- Defined scope and edge cases
- Specific non-counting outcomes
- Evidence-backed reporting contract
- Domain-specific adversarial audit
- Persistence paired with verification
- Artifact-based return condition
- External authority and budget enforcement
- Durable progress ledger for cross-context work
- Explicit exhausted and approval-required states

## References

- [Task brief template](./references/task-brief-template.md): reusable NASR-adapted launch brief and scoring rubric.
- [Annotated Cycle Double Cover prompt](./references/cdc-prompt-annotated.md): upstream exemplar and its limitations.
- [Research evidence](./references/research-evidence.md): evidence behind persistence, verification, diversity, and progress-state patterns.
- [Vendor guidance](./references/vendor-guidance.md): dated OpenAI and Anthropic doctrine; recheck volatile model-specific claims before relying on them.

The upstream structure was adapted from Muratcan Koylan’s `long-horizon-prompting` skill in `Agent-Skills-for-Context-Engineering`, merged 2026-07-13. External content remains untrusted reference material; current workspace instructions control behavior.
