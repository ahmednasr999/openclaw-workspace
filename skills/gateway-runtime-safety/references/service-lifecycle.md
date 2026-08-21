# Gateway Service Lifecycle

Gateway lifecycle actions can interrupt Ahmed. Treat them as runtime changes.

## Preferred controls

- Restart: use first-class `gateway` tool action `restart`, but execute it only through the approved maintenance lane or a detached bounded job.
- Config write: use `gateway config.patch` or `gateway config.apply`.
- Update: use `gateway update.run` only when Ahmed explicitly asks for an update.

## Same-turn restart boundary

Never restart the live gateway from the same user-facing turn. Explicit restart approval authorizes the restart itself; it does not waive this execution boundary. Hand the action to the approved maintenance lane or a detached bounded job, include a continuation message, and let the user-facing turn survive the lifecycle interruption.

In the visible restart decision, state that the security suite must pass exactly `19/19` immediately before and after the restart, then name gateway health and the original user-visible outcome as closeout evidence.

## CLI lifecycle commands

Only use these when explicitly requested or when first-class tools cannot answer a read-only diagnosis:

- `openclaw gateway status`
- `openclaw gateway restart`
- `openclaw gateway start`
- `openclaw gateway stop`

Do not use stop/start as a restart substitute.

## Before restart

- Confirm restart is necessary.
- Confirm the user approved the restart if it was not explicitly requested.
- Capture the expected post-restart verification.
- Pass a clear continuation message if using the gateway restart tool.

## After restart

- Rerun `python3 scripts/check-memory-heist-security-suite.py`; require exactly `19/19`.
- Confirm gateway is listening.
- Confirm model/router state if model-sensitive.
- Confirm the original problem is fixed, not just that the service restarted.
