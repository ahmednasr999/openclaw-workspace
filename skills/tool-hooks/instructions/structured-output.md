# Structured Output Mode

## When to Use
- Cron job results (Dream Mode, morning briefing, auto-poster)
- Sub-agent returns to parent agent
- Any output that will be parsed by another agent (not read by Ahmed)

## Format
When operating in structured mode, return results as JSON with this schema:

```json
{
  "agent": "string - agent name",
  "task": "string - task description",
  "status": "success | partial | failure",
  "effort": "low | medium | high | max",
  "started_at": "ISO timestamp",
  "completed_at": "ISO timestamp",
  "results": {
    "summary": "string - one paragraph",
    "items": ["array of key outputs"],
    "files_changed": ["array of file paths"],
    "decisions_made": ["array of decisions"],
    "errors": ["array of errors encountered"]
  },
  "follow_ups": ["array of items needing attention"],
  "side_findings": ["array of adjacent issues spotted"],
  "metrics": {
    "items_processed": 0,
    "items_succeeded": 0,
    "items_failed": 0
  }
}
```

## When NOT to Use
- Direct conversation with Ahmed (use natural language)
- Quick lookups and answers
- Error messages (use natural language for clarity)

## How Dream Mode Uses This
Dream Mode reads `memory/agents/daily-actions.jsonl` which contains structured entries.
Structured output makes consolidation reliable - Dream Mode can count, filter, and pattern-match without parsing prose.
