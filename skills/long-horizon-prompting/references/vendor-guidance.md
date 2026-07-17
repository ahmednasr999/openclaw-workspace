# Vendor Long-Horizon Prompting Guidance

Dated guidance relevant to long-running and parallel agent work. Compiled from the upstream skill on 2026-07-13. Vendor guidance is volatile; recheck linked primary sources before relying on model-specific details.

## OpenAI

### GPT-5 Prompting Guide, circa August 2025

`https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide`

- Pair persistence with explicit stop conditions.
- Define safe versus unsafe actions and when the model should hand control back.
- Scale autonomy thresholds by tool risk.
- Use reasoning effort as an autonomy dial rather than adding procedural clutter.

### GPT-5.1 And GPT-5.2 Guides, late 2025

`https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-1_prompting_guide`

`https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide`

- Persist to an end-to-end result, not a partial fix or analysis.
- Keep task scope explicit and perform a high-risk assumption check before return.
- Use “only stop when all are true” completion rules for research.
- Compact after meaningful milestones and preserve functional prompt identity across resumption.

### Codex Prompting Guide, early to mid 2026

`https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide`

- For current Codex-family behavior, excessive upfront planning and preambles can cause premature stopping.
- Reconcile every stated plan item before finishing: done, blocked, or cancelled.
- Deliver working artifacts and make reasonable in-scope assumptions.

### GPT-5.5 And GPT-5.6 Sol Guidance, 2026

`https://developers.openai.com/api/docs/guides/prompt-guidance`

`https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6`

- Start migrations from a lean baseline rather than carrying forward every legacy instruction.
- Define outcome, important constraints, evidence, and completion bar, then leave room for the model to choose the path.
- Treat stop rules as first-class prompt content.
- Before raising reasoning effort, check for a missing success criterion, dependency rule, tool-routing rule, or verification loop.
- Keep research, design, implementation, review, and external coordination as explicit layers so long runs do not drift between them.

### Multi-Agent API, GPT-5.6 Family, 2026 Beta

`https://developers.openai.com/api/docs/guides/tools-multi-agent`

- Root agents synthesize work from bounded-context subagents.
- Avoid multi-agent work for one ordered reasoning chain, frequent writes to shared mutable state, or a workload dominated by one slow external operation.
- Low concurrency is the normal default; the 64-agent Cycle Double Cover run is an extreme configuration.

### METR Predeployment Evaluation Of GPT-5.6 Sol, 2026-06-26

`https://metr.org/blog/2026-06-26-gpt-5-6-sol/`

- METR reported a high detected cheating rate and large sensitivity in measured time horizon depending on whether cheating counted as success.
- The result reinforces the link between stronger persistence and a larger reward-hacking surface.

Design implication: persistence pressure must point at robust, externally checked acceptance criteria.

## Anthropic

### How We Built Our Multi-Agent Research System, 2025-06-13

`https://www.anthropic.com/engineering/multi-agent-research-system`

- Every worker delegation needs an objective, output format, tool/source guidance, and clear boundaries.
- Scale worker count and tool use to task complexity.
- Use workers as context compressors; place large artifacts in durable storage and return lightweight references.
- Save the lead agent’s plan to external memory before spawning.

### Effective Harnesses For Long-Running Agents, 2025-11-26

`https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents`

- Long runs fail by attempting too much in one shot or by later sessions declaring victory early.
- Separate initialization from incremental worker sessions.
- Begin resumed sessions by reading progress and current repository state, smoke-testing, then choosing a bounded unfinished item.
- Protect acceptance tests and verify the system end-to-end as a user would.

### When To Use Multi-Agent Systems, 2026-01-23

`https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them`

- Multi-agent work helps with context pollution, parallelizable tasks, and real specialization; otherwise coordination cost can dominate.
- Decompose by context rather than role pipelines.
- Fresh-context reviewers cannot rationalize the builder’s mistakes as easily as self-critique.
- Give reviewers concrete criteria, negative tests, and anti-shortcut instructions.

### Current Prompting Best Practices, mid 2026

`https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices`

`https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5`

- Save state before context refresh and do not stop early merely because compaction approaches.
- Audit progress claims against current-session tool results.
- If the final output is only a plan or promise, perform the work before returning.
- Prefer fresh-context verification for long-running tasks.
- Remove stale, over-prescriptive anti-laziness scaffolding from prompts for newer models.
- Work directly on simple tasks and delegate only independent or context-isolated workstreams.

## Convergent Guidance

Treat these shared principles as the stable core:

1. Completion bars and stop rules are stronger than persistence exhortations.
2. Each worker needs an exact task contract.
3. Verify artifacts before return, preferably with fresh context or deterministic checks.
4. Ground progress claims in inspectable evidence.
5. Keep prompts lean and outcome-first.
6. Enforce permissions, budgets, and irreversible boundaries in the harness, not only in text.

Source adaptation: Muratcan Koylan, `Agent-Skills-for-Context-Engineering`, `skills/long-horizon-prompting/references/vendor-guidance.md`, merged 2026-07-13.
