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
