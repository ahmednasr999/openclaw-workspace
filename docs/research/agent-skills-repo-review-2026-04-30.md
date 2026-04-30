# agent-skills Repo Review - 2026-04-30

Source: https://github.com/addyosmani/agent-skills
Inspected commit: 19e49a0 (2026-04-27)

## What matters

The repo packages production engineering workflows as agent skills. Its strongest pattern is not the exact files, but the discipline:

DEFINE -> PLAN -> BUILD -> VERIFY -> REVIEW -> SHIP

It also uses anti-rationalization tables to stop common agent excuses such as "tests later", "patch applied means done", and "nearby cleanup is harmless".

## Adopted locally

Applied a small governance patch rather than importing the repo wholesale.

Updated:
- `AGENTS.md`
- `docs/agent-governance/NASR-Coding-Rules-v1.md`
- `docs/agent-governance/NASR-ACP-Coding-Brief.md`
- `templates/workflows/verification.md`
- `/usr/lib/node_modules/openclaw/skills/coding-agent/SKILL.md`

Changes made:
- Added DEFINE/PLAN/BUILD/VERIFY/REVIEW/SHIP lifecycle to NASR coding doctrine.
- Added anti-rationalization table and source-driven implementation rule.
- Tightened sub-agent dispatch and verification template around actual evidence.
- Added coding-agent execution discipline section pointing to NASR coding doctrine.

## Deliberately not adopted

- Claude/Gemini/Cursor/OpenCode plugin structures.
- Hooks and session startup scripts.
- Full skill pack import.
- Any replacement of OpenClaw-specific CMO/HR/CTO/JobZoom/runtime rules.

Reason: direct import would increase prompt noise and duplicate existing OpenClaw governance.

## Future candidates

If repeated coding quality issues continue, selectively adapt:
- `source-driven-development`
- `debugging-and-error-recovery`
- `code-review-and-quality`
- `security-and-hardening`
- `test-driven-development`

Do this by extending existing OpenClaw/NASR skills, not by bulk copying.
