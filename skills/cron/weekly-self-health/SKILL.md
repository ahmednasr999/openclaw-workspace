---
name: weekly-self-health
description: Weekly OpenClaw health/security check reporting format for CEO General.
---

# Weekly Self-Health Check

Purpose: run the weekly OpenClaw health check and report it as a decision-card, not a raw log dump.

## Output contract

Use this format for Ahmed-facing alerts:

```text
[✅ Healthy | ⚠️ Attention needed | 🚨 Action needed] Weekly OpenClaw health

Bottom line:
- Core system: [healthy/degraded/broken] - [short evidence]
- Urgency: [none/schedule/act now]
- Recommendation: [one clear next action]

🚨 Critical
- None.
```

If there are critical items, replace `None` with numbered items. Use critical only when Ahmed needs immediate action because of outage, public exposure, broken routing, failed backups, disk danger, credential/security risk, or repeated cron failure.

```text
⚠️ Important
1. [Issue]
   Impact: [why it matters]
   Recommendation: [specific next step]

ℹ️ Monitor
- [Non-blocking warning/noise]

Evidence checked:
- Gateway: [short status]
- Channels: [short status]
- Disk/memory: [short status]
- Security audit: [short status]
```

## Alert rules

- Start with the decision, not command output.
- Do not paste long command logs unless Ahmed asks or a critical issue needs proof.
- Separate real action items from noise.
- No more than 3 bullets in Bottom line.
- Use exact numbers when useful, but avoid raw diagnostic clutter.
- End with one recommendation or one approval request.
- No em dashes. Use commas or hyphens.

## Severity guide

### 🚨 Critical, interrupt Ahmed
Use only for:
- Gateway down or unreachable
- Telegram/primary routing broken
- Disk near-full or database/files at risk
- Public exposure or confirmed dangerous security posture requiring immediate action
- Backup/restore failure when data is at risk
- Repeated cron failure affecting core workflows

### ⚠️ Important, schedule work
Use for:
- Exec security too permissive
- Plugin/tool policy too broad
- Deep audit code-safety flags
- Gateway service enabled/running mismatch
- Stale PATH or service hygiene issues
- Semantic memory degraded but lexical/FTS still works
- Optional skills missing dependencies that affect a known workflow

### ℹ️ Monitor / noise
Use for:
- Optional skill requirements missing with no active workflow impact
- One-off warnings with no failed outcome
- Informational version/channel state
- Non-urgent cleanup notes

## Example

```text
⚠️ Weekly OpenClaw health: attention needed

Bottom line:
- Core system is healthy: gateway, Telegram, Slack, disk, heartbeats all OK.
- No immediate outage detected.
- Main risk is security posture: permissive exec/tool policy plus 3 code-safety flags.

🚨 Critical
- None.

⚠️ Important
1. Exec security is too permissive for some agents.
   Impact: higher blast radius if a tool path misbehaves.
   Recommendation: move high-risk agents to allowlist/approval.
2. Deep audit found 3 code-safety flags: camofox-browser, slides, tavily.
   Impact: review before trusting those skills for sensitive work.
   Recommendation: inspect and patch or quarantine.
3. memory_search semantic embeddings unavailable.
   Impact: weaker semantic recall, not an outage.
   Recommendation: schedule a separate memory dependency fix.

ℹ️ Monitor
- 39 skills missing optional requirements.
- Gateway service running but disabled, clean up later.

Recommended next action:
Approve a read-only security review plus staged hardening plan. No live changes until you approve exact commands.
```
