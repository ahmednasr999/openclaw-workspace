# System Map

This is the shortest accurate map of how NASR's OpenClaw setup is shaped right now.

## 1. User-facing layer
- **Ahmed** primarily interacts through **Telegram DM**.
- Shared operational work also routes through Telegram group topics under `-1003882622947`.

## 2. Agent layer
- `main` = CEO / direct assistant / DM-facing agent
- `hr` = jobs, CVs, interviews
- `cto` = infra, scripts, gateway, maintenance
- `cmo` = content, LinkedIn, brand
- `jobzoom` = job scanning and matching lane

## 3. Routing layer
- Telegram DM `866838380` primarily lands in `main`
- Telegram topic `7` routes to `cmo`
- Telegram topic `8` routes to `cto`
- Telegram topic `9` routes to `hr`
- Telegram topic `5247` routes to `jobzoom`
- Topic `10` is the CEO General / main reporting lane

## 4. Model layer
- Active production default is `openai-codex/gpt-5.4`
- Thinking default is high
- Fast UX defaults are enabled where supported
- Session-level overrides are a known control surface and can override good global config

## 5. Heartbeat layer
- `main` heartbeats may go direct to Ahmed
- `hr`, `cto`, `cmo`, and `jobzoom` heartbeats are pinned to their topics with direct delivery blocked
- This is deliberate to stop routing drift

## 6. Execution layer
- Most scheduled jobs run as isolated `agentTurn` cron jobs
- Maintenance, reporting, and scans are distributed across `main`, `cto`, `cmo`, and job-search lanes
- Heavy recurring lanes are email monitoring, JobZoom scanning, maintenance sweeps, and content workflows

## 7. Knowledge layer

### Live source of truth
- `MEMORY.md`
- `TOOLS.md`
- `AGENTS.md`
- `/root/.openclaw/openclaw.json`
- scripts, cron registry, and agent session registries

### Human-readable knowledge layer
- `memory/wiki/`
- explains the system, links to canonical files, captures decisions and playbooks

## 8. Known risk surfaces
- stale session override state
- cron/session metadata drift
- gateway/service drift after updates
- noisy autonomous memory or skill-writing jobs
- transcript extraction / browser trust issues on VPS-hosted YouTube access

## 9. Operating principle
The system works best when:
- routing is explicit
- jobs are scoped
- expensive reasoning is intentional
- noisy success chatter is suppressed
- durable knowledge is curated instead of dumped

## 10. Best companion pages
- `Current-State.md`
- `../10-CORE/Model-Routing.md`
- `../10-CORE/Heartbeats-and-Routing.md`
- `../60-REFERENCE/Cron-Inventory.md`
- `../60-REFERENCE/Agents-and-Topics.md`
