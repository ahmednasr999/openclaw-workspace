---
name: weekly-pipeline-archive
description: "Archive current pipeline snapshot to jobs-bank for historical tracking."
---

# Weekly Pipeline Archive

Thursday archive of pipeline state for historical tracking.

## Steps

### Step 1: Run archive script
```bash
bash /root/.openclaw/workspace/scripts/weekly-pipeline-archive.sh
```

### Step 2: Verify archive created
Check `jobs-bank/archives/` for new timestamped file.

### Step 3: Report
"📦 Pipeline archived: [X] jobs, file: [filename]"

## Error Handling
- If script fails: Check disk space, report error
- If archive dir missing: Create it first

## Quality Gates
- Archive file must exist in jobs-bank/archives/ after script completes
- Archive filename must include date-stamp (YYYY-MM-DD format)
- Job count in report must match actual entries in archived file
- No existing archives overwritten - each run produces a new timestamped file

## Output Rules
- No em dashes - use hyphens only
- Report format: "Pipeline archived: [N] jobs - file: [filename] - [timestamp]"
- Include path to archive file in confirmation message
- Keep output under 300 chars for Telegram delivery
