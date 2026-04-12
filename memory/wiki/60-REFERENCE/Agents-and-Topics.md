# Agents and Topics

Generated from live config and workspace routing rules on 2026-04-11.

## Core agent map

| Agent | Role | Primary Telegram destination | Heartbeat direct policy |
|---|---|---|---|
| `main` | CEO / direct assistant | DM `866838380` | allow |
| `hr` | jobs, CVs, interviews | `-1003882622947:topic:9` | block |
| `cto` | infra, scripts, gateway | `-1003882622947:topic:8` | block |
| `cmo` | LinkedIn, content, brand | `-1003882622947:topic:7` | block |
| `jobzoom` | job scan/reporting lane | `-1003882622947:topic:5247` | block |

## Explicit live route bindings seen in config
- `hr` ← Telegram group peer `-1003882622947:topic:9`
- `cto` ← Telegram group peer `-1003882622947:topic:8`
- `cmo` ← Telegram group peer `-1003882622947:topic:7`
- `jobzoom` ← Telegram group peer `-1003882622947:topic:5247`

## Operational topic meanings
- **Topic 7**: CMO
- **Topic 8**: CTO
- **Topic 9**: HR
- **Topic 10**: CEO General / main operational reporting thread
- **Topic 5247**: JobZoom

## Heartbeat posture

### Main
- Model: `openai-codex/gpt-5.4`
- Direct heartbeat allowed
- Default heartbeat destination remains Ahmed DM

### HR
- Every 2h
- Active hours: `07:00-23:00` Cairo
- To: topic 9
- Direct blocked

### CTO
- Every 2h
- Active hours: `07:00-23:00` Cairo
- To: topic 8
- Direct blocked

### CMO
- Every 2h
- Active hours: `07:00-23:00` Cairo
- To: topic 7
- Direct blocked

### JobZoom
- Every 1d
- Active hours: `05:00-07:00` Cairo
- To: topic 5247
- Direct blocked

## Why direct policy matters
- `allow` means the heartbeat may go direct to Ahmed.
- `block` means the heartbeat must stay on its routed topic and should not drift into DM.

## Caution
When checking agent behavior, do not assume global defaults explain everything. Session-level override state can still distort what an agent actually does.

## Canonical companions
- `/root/.openclaw/workspace/AGENTS.md`
- `/root/.openclaw/workspace/memory/wiki/10-CORE/Heartbeats-and-Routing.md`
- `/root/.openclaw/openclaw.json`
