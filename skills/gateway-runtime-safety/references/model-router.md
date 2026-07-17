# Model Router Notes

Ahmed's current default model is GPT-5.6 Sol via OpenAI Codex OAuth unless he changes it. Never silently revert his explicit model choice.

## Model-sensitive work

Use `session_status` for current session model and quota state. Disclose any model switch immediately.

## Places model leaks or overrides can persist

1. Global `config/model-router.json`.
2. Agent-local `workspace-*/config/model-router.json`.
3. `/root/.openclaw/agents/*/sessions/sessions.json`.
4. Channel/group/topic overrides such as `channels.modelByChannel.telegram`.
5. Current topic session after `/reset`.

## Recommended diagnosis flow

1. Use `session_status` for current active model.
2. Inspect relevant router config only if needed.
3. If config changes are needed, use gateway schema/config tools first.
4. Verify the actual session after change.

## Do not

- Do not silently switch away from GPT-5.6 Sol.
- Do not use retired MiniMax unless Ahmed explicitly asks.
- Do not assume a model change in one place updated all agent/topic overrides.
