---
name: gateway-runtime-safety
description: Use for OpenClaw gateway config, runtime safety, restarts, updates, model-router checks, runtime patches, and service lifecycle decisions.
metadata:
  owner: CTO
  status: active
---

# Gateway Runtime Safety

Use this skill whenever the task touches OpenClaw gateway behavior, config, updates, restarts, model routing, runtime patches, service health, or live runtime repair.

## Operating rule

Gateway work is high-risk. Use source-of-truth tools first, change one thing at a time, and verify the real user-visible outcome before closeout.

## Tool ladder

1. First-class `gateway` tool for config schema, config reads, config patches, config apply, restarts, and updates.
2. `session_status` and existing health scripts for read-only status.
3. Local docs and source only when schema/docs are needed.
4. Shell only for direct, bounded inspection that first-class tools cannot answer.
5. Ask Ahmed before runtime/config/update/restart actions unless he explicitly approved the maintenance window.

## Approval boundary

Read-only diagnosis is allowed. Config writes, updates, restarts, service lifecycle changes, credential changes, destructive changes, and public ingress changes require explicit approval unless the current user request clearly authorizes that exact action.

When Ahmed explicitly approves a named maintenance repair, treat that as authorization to use the narrowest available first-class gateway/cron tool or bounded `host=gateway` execution path. Use timeouts, backups, one change at a time, and real verification. If the runtime policy still denies the tool, report the exact missing capability key instead of retrying the same denied call.

## References

- `references/config-schema-first.md` - config workflow and schema-first rule.
- `references/service-lifecycle.md` - restart/start/stop boundaries.
- `references/model-router.md` - model override and leak locations.
- `references/runtime-patches.md` - runtime patch verification.
- `references/failure-modes.md` - common gateway failure patterns.

## Checklists

- `checklists/config-change-preflight.md` - before any config write.
- `checklists/restart-preflight.md` - before restart or lifecycle action.
- `checklists/update-preflight.md` - before OpenClaw update.
- `checklists/post-change-verification.md` - before saying done.

## Done means

- The requested state or diagnosis was verified against source-of-truth evidence.
- Any config/runtime change has schema evidence and post-change verification.
- Remaining risk is named.
- No gateway safety rule was weakened to avoid approvals.
