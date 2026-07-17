# NASR Local Integration

- Upstream repository: `https://github.com/openclaw/agent-skills`
- Upstream path: `skills/autoreview`
- Installed commit: `599be8dcd33369ce06324cdb63da2e421830fac2`
- Installed date: `2026-07-15`

## Intentional policy patch

The upstream automatic Codex retry from `gpt-5.6-sol` to `gpt-5.6-terra` is disabled. NASR preserves Ahmed's explicit model choice and fails visibly when Sol is unavailable.

The patch changes the default Codex fallback to `None`, rejects any programmatic Codex fallback model at execution time, updates deterministic and unit tests to require Sol-only failure behavior, and updates the skill documentation. Claude fallback chains remain explicit and opt-in.

## Upgrade procedure

1. Fetch the current upstream skill and record its commit.
2. Replace this directory from upstream.
3. Reapply the no-Codex-fallback policy patch.
4. Update this file with the new commit.
5. Run Python compilation, `scripts/autoreview --self-test`, the unit tests, the hardening suite, and the benign real-review harness.
