# OpenClaw Docs Map and Feature Activation Rules

Last reviewed: 2026-04-26
Source entry points:
- https://docs.openclaw.ai/start/hubs
- https://docs.openclaw.ai/llms.txt

## Why this exists

Use the docs hub and `llms.txt` before changing OpenClaw features. The hub is the curated map. `llms.txt` is the complete machine-readable index and exposes pages that do not always appear in the sidebar.

Current observed index size: 431 docs pages.

## Fast rule

Before enabling, disabling, or reconfiguring an OpenClaw feature:
1. Check `/start/hubs` for the official area.
2. Check `llms.txt` for the exact page.
3. Read the feature page plus its troubleshooting/security page when present.
4. Compare docs to live config and runtime state.
5. Change the smallest safe thing.
6. Validate config, restart only if required, then verify the actual feature works.

## High-value docs areas

| Area | Key docs | Use when |
|---|---|---|
| Browser | `/tools/browser`, `/tools/browser-control`, `/tools/browser-login`, `/tools/browser-linux-troubleshooting` | Browser plugin, profiles, node proxy, login flows, CDP issues |
| Nodes | `/nodes`, `/nodes/audio`, `/nodes/camera`, `/nodes/talk`, `/nodes/voicewake` | Mac/local capability routing, media, voice wake, talk mode |
| Voice calls | `/plugins/voice-call`, `/cli/voicecall` | Telephony, inbound/outbound calls, realtime voice |
| Automation | `/automation/cron-jobs`, `/automation/standing-orders`, `/automation/taskflow`, `/automation/hooks` | Recurring jobs, proactive work, durable workflows |
| Memory/context | `/concepts/memory`, `/concepts/context-engine`, `/concepts/compaction`, `/concepts/dreaming` | Memory engines, lossless recall, compaction, background consolidation |
| Agents/harnesses | `/tools/acp-agents`, `/tools/acp-agents-setup`, `/plugins/codex-harness`, `/tools/subagents` | Codex/Claude/ACP sessions, thread-bound coding agents |
| Gateway ops | `/gateway/configuration`, `/gateway/configuration-reference`, `/gateway/health`, `/gateway/doctor`, `/gateway/troubleshooting` | Config changes, restarts, validation, runtime diagnosis |
| Security | `/gateway/security`, `/gateway/security/audit-checks`, `/gateway/sandbox-vs-tool-policy-vs-elevated`, `/gateway/secrets` | Plugin trust, sandbox/tool policy, secrets, audit checks |
| Plugins | `/plugins/community`, `/plugins/bundles`, `/plugins/manifest`, `/plugins/hooks`, `/tools/clawhub` | Plugin/skill discovery and installs |

## Browser activation rule

Browser support is first-class and bundled, but it is gated by plugin loading.

Required for local CLI/tool surface:
- `plugins.allow` includes `browser`
- Gateway restarted after plugin allowlist change
- `openclaw browser doctor` passes

Current live state after activation:
- Browser plugin enabled
- Gateway running after restart
- Default reachable profile: `chrome` on Ahmed-Mac
- `openclaw` isolated profile exists but is stopped
- `nasr-linkedin` profile exists but is stopped
- `browser` config block is absent, valid because node proxy auto-routing works
- `gateway.nodes.browser` is absent, valid with a single browser-capable node

Operating rule:
- Use Mac Chrome only when logged-in state matters.
- Use explicit isolated `openclaw` profile for generic browsing or lower-trust sites.
- Do not pin `gateway.nodes.browser.node` unless more browser-capable nodes are added or routing becomes ambiguous.
- Do not configure local VPS Chrome unless Mac node proxy becomes unavailable or a VPS-local browser is explicitly needed.

Verification commands:

```bash
openclaw browser status
openclaw browser profiles
openclaw browser doctor
openclaw browser --browser-profile chrome tabs
```

Known CLI gotcha:
- `openclaw browser profiles --json` errored in this install. Plain `openclaw browser profiles` works. If JSON is needed, check the current CLI help before assuming flag placement.

