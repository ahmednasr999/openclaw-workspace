---
name: memory-index
description: "Daily memory indexing: embed and update search index for all memory files."
---

# Memory Index - Daily Embed

Update the memory search index with today's notes and changes.

## Steps

### Step 1: Find changed files
Check which memory files were modified today:
```bash
find /root/.openclaw/workspace/memory -mtime 0 -name "*.md"
```

### Step 2: Update index
Run indexing commands with low priority:
```bash
nice -n 19 ionice -c 3 [indexing commands]
```

### Step 3: Verify index
Confirm index is searchable and up to date.

### Step 4: Report
"📇 Memory index updated: [X] files indexed"

## Error Handling
- If indexing fails: Report error, don't delete existing index
- Use nice/ionice to avoid impacting system performance

## Quality Gates
- Index update runs only on files modified today (not a full re-index)
- nice/ionice flags applied to avoid system impact
- Existing index preserved if new indexing run fails
- Report confirms count of files indexed matches files found in Step 1

## Output Rules
- No em dashes - use hyphens only
- Report format: "Memory index updated: [N] files indexed - [timestamp]"
- Keep output under 200 chars for Telegram delivery
- If zero files changed: "Memory index: no changes today"
- If error: include which step failed and the error message
