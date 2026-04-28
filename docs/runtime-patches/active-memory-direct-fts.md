# Active-memory direct FTS live-reply patch

Status: enabled for main Telegram direct chat.

## Decision

Keep active-memory enabled only on the fast direct FTS path for live replies. Do not put semantic/vector memory or the embedded LLM recall subagent back into the live Telegram prompt path until it passes isolated performance tests.

## Why

Observed behavior on 2026-04-27:

- Local semantic/vector memory became available, but live searches ranged from seconds to more than a minute.
- The stock active-memory embedded recall subagent exceeded the configured 4s timeout and blocked Telegram replies for about 14s.
- After patching active-memory to use direct SQLite FTS, the live Telegram path completed in 7ms with `directFts=1` in logs.

## Current operating model

- `plugins.entries.active-memory.config.enabled`: true
- Scope: `main` agent, direct chats only
- Query mode: current message
- Recall path: direct SQLite FTS over `~/.openclaw/memory/main.sqlite`
- Vector store: disabled for live memory search
- `agents.defaults.memorySearch.sync.onSearch`: false

This is intentionally keyword/FTS recall, not semantic recall. It is safer for live replies.

## Verification

Run after OpenClaw updates:

```bash
python3 scripts/check-openclaw-runtime-patches.py
```

Expected checks include:

- `OK: active-memory direct FTS live-reply patch present`

Live log evidence should look like:

```text
active-memory ... done status=ok elapsedMs=<small number> summaryChars=<n> directFts=1
```

## Rollback

If the patch breaks plugin loading or slows replies, disable only active-memory recall, not the plugin entry:

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('/root/.openclaw/openclaw.json')
cfg = json.loads(p.read_text())
cfg['plugins']['entries']['active-memory']['config']['enabled'] = False
p.write_text(json.dumps(cfg, indent=2) + '\n')
PY
openclaw config validate
systemctl --user restart openclaw-gateway.service
```

## Future semantic-memory acceptance criteria

Before semantic/vector recall can return to live replies:

- p95 under 2s on real Ahmed queries
- no timeout leak beyond the configured budget
- no embedded failover timeout surfacing after the reply
- relevance better than current FTS for actual preference/rule queries
