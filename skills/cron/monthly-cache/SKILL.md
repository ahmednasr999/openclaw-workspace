---
name: monthly-cache
description: "Monthly cache cleanup: clear temp files, old downloads, stale caches."
---

# Monthly Cache Cleanup

## Steps

### Step 1: Run cleanup script
```bash
bash /root/.openclaw/workspace/scripts/monthly-cache-clean.sh
```

### Step 2: Report
"🧹 Cache cleanup complete: [X] MB freed"

## Error Handling
- If script missing: Report error, list manual cleanup targets
