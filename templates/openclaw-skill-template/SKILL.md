---
name: example-skill-name
description: Use for [specific trigger/task]. Include concrete nouns users will say. Avoid broad generic descriptions.
metadata:
  owner: NASR
  status: draft
---

# Example Skill Name

Use this skill when [specific condition]. Do not use it for [nearby non-goals].

## Outcome

The skill should produce [artifact/decision/action] with [quality bar].

## Operating rule

Source-of-truth first, safe tool first, approval boundaries explicit, verify actual outcome before closeout.

## Tool ladder

1. First-class OpenClaw tool.
2. Existing safe wrapper or workflow script.
3. Small reusable wrapper if missing.
4. Shell only when necessary.
5. External/destructive/runtime action only when approval boundary is satisfied.

## References

- `references/sources-of-truth.md` - files, databases, services, and docs to inspect first.
- `references/tools-and-fallbacks.md` - tool order and fallback rules.
- `references/approval-boundaries.md` - what is pre-approved vs requires Ahmed.

## Checklists

- `checklists/preflight.md` - before starting risky or state-changing work.
- `checklists/verification.md` - before saying done.

## Done means

- The requested output exists or the blocker is clearly named.
- Source-of-truth evidence was checked.
- Approval boundary was respected.
- Verification result is included in closeout.
