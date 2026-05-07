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
