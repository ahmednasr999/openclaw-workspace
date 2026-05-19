# OpenClaw Update Guard

Local read-only guard for OpenClaw update, restart, and gateway-config-change windows.

Script:

```bash
scripts/openclaw-update-guard.py --write-report
```

Optional deep channel probe, slower and may block under channel/plugin pressure:

```bash
scripts/openclaw-update-guard.py --deep --write-report
```

## Verdicts

- `PASS` - no blocker found.
- `WARN` - inspect before proceeding. Known acceptable warnings can include newer-config-version drift or non-standard service PATH when already understood.
- `FAIL` - stop. Do not update/restart until repaired.

## What it checks

- `/tmp` has at least 2 GB free.
- `openclaw --version` works.
- systemd gateway `ExecStart`, `MainPID`, and start timestamp exist.
- `openclaw config validate` passes.
- `openclaw gateway status --deep` returns usable output and no fatal module/auth errors.
- `openclaw gateway probe --json` completes.
- model refs have not drifted from `openai-codex/gpt-5.5` to `openai/gpt-5.5`.
- Codex usage/auth does not surface a hard missing-key error, when the status command responds.
- key plugins are loaded.
- lossless-claw and file-transfer runtime tool contracts are present.

## Limits

The guard is read-only. It does not update, restart, edit config, or prove Telegram delivery. For a full update closeout, pair it with a real Telegram/NASR response test and the normal backup/update evidence.

## Post-Update Guardrail

After every OpenClaw update, do not trust CLI probes alone. CLI model/auth checks can pass while the live gateway runtime still fails to use existing Codex OAuth profiles.

Required post-update checks:

```bash
openclaw models status --agent main --probe
openclaw models status --agent cmo --probe
openclaw models status --agent cto --probe
openclaw models status --agent hr --probe
openclaw models status --agent jobzoom --probe
```

Then run:

- one live Telegram ping to `main`
- one read-only all-agent health check for `main`, `cmo`, `cto`, `hr`, and `jobzoom`

### 2026-05-19 Incident: Codex OAuth Passed CLI, Failed Live Gateway

After the OpenClaw update to `2026.5.18`, Telegram agents returned:

```text
Missing API key for provider "openai-codex"
```

Gateway logs showed the deeper runtime error:

```text
No API key found for provider openai-codex
```

What was actually broken:

- The live gateway runtime was not correctly using the existing Codex OAuth auth profiles.
- The model route requested `openai/gpt-5.5`, which should use Codex OAuth.
- Gateway runtime fell through to an API-key lookup for provider `openai-codex`.
- CLI auth probes still passed, so CLI-only verification was insufficient.

Root cause:

- Post-update auth profile migration/shape issue.
- Some Codex OAuth profiles were sidecar-backed.
- Some per-agent auth profiles had stale OAuth shadow entries.

Evidence:

- CMO cron lane failed first with `openai-codex` auth lookup against `/root/.openclaw/agents/cmo/agent/auth-profiles.json`.
- Main DM then failed with the same `openai-codex` auth lookup against `/root/.openclaw/agents/main/agent/auth-profiles.json`.
- `openclaw doctor --fix` migrated sidecar-backed Codex OAuth profiles back to inline credentials.
- `openclaw doctor --fix` also removed stale OAuth auth profile shadows from `cmo`, `cto`, and `hr`.
- After gateway restart, DM `ping` returned `pong`.
- The read-only all-agent health check showed `main`, `cmo`, `cto`, `hr`, and `jobzoom` OK.

Fix that worked:

1. Create a backup of `openclaw.json`, agent `models.json` files, and agent `auth-profiles.json` files.
2. Run `openclaw doctor --fix`.
3. Leave the orphan transcript archive prompt at `No`.
4. Restart the gateway with `openclaw gateway restart`.
5. Test live Telegram DM with `ping` -> `pong`.
6. Run a read-only health check across all agents.

If this exact error returns, do not manually paste tokens or edit secrets first. Back up config/auth files, run `openclaw doctor --fix`, restart the gateway, then live-test Telegram.

## Common Failures

### Missing API key for provider openai-codex after update

Failure:

```text
Missing API key for provider "openai-codex"
```

Likely cause:

- Codex OAuth auth profile migration or stale shadow-profile issue after an update.

Safe fix:

```text
backup -> openclaw doctor --fix -> openclaw gateway restart -> live ping test
```
