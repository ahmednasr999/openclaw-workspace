# Gateway Failure Modes

## Common patterns

- Schema mismatch after version changes.
- Runtime patch checker timeout with otherwise healthy gateway.
- Model override stuck in agent/session/channel config.
- Tool approval prompts caused by command shape, not domain policy.
- External service failures that look like local bugs, for example Tavily 401/402.
- Restart succeeds but original behavior remains broken.
- Telegram DM is processed internally and session logs show assistant text, but no visible DM reply is sent. Check `messages.visibleReplies = automatic`; for group/topic agents, check `messages.groupChat.visibleReplies = automatic` because `message_tool` can suppress visible final replies.
- After OpenClaw updates, Telegram can fail before model execution if Docker sandbox image `openclaw-sandbox:bookworm-slim` is missing. Rebuild it from `/usr/lib/node_modules/openclaw/docs/gateway/sandboxing.md`.

## Response pattern

1. Identify source of truth.
2. Separate local bug, external service issue, policy boundary, and transient timeout.
3. Use the smallest safe verification step.
4. Change one thing at a time.
5. Verify actual behavior before closeout.

## Reporting

Closeout must include:

- What changed or what was diagnosed.
- Evidence.
- Remaining risk.
- Whether Ahmed needs to act.