## Voice-call activation rule

Do not enable voice-call casually.

Why:
- It runs inside the Gateway process.
- Real providers require phone provider setup, public webhook reachability, security checks, and billing.
- Inbound calls must be allowlisted before exposure.

Safe rollout:
1. Read `/plugins/voice-call` and `/cli/voicecall`.
2. Start with mock/local testing only.
3. Decide provider later, likely Twilio if real calls are needed.
4. Configure inbound allowlist for Ahmed's number only.
5. Start read-only/safe behavior before any owner-level actions.
6. Verify webhook security and call logs before claiming success.

## Automation activation rule

Use native OpenClaw automation for recurring work.

Preferred pattern:
- Standing orders define authority and operating rules.
- Cron defines schedule.
- Taskflow tracks multi-step durable work when needed.

Do not revive Mission Control task-board workflows unless Ahmed explicitly re-enables them.

Use cases:
- Heartbeats and health checks: cron or heartbeat docs.
- Daily digests and proactive scans: standing order + cron.
- Multi-step workflows with retries/waits: taskflow.
- Webhook-triggered work: cron webhooks or webhooks plugin, depending on use case.

## Memory/context rule

Compacted summaries are not proof of exact details.

Use this sequence for prior-conversation precision:
1. `lcm_grep`
2. `lcm_describe` when a specific summary ID is known
3. `lcm_expand_query` for exact decisions, commands, paths, config values, or causal chains

Memory-related docs justify this split:
- `/concepts/memory`
- `/concepts/context-engine`
- `/concepts/compaction`
- `/concepts/dreaming`

Operational rule:
- Use summaries as cues.
- Expand before asserting exact values.
- Prefer fresh runtime/file evidence over old summaries.

## ACP/Codex routing rule

ACP and Codex harnesses are official OpenClaw surfaces.

Before changing coding-agent routing:
- Read `/tools/acp-agents`
- Read `/tools/acp-agents-setup`
- Read `/plugins/codex-harness`
- Check runtime availability before promising a harness launch

Routing preference:
- Plain sub-agents for isolated OpenClaw-native delegation.
- ACP for explicit Claude Code/Codex/Gemini harness requests.
- Thread-bound persistent ACP sessions when the chat/channel workflow expects ongoing coding context.

## Plugin and ClawHub rule

Plugin and skill discovery is useful but high-trust.

Before installing community plugins or ClawHub skills:
1. Read the relevant docs page.
2. Check whether the same capability already exists locally.
3. Treat install as a state-changing action requiring approval.
4. Review plugin trust, permissions, and config schema.
5. Validate config and restart only when required.
6. Verify the actual tool/CLI surface works.

Relevant docs:
- `/plugins/community`
- `/plugins/bundles`
- `/plugins/manifest`
- `/plugins/hooks`
- `/tools/clawhub`
- `/tools/skills-config`

## Gateway config safety rule

Before gateway config changes:
1. Run `openclaw --version`.
2. Check `openclaw gateway status`.
3. Check systemd user service `ExecStart` when service behavior matters.
4. Back up `~/.openclaw/openclaw.json`.
5. Read the docs/schema for the exact path.
6. Change one thing.
7. Run `openclaw config validate`.
8. Restart only if docs or plugin loading require it.
9. Verify runtime and feature-specific behavior.
10. Confirm model routing did not silently change.

Model route check:

```bash
python3 - <<'PY'
import json
print(json.load(open('/root/.openclaw/workspace/config/model-router.json')).get('default_model'))
PY
```

Expected current default: `openai-codex/gpt-5.5`.

## Current docs audit artifacts

Temporary audit files from the 2026-04-26 deep dive:
- `/tmp/openclaw-docs-audit/targeted-audit-report.md`
- `/tmp/openclaw-docs-audit/operational-index.md`

If these are missing later, regenerate from:
- `https://docs.openclaw.ai/start/hubs`
- `https://docs.openclaw.ai/llms.txt`
