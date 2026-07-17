# Autoreview Skill

- Upstream source: `openclaw/agent-skills`, under `skills/autoreview`.
- This NASR installation intentionally carries one local policy patch: Codex model fallback is disabled so `gpt-5.6-sol` failures are visible instead of silently switching to Terra.
- Before syncing upstream, record the upstream commit, replace the complete directory, reapply the no-fallback patch, and rerun the full deterministic and hardening tests.
- Do not add other local behavior variants without Ahmed's explicit approval.
- Keep approval, scope, finding-triage, and closeout governance in `skills/codex-review-closeout`; keep review execution in this skill.
