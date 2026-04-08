# Batch Operations Skill

Apply the same operation across multiple items with built-in parallelism, error collection, and checkpoint/resume.

## When to Use
- Bulk file operations (rename, edit, format N files)
- Bulk API calls (send N emails, update N records, label N items)
- Bulk data processing (score N jobs, review N applications)
- Any task where the same action repeats across a list

## Workflow

### Step 1: Define the Batch
Identify:
- **Items**: List of targets (files, records, URLs, etc.)
- **Operation**: What to do with each item (edit, send, score, etc.)
- **Parallelism**: Can items be processed in parallel? Check `tool_properties` in `config/tool-hooks.yaml`

### Step 2: Plan Execution
Read `instructions/batch-execution.md` for:
- Chunk sizing (based on rate limits and timeouts)
- Checkpoint strategy (in-memory for <50 items, file-based for 50+)
- Error handling (continue-on-error vs fail-fast)

### Step 3: Execute
For each chunk:
1. Process items (parallel if tool is `concurrent: true`, serial otherwise)
2. Collect results: `{item, status: success|failure, result, error}`
3. Checkpoint progress after each chunk
4. Respect rate limits from `config/tool-hooks.yaml`

### Step 4: Report
Generate summary:
```
Batch: {operation} on {total} items
✅ Succeeded: {count}
❌ Failed: {count} (details below)
⏭️ Skipped: {count}
Duration: {time}

Failed items:
- {item}: {error}
```

### Step 5: Recovery (if failures)
For failed items:
1. Classify errors (transient vs permanent) per `instructions/error-recovery.md`
2. Retry transient failures once
3. Report permanent failures with full error context
