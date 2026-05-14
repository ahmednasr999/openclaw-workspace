# Gateway Service Lifecycle

Gateway lifecycle actions can interrupt Ahmed. Treat them as runtime changes.

## Preferred controls

- Restart: use first-class `gateway` tool action `restart`.
- Config write: use `gateway config.patch` or `gateway config.apply`.
- Update: use `gateway update.run` only when Ahmed explicitly asks for an update.

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

- Confirm gateway is listening.
- Confirm model/router state if model-sensitive.
- Confirm the original problem is fixed, not just that the service restarted.
