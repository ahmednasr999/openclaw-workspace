# Model Routing

## Intent
Use explicit routing by task, not expensive defaults by habit.

## Current production posture
- Primary agent model: `openai-codex/gpt-5.4`
- Subagents: `openai-codex/gpt-5.4`
- Default thinking: `high`
- Fast UX defaults: enabled where supported for main operational agents

## Important rules
- Do not silently revert Ahmed's explicit model choices.
- Cron jobs that matter operationally should declare their model explicitly.
- Historical MiniMax or other legacy model references may still exist in old records, but they are not acceptable in active production paths.

## Proven failure mode
Global router correctness is not enough. Session-level override state can still surface old model behavior.

## Debug order for model drift
1. Check live behavior.
2. Check active session registry entries.
3. Check cron payload model fields.
4. Check active scripts for direct model calls.
5. Only then assume global router drift.

## Current namespace decisions
- `gpt-5.4` stays on `openai-codex`.
- `gpt-5.4-pro` references should use direct `openai` namespace, not `openai-codex`.

## Related files
- `/root/.openclaw/openclaw.json`
- `/root/.openclaw/workspace/config/model-router.json`
- `../40-DECISIONS/2026-04-11-gateway-hardening.md`
