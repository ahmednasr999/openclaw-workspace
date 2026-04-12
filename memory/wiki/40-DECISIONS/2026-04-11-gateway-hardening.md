# Decision: Gateway Hardening After Update Stabilization

Date: 2026-04-11

## Context
The environment had just gone through routing cleanup, session normalization, and heartbeat hardening. Gateway safety mattered more than convenience. Unit/path drift and version mismatch were proven sources of misleading diagnostics and risk.

## Decision
- Keep the gateway on a known-good repo build path.
- Run the gateway with `/usr/bin/node`.
- Use a minimal controlled PATH for the service.
- Align shell `openclaw`, doctor, and service behavior to the same live build.
- Validate after change instead of trusting update logs.

## Why
- Narrow PATH reduces surprising runtime behavior.
- Version alignment reduces false warnings and hidden incompatibilities.
- The working setup was more valuable than a theoretically cleaner but mismatched install path.

## Consequences
- Service hardening became explicit and easier to reason about.
- Doctor output became more trustworthy after CLI/service alignment.
- Any future update must verify that unit changes did not silently undo the chosen hardening.

## Related files
- `/root/.config/systemd/user/openclaw-gateway.service`
- `/root/.openclaw/openclaw.json`
- `../README.md`
