# Tool Hooks - Runtime Safety Layer

This skill defines the Pre/PostToolUse hook system. ALL agents MUST follow these rules for every tool call.

## When This Fires
Every tool call. No exceptions.

## Pre-Tool Check (Before calling ANY tool)

### Step 1: Permission Check (Wildcard Patterns)
Read `config/tool-permissions.yaml`. Match tool against your agent profile's patterns:
1. Check `allow_patterns` first - if tool matches an allow pattern, it's permitted
2. Check `deny_patterns` - if tool matches a deny pattern, it's DENIED
3. Pattern types: exact ("cron_remove"), prefix wildcard ("LINKEDIN_*"), path scope ("edit:memory/*.md"), command scope ("exec:rm -rf *")
4. If denied → STOP. Report: "Permission denied: {tool} matches deny pattern '{pattern}' for {agent} agent."
5. If denied but genuinely needed → escalate to CEO agent.

### Step 2: Effort Gate Check
If the tool targets a file listed in `effort_gates`:
- Check current task's effort classification (from AGENTS.md Effort Classification table)
- If effort is below the gate → STOP. Report: "Effort gate: {tool} requires {minimum} effort. Current: {current}."
- Upgrade effort if justified, then proceed.

### Step 3: Mode Check
Check current time (Africa/Cairo timezone):
- 00:00-06:00 → AFK mode active. Check `mode_overrides.afk.additional_deny`.
- If tool is in the deny list AND not a cron_scheduled exception → QUEUE to `memory/agents/afk-queue.jsonl` instead of executing. Format:
  ```json
  {"timestamp":"ISO","agent":"...","tool":"...","args_summary":"...","reason":"AFK mode"}
  ```

### Step 4: Rate Limit Check
Before calling tools listed in `pre_hooks.rate_limiter.limits`:
- Check `memory/agents/audit-log.jsonl` for recent calls of this tool type
- If over limit → WAIT or report: "Rate limit: {tool} at {count}/{limit} in the last hour."

### Step 5: Core File Guard
If editing a protected file from `pre_hooks.core_file_guard.protected_files`:
- Verify effort is ● High or above
- Read the file's current content first (for checksum comparison later)
- Log the intent to `memory/agents/audit-log.jsonl` BEFORE the edit

### Step 6: Verification Flag
If this task has already modified 2+ files and is about to modify another:
- Set internal flag: verification_needed = true
- On task completion, trigger Verification Agent (skills/verify/SKILL.md)

### Step 6b: Concurrency Check (before parallel tool calls)
Before running multiple tools in parallel:
1. Check `config/tool-hooks.yaml` → `tool_properties` for each tool
2. ALL tools must have `concurrent: true` to run in parallel
3. If ANY tool has `concurrent: false`, serialize it
4. Two write tools targeting the SAME file/resource MUST serialize regardless
5. `sessions_spawn` is concurrent (independent sessions) even though it's a write

### Step 6c: Preset Check
Check which preset is active (from `config/tool-permissions.yaml` → agent's `default_preset`):
- If a tool is NOT in the active preset's tool list → DENY
- Wildcard `*` in preset means all tools allowed
- Presets with `inherits` include the parent's tools plus `additional`
- AFK mode (00:00-06:00 Cairo) auto-switches to "afk" preset

## Post-Tool Actions (After ANY external tool call)

### Step 7: Audit Log
After any tool in `tool_categories.external_write` or `tool_categories.config_change` completes:
- Append to `memory/agents/audit-log.jsonl`:
  ```json
  {"timestamp":"ISO","agent":"...","tool":"...","action":"...","target":"...","result":"success|failure","effort":"...","detail":"..."}
  ```

### Step 8: CEO Notification
After any `external_write` action (unless you ARE the CEO agent):
- Send notification to topic 10: "✅ {agent}: {action} completed - {detail}"

### Step 9: Dream Tag
After every tool call, append to `memory/agents/daily-actions.jsonl`:
```json
{"timestamp":"ISO","agent":"...","category":"...","summary":"one-line description"}
```

### Step 10: Error Recovery
If a tool call FAILS:
1. Check if the error is transient (timeout, rate limit, network)
2. If transient → wait 3 seconds → retry ONCE
3. If retry fails → try alternative approach if one exists
4. If no alternative → report the error with full output (never paraphrase)
5. Append failure to audit log with result="failure"
