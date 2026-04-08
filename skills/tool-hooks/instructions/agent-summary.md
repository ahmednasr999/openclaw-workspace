# Agent Summary Service

After EVERY sub-agent completes, auto-generate a structured summary appended to the parent's context.

## When This Fires
- Sub-agent spawned via `sessions_spawn` completes (success or failure)
- Cron job agentTurn finishes
- Any background task returns results

## Summary Schema (JSON)

```json
{
  "agent_summary": {
    "agent": "string - agent name or spawn label",
    "task": "string - what was requested",
    "status": "completed | partial | failed | stuck",
    "duration_seconds": 0,
    "results": {
      "summary": "string - 1-2 sentences of what was accomplished",
      "key_outputs": ["array - main deliverables"],
      "files_changed": ["array - paths created/modified"],
      "files_created": ["array - new files"],
      "decisions_made": ["array - any choices the agent made"],
      "external_actions": ["array - LinkedIn posts, emails sent, etc."]
    },
    "quality": {
      "effort_level": "low | medium | high | max",
      "verification_run": true,
      "verification_result": "pass | partial | fail | skipped"
    },
    "follow_ups": ["array - items needing attention"],
    "side_findings": ["array - adjacent issues discovered"],
    "errors": ["array - any errors encountered"],
    "metrics": {
      "items_processed": 0,
      "items_succeeded": 0,
      "items_failed": 0
    }
  }
}
```

## Generation Rules

1. **Auto-generate** - don't wait for the agent to write one. Parse from:
   - The agent's final message
   - The audit log entries during the agent's session
   - File system changes (git diff if available)

2. **Append to audit log** - every summary gets logged:
   ```json
   {"timestamp":"ISO","type":"agent_summary","agent":"...","status":"...","summary":"..."}
   ```

3. **Append to daily actions** - for Dream Mode consumption

4. **If the agent was stuck** - include the stuck protocol output in the summary

5. **If verification failed** - include the verification verdict

## Delivery
- Sub-agent summaries → returned to parent agent automatically
- Cron job summaries → appended to `memory/agents/daily-{date}.md`
- Background task summaries → appended to `memory/agents/daily-actions.jsonl`

## The "Boil the Lake" Check
Before finalizing summary, ask: "What's the last 10% this agent should have done?"
If the missed 10% is quick (<2 min), note it in `follow_ups`.
If it requires new work, create a task suggestion.
