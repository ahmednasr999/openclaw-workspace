# Decision: Standardize Active Production Routing on GPT-5.4

Date: 2026-04-11

## Context
There was confusion about why some agents still appeared to be using MiniMax or other older models even after the global router had already been moved to GPT-5.4. Investigation showed that current router policy was not the only control surface.

## Decision
- Standardize active production routing on `openai-codex/gpt-5.4`.
- Explicitly pin important cron jobs to GPT-5.4.
- Remove direct MiniMax runtime calls from active scripts.
- Treat session-level override state as part of model routing, not as a side detail.
- Keep `gpt-5.4-pro` on direct `openai` namespace rather than under `openai-codex`.

## Why
- Router correctness alone was not enough.
- Active sessions could still carry stale model/provider override state.
- Explicit pinning reduces ambiguity in long-lived operational paths.
- Native Codex transport should stay clean and purpose-specific.

## Consequences
- Model debugging should inspect active session registries early.
- Old historical records may still mention legacy models without representing current production behavior.
- Cron jobs and active scripts are now expected to declare or inherit GPT-5.4 intentionally, not accidentally.

## Related files
- `/root/.openclaw/openclaw.json`
- `/root/.openclaw/workspace/config/model-router.json`
- `/root/.openclaw/workspace/memory/wiki/10-CORE/Model-Routing.md`
