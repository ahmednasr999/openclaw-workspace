# Error Recovery Protocol

When a tool call fails, follow this escalation ladder. Never just report the error and stop.

## Step 1: Classify the Error

| Error Type | Examples | Action |
|-----------|----------|--------|
| Transient | Timeout, 429 rate limit, network error, 503 | Retry with backoff |
| Auth | 401, 403, expired token, invalid credentials | Report + suggest fix |
| Input | 400, missing field, invalid format | Fix input + retry |
| Permanent | 404, feature not available, tool doesn't exist | Try alternative |
| Unknown | Unexpected response, empty result | Log + report |

## Step 2: Retry (Transient Errors Only)

1. Wait 3 seconds
2. Retry the exact same call ONCE
3. If retry succeeds → proceed normally, note "succeeded on retry" in audit log
4. If retry fails → move to Step 3

## Step 3: Try Alternative Approach

| Failed Tool | Alternative |
|------------|-------------|
| Composio LinkedIn post | Direct API via proxy_execute |
| web_search | web_fetch on Google directly |
| Himalaya email | Composio Gmail tool |
| Image generation (one model) | Try next model in chain |
| Browser proxy (Mac offline) | Camoufox on VPS |
| YouTube transcript | Flag "Mac required" |

If no alternative exists → move to Step 4

## Step 4: Report with Full Context

Report must include:
- Exact error message (quoted, not paraphrased)
- What was attempted
- What retry/alternative was tried
- What the user needs to do (if anything)

**Never say:** "The operation was completed successfully" when it wasn't.
**Never say:** "I'll try that" and then not try it.

## Step 5: Log the Failure

Append to `memory/agents/audit-log.jsonl`:
```json
{
  "timestamp": "ISO",
  "agent": "...",
  "tool": "...",
  "action": "...",
  "result": "failure",
  "error": "exact error message",
  "retry_attempted": true,
  "alternative_attempted": "tool name or false",
  "resolution": "reported to user | queued | fixed"
}
```
