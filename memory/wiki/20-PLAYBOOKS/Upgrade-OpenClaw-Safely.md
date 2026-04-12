# Upgrade OpenClaw Safely

## Goal
Upgrade without breaking gateway startup, routing, heartbeats, or model behavior.

## Preflight
1. Confirm current version: `openclaw --version`
2. Confirm the active gateway binary / entrypoint matches the intended build.
3. Check `/tmp` free space and require at least 2 GB.
4. Create a fresh backup before touching the install.
5. Prefer a preflight worktree or other isolated validation path before changing the live tree.

## Update flow
1. Fetch target version.
2. Validate install/build in an isolated location if practical.
3. Apply update to live tree.
4. Rebuild what the runtime actually needs.
5. Restart or reload carefully.

## Required validation after update
1. `openclaw --version`
2. gateway service health
3. `openclaw doctor`
4. GPT-5.4 routing correctness
5. heartbeat config correctness
6. Telegram topic routing correctness

## Rollback trigger
Rollback immediately if any of these regress:
- gateway startup
- core routing
- heartbeat behavior
- Telegram topic behavior
- critical model/provider alignment

## Notes from the 2026-04-11 cycle
- doctor can modify or stage service-unit changes, so inspect the resulting unit rather than assuming nothing changed.
- version alignment between shell CLI, service entrypoint, and live repo build matters.
- success means working setup preserved, not just update command exit code 0.
