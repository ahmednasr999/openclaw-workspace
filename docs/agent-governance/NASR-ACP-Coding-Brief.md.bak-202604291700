# NASR ACP Coding Brief

Use this as the default briefing structure for ACP coding sessions and coding-focused sub-agents.

It is intentionally short.
The doctrine lives in `NASR-Coding-Rules-v1.md`.
This file exists to make future ACP launches consistent without copying long rule blocks into every prompt.

## Default brief template

```md
TASK: [one sentence describing the deliverable]

SCOPE:
- [exact files, directories, surfaces, or systems allowed]
- [include repo/workdir boundaries when relevant]

DO NOT:
- no unrelated cleanup
- no speculative refactors
- no config changes, restarts, or dependency changes unless explicitly requested
- no edits outside scope

DONE WHEN:
- [exact condition that proves completion]
- [exact test, command, or user-visible check]

REPORT FORMAT:
- CHANGED
- WHAT
- VERIFIED
- TEST
- RISK
- NEXT

Before coding, follow:
- /root/.openclaw/workspace/docs/agent-governance/NASR-Coding-Rules-v1.md
```

## Default operator behavior

When using this brief:

1. Keep the task sentence singular and concrete.
2. Scope the agent tightly.
3. Name at least one real verification step in `DONE WHEN`.
4. If the task is ambiguous, include the primary assumption explicitly.
5. If the task is risky, say what is off limits in `DO NOT`.

## Example

```md
TASK: Fix the failing CSV export in the analytics report endpoint.

SCOPE:
- `src/routes/reports.py`
- `src/services/report_export.py`
- existing tests under `tests/reports/`

DO NOT:
- no config edits
- no dependency changes
- no unrelated formatting or refactors
- do not touch PDF export

DONE WHEN:
- CSV export works for the broken reproduction case
- `pytest tests/reports/test_csv_export.py -q` passes

REPORT FORMAT:
- CHANGED
- WHAT
- VERIFIED
- TEST
- RISK
- NEXT

Before coding, follow:
- /root/.openclaw/workspace/docs/agent-governance/NASR-Coding-Rules-v1.md
```

## Why this structure

This prevents the most common ACP failure modes:
- task drift from vague prompts
- overbuilding from weak scope boundaries
- fake completion from vague success criteria
- noisy reports with no proof

## Rule

Do not paste the full coding doctrine into ACP prompts unless there is a very specific reason.
Reference the canonical file instead.
