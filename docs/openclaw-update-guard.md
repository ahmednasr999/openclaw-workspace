# OpenClaw Update Guard

Local read-only guard for OpenClaw update, restart, and gateway-config-change windows.

Script:

```bash
scripts/openclaw-update-guard.py --write-report
```

Optional non-delivered cold/warm gateway turn timing, slower and uses model budget:

```bash
scripts/openclaw-update-guard.py --measure-turn-latency --write-report
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
- OpenClaw install footprint is below the release-risk threshold.
- Direct dependency count is below the release-risk threshold.
- Duplicate nested `openclaw/node_modules` dependency tree is absent.
- Native optional package count is not unexpectedly high.
- Plugin runtime LLM support is inspected through `runtime.llm.complete` evidence where available.
- Optional non-delivered gateway agent turns can record cold/warm turn latency with `--measure-turn-latency`.
- systemd gateway `ExecStart`, `MainPID`, and start timestamp exist.
- `openclaw config validate` passes.
- Docker sandbox image `openclaw-sandbox:bookworm-slim` exists.
- Telegram direct/group reply-delivery config is known-good: `messages.visibleReplies = automatic` and `messages.groupChat.visibleReplies = automatic`.
- `openclaw gateway status --deep` returns usable output and no fatal module/auth errors.
- `openclaw gateway probe --json` completes.
- model refs have not drifted from `openai-codex/gpt-5.5` to `openai/gpt-5.5`.
- Codex usage/auth does not surface a hard missing-key error, when the status command responds.
- key plugins are loaded.
- lossless-claw and file-transfer runtime tool contracts are present.

## Limits

The guard is read-only. It does not update, restart, edit config, or prove Telegram delivery. For a full update closeout, pair it with a real Telegram DM test: send `/new`, then `ping`, and verify a visible `pong` reply in the DM.

## Release Performance Gates

The guard now includes release-footprint checks prompted by the 2026-05-29 OpenClaw lighter-core report. These checks are read-only and are intended to catch package-shape regressions before an update window is accepted.

Current thresholds:

- Install size warning: greater than `850 MB` under `/usr/lib/node_modules/openclaw`.
- Direct dependency count warning: greater than `450` direct packages under OpenClaw `node_modules`.
- Native optional package warning: greater than `18` known native optional package variants.
- Hard failure: duplicated nested dependency tree at `/usr/lib/node_modules/openclaw/node_modules/openclaw/node_modules`.

Current verified baseline from the latest guard run:

- Install size: `505 MB`.
- Direct dependency count: `331`.
- Native optional package count: `0`.
- Duplicate nested OpenClaw dependency tree: absent.
- `runtime.llm.complete`: still a warning, because runtime inspection does not provide explicit availability evidence in this build.
- Turn latency: optional, latest measured cold `10.5s` and warm `9.6s` through non-delivered gateway agent turns.

Latest report:

```text
/root/.openclaw/workspace/reports/openclaw-update-guard-20260529-030746.txt
```

## Post-Update Guardrail

After every OpenClaw update, do not trust CLI probes alone. CLI model/auth checks can pass while the live gateway runtime still fails to use existing Codex OAuth profiles.

Required post-update checks:

```bash
docker image inspect openclaw-sandbox:bookworm-slim
scripts/openclaw-update-guard.py --write-report
```

The guard must include the reply-delivery config checks. Expected config values:

```json
{
  "messages": {
    "visibleReplies": "automatic",
    "groupChat": {
      "visibleReplies": "automatic"
    }
  }
}
```

Then run model probes:

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


### 2026-05-22 Incident: Sandbox Image Missing, Then Telegram DM Reply Not Delivered

After the OpenClaw `2026.5.22` update, Telegram first showed:

```text
Something went wrong...
```

The immediate cause was a missing Docker sandbox image:

```text
openclaw-sandbox:bookworm-slim
```

Fix used:

```bash
docker build -t openclaw-sandbox:bookworm-slim
```

Use the inline Dockerfile from:

```text
/usr/lib/node_modules/openclaw/docs/gateway/sandboxing.md
```

A second failure remained: Telegram DM messages were processed internally, and session logs showed assistant text such as `pong`, but no visible Telegram DM reply was sent.

Root cause:

- Reply-delivery config was wrong for direct chats.
- Direct chats need `messages.visibleReplies = automatic`.
- Group/topic replies should use `messages.groupChat.visibleReplies = automatic`; `message_tool` can keep non-main group-topic replies private.

Known-good config:

```json
{
  "messages": {
    "visibleReplies": "automatic",
    "groupChat": {
      "visibleReplies": "automatic"
    }
  }
}
```

Behavior rule:

- For normal Telegram/chat replies, reply as final assistant text in the current turn.
- Do not use `sessions_send`, `message`, or Telegram send tools to answer the message that triggered the current turn.
- `sessions_send` is only for cross-session or sub-agent handoff.

Closeout proof after future updates:

1. `docker image inspect openclaw-sandbox:bookworm-slim` passes.
2. `messages.visibleReplies == automatic`.
3. `messages.groupChat.visibleReplies == automatic`.
4. Real Telegram validation: `/new`, then `ping`, with visible `pong` in the DM, plus visible replies in CTO topic 8, CMO topic 7, HR topic 9, and JobZoom topic 5247.

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
