# Current State

Last seeded: 2026-04-11

## Platform state
- OpenClaw was upgraded to `2026.4.11`.
- Gateway service is running on `/usr/bin/node` against `/root/openclaw/dist/index.js`.
- Core routing and heartbeat configuration were validated after the update.

## Model state
- Primary production routing is `openai-codex/gpt-5.4`.
- `thinkingDefault` is high.
- Fast UX defaults were intentionally enabled for main operational agents.
- Session-level overrides remain a known source of drift and should be checked early when behavior looks wrong.

## Heartbeat state
- Main heartbeat may go direct to Ahmed.
- HR, CTO, CMO, and JobZoom heartbeats are intentionally pinned to their Telegram topics with direct delivery blocked.
- Config correctness was verified live. End-to-end delivery should still be checked separately when needed.

## Known open threads
- YouTube full transcript retrieval is still not reliably solved from the VPS.
- Cookie-assisted retry remains the next experiment.
- Proxy-backed browser extraction remains the likely reliable fallback.

## Active strategic build
- AI Ops Anomaly Sentinel v1 has a written spec and is a good candidate for careful implementation.

## First places to look when something feels off
- `TOOLS.md`
- `AGENTS.md`
- `memory/wiki/10-CORE/Model-Routing.md`
- `memory/wiki/10-CORE/Heartbeats-and-Routing.md`
- agent session registries under `~/.openclaw/agents/*/sessions/`
