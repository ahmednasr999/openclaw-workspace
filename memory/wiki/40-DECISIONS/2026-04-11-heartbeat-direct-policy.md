# Decision: Block Direct Heartbeats for Routed Subagents

Date: 2026-04-11

## Context
Heartbeat routing needed to remain stable after config cleanup and upgrades. The main risk was silent drift, where routed agent heartbeats could land in the wrong direct chat instead of their intended Telegram topics.

## Decision
- Keep `main` heartbeat direct policy as `allow`.
- Set `hr`, `cto`, `cmo`, and `jobzoom` heartbeat direct policy to `block`.
- Keep those subagent heartbeats explicitly targeted to their assigned Telegram topics.

## Why
- `main` is the direct assistant lane and should be able to reach Ahmed directly.
- Routed subagents should stay inside their operational topics.
- Explicit policy is safer than relying on implied routing behavior.

## Consequences
- Heartbeat checks now have clearer expectations by agent.
- If a subagent heartbeat appears in DM, it should be treated as drift or misconfiguration.
- When answering whether heartbeats are OK, config correctness still must be separated from actual observed delivery.

## Related files
- `/root/.openclaw/openclaw.json`
- `/root/.openclaw/workspace/memory/wiki/10-CORE/Heartbeats-and-Routing.md`
- `/root/.openclaw/workspace/memory/wiki/60-REFERENCE/Agents-and-Topics.md`
