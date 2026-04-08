# Batch Execution Rules

## Chunk Sizing
| Item Count | Chunk Size | Strategy |
|-----------|-----------|----------|
| 1-10 | All at once | Single pass, no checkpoints needed |
| 11-50 | 10 per chunk | In-memory checkpoints |
| 51-200 | 20 per chunk | File-based checkpoints (/tmp/batch-{id}.json) |
| 200+ | 50 per chunk | File-based + progress reporting every chunk |

## Parallelism Rules
1. Check `config/tool-hooks.yaml` → `tool_properties` for each tool used
2. If `concurrent: true` → use ThreadPoolExecutor (max_workers based on rate limits)
3. If `concurrent: false` → process sequentially
4. Mixed operations → group by concurrency, parallel within groups, serial between

## Rate Limit Awareness
Before starting batch, check limits in `config/tool-hooks.yaml` → `pre_hooks.rate_limiter.limits`:
- `linkedin_comment: 5 per hour` → max 5 items/hour for LinkedIn comments
- `email_send: 10 per hour` → max 10 items/hour for emails
- `web_search: 30 per hour` → can batch 30 searches/hour

Adjust chunk timing accordingly. Never exceed limits.

## Checkpoint Format
```json
{
  "batch_id": "timestamp-operation",
  "total": 100,
  "completed": 45,
  "failed": 2,
  "remaining": 53,
  "failed_items": [
    {"item": "...", "error": "...", "retryable": true}
  ],
  "last_chunk_at": "ISO timestamp"
}
```

## Error Handling Modes
| Mode | When | Behavior |
|------|------|----------|
| `continue-on-error` | Default | Log error, skip item, continue |
| `fail-fast` | Destructive operations | Stop on first error, report |
| `retry-then-continue` | Transient-prone operations | Retry failed items once, then continue |

## Reporting
After every chunk, update the audit log:
```json
{"timestamp":"ISO","agent":"...","tool":"batch","action":"chunk_complete","detail":"45/100 processed, 2 failures"}
```

Final report goes to the calling agent or Ahmed (if standalone batch).
