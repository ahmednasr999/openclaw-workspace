# GPT-5.6 Sol reasoning and tool policy

## Decision

- Keep `openai/gpt-5.6-sol` for every tier.
- Use `low` for deterministic wrappers whose judgment is owned by tested scripts.
- Use `medium` for research, classification, review, browser work, and bounded edits.
- Use `high` for executive synthesis and original content drafting.
- Do not enable experimental OpenClaw `tools.toolSearch` globally for Codex-harness runs. Codex already provides stable native code mode, deferred tool discovery, and nested tool calls.

## Programmatic tool use

Use native code/tool orchestration only when intermediate work is deterministic and bounded, such as filtering, ranking, deduplication, validation, aggregation, or parallel read-only retrieval. Return to model judgment before recommendations, approvals, public content, sensitive decisions, or external writes.

## Promotion gate

A lower reasoning tier may enter production only when:

1. the task has a deterministic output contract;
2. representative low and current-tier fixtures both pass;
3. the live workflow has one successful no-delivery or otherwise safe verification run;
4. model routing remains GPT-5.6 Sol;
5. rollback evidence exists.

If quality falls, restore the previous tier. Do not lower judgment-heavy workflows merely to reduce latency or token use.
