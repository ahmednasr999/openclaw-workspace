---
title: "Codex cross-workspace approvals can end without a visible reply"
status: verified
verified_on: 2026-08-10
area: runtime
tags: [codex, approvals, workspace-write, visible-reply]
---

# Codex cross-workspace approvals can end without a visible reply

## Summary

An interactive NASR turn completed substantial JobZoom work but ended three times with OpenClaw's generic no-visible-reply fallback. The proven trigger was running mutating Codex work against a sibling agent workspace: the active app-server sandbox was rooted in NASR's workspace, so routine JobZoom edits and commands generated approval requests. When the final approval expired or was declined, the transcript ended on a tool result without a final assistant message. Route mutations to the agent that owns the target workspace and require a concrete closeout after every expired or declined approval.

## Symptoms

- Telegram receives: `I finished the turn, but it did not produce a visible reply.`
- The underlying edits or tests may already have completed, so retrying the entire task could duplicate work.
- The turn contains repeated Codex file or command approval cards for paths under another agent's workspace.
- Gateway logs show the Codex turn completed, but the session transcript ends with a tool result and no terminal assistant text.
- Long approval waits or context-engine maintenance can increase lane delay, but they are secondary to the missing final assistant message.

## Root cause

Codex app-server `workspace-write` scope is rooted in the active agent's workspace. NASR invoked edits and commands in the JobZoom sibling workspace, outside NASR's writable root. This converted standing-preapproved internal work into native approval requests. The last approval returned declined after its wait window, and Codex produced no subsequent final message. OpenClaw correctly detected an empty interactive reply and substituted its generic fallback.

The same session also spent about 138 seconds in context compaction and reported an extended lane wait. That amplified latency but did not create the empty terminal response: the persisted transcript itself ended after the declined tool result.

## Failed approaches

- Repeating differently shaped shell commands did not solve the authorization mismatch; opaque `bash -lc` wrappers created more approval surfaces.
- Retrying the whole user task after the generic fallback would have been unsafe because several edits and tests had already succeeded.
- Changing global Codex approval or sandbox policy would weaken unrelated safety boundaries and is unnecessary for owned-workspace routing.

## Verified solution

1. Inspect sibling workspaces read-only from NASR when needed.
2. Route edits, tests, and routine commands to the agent that owns the target workspace. Do not perform sibling-workspace mutations from NASR's Codex session.
3. Call stable approved entry points directly; avoid unnecessary `bash -lc` wrappers.
4. If an approval expires or is declined, stop that gated action. Do not retry it under a different command shape.
5. Always send a concrete closeout: completed work, incomplete work, and the next safe action.
6. Before retrying any interrupted task, inspect the target worktree and artifacts so already completed operations are not repeated.

No gateway restart or global approval-policy change is required. If owner-workspace routing still produces approvals, stop and inspect the active agent workspace projection before changing runtime configuration.

## Evidence

- Live config showed `messages.visibleReplies` and `messages.groupChat.visibleReplies` both set to `automatic`; Telegram was connected and outbound sends succeeded.
- The affected transcript ended with a declined tool result and no final assistant text.
- Gateway diagnostics recorded a stalled embedded run after `turn/completed`, followed by a generic fallback send.
- The JobZoom changes and tests were preserved despite the missing closeout, proving that a blind full retry would be unsafe.
- The durable routing and closeout guards are recorded in `AGENTS.md:12`, `AGENTS.md:46`, and `TOOLS.md:53`.

## Prevention

- Keep one primary owner per workspace and execute mutations from that owner.
- Treat cross-workspace approval cards as a routing defect for standing-preapproved internal workflows, not as normal operator interaction.
- Verify user-visible delivery, not only tool success or `turn/completed`.
- Preserve the global sandbox and approval boundaries; fix routing before considering runtime-policy changes.

## When to revisit

Revisit if Codex gains supported multi-root workspace-write projection, if OpenClaw adds a safe post-tool empty-response continuation that cannot replay side effects, or if an owner-workspace turn reproduces the same fallback without any approval expiry.
