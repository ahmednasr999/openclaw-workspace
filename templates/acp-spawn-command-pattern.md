# ACP Spawn Command Pattern

Use this as the standard shape when launching ACP work with `sessions_spawn`.

## Medium coding session
```json
{
  "runtime": "acp",
  "agentId": "codex",
  "mode": "session",
  "thread": true,
  "cwd": "{{repo_or_cwd}}",
  "task": "{{paste_filled_spawn_brief_here}}",
  "timeoutSeconds": 900,
  "runTimeoutSeconds": 900
}
```

## Full build session
```json
{
  "runtime": "acp",
  "agentId": "codex",
  "mode": "session",
  "thread": true,
  "cwd": "{{repo_or_cwd}}",
  "task": "{{paste_filled_spawn_brief_here}}",
  "timeoutSeconds": 900,
  "runTimeoutSeconds": 900
}
```

## Plan-only session
```json
{
  "runtime": "acp",
  "agentId": "codex",
  "mode": "session",
  "thread": true,
  "cwd": "{{repo_or_cwd}}",
  "task": "{{paste_filled_spawn_brief_here}}",
  "timeoutSeconds": 900,
  "runTimeoutSeconds": 900
}
```

## Implement-from-plan session
```json
{
  "runtime": "acp",
  "agentId": "codex",
  "mode": "session",
  "thread": true,
  "cwd": "{{repo_or_cwd}}",
  "task": "{{paste_filled_spawn_brief_here}}",
  "timeoutSeconds": 900,
  "runTimeoutSeconds": 900
}
```

## Notes
- Set `agentId` explicitly.
- Default to `thread: true` and `mode: "session"` for chat-driven ACP work.
- Use the compact spawn brief template as the `task` payload.
- If the repo is unclear, ask before spawning.
- If Ahmed asked for planning only, do not silently turn that into implementation.
