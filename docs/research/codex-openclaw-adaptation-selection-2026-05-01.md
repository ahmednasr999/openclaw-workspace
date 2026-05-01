# Codex/OpenClaw adaptation selection - 2026-05-01

## Decision

Adopt governance patterns only. Do not import Codex or agent-skills behavior wholesale.

## Already adopted

- Goal contract template: `templates/workflows/goal-contract.md`
- Implementation/review/verification workflow templates under `templates/workflows/`
- Runtime stabilization pilot goal: `docs/goals/openclaw-runtime-stabilization-goal.md`
- Premium visual quality gate: `docs/content-claw/premium-linkedin-visual-quality-gate.md`
- Runtime patch workflow docs under `docs/runtime-patches/`

## Next adaptations selected

1. **Goal contract for risky multi-step work**
   - Use when work includes config/runtime/kernel/firewall/public posting or multi-agent handoff.
   - Must state success criteria, approval gates, verification, and stop rules.

2. **Permission profile language**
   - Add compact labels to briefs/plans: read-only, local-write, external-write, runtime-change, destructive/disruptive.
   - Purpose: prevent the assistant from pausing after safe steps while still stopping before real risk.

3. **Closeout verification standard**
   - Every significant workstream closes with direct evidence: artifact path, command output, test/check result, screenshot, or named blocker.
   - Avoid proof by exit code or generated-file existence.

## Explicit non-goals

- No gateway config changes from this adaptation.
- No runtime patch edits from this adaptation.
- No full skill-pack import.
- No replacement of Ahmed/NASR-specific rules.
- No new cron until a manual sample proves value.

## Next concrete action

Apply permission-profile wording to the relevant workflow template or AGENTS coding dispatch section in a small later patch, only after current cleanup is committed.
