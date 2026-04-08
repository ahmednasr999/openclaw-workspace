---
name: monthly-cache
description: "Monthly cache cleanup: clear temp files, old downloads, stale caches, reclaim disk space."
---

# Monthly Cache Cleanup

## Steps

### Step 1: Audit cache sizes
```bash
echo "=== CACHE AUDIT ==="
echo "npm: $(du -sh ~/.npm 2>/dev/null | cut -f1 || echo 'none')"
echo "pip: $(du -sh ~/.cache/pip 2>/dev/null | cut -f1 || echo 'none')"
echo "/tmp: $(du -sh /tmp 2>/dev/null | cut -f1)"
echo "pnpm: $(du -sh ~/.local/share/pnpm 2>/dev/null | cut -f1 || echo 'none')"
echo "Old sessions: $(find /root/.openclaw/agents/main/sessions -name '*.reset.*' 2>/dev/null | wc -l) files"

# Total reclaimable
echo ""
echo "Disk before: $(df -h / | tail -1 | awk '{print $4}') free"
```

### Step 2: Clean caches
```bash
# npm cache
npm cache clean --force 2>/dev/null && echo "npm cache cleared" || echo "npm cache: nothing to clean"

# pip cache
pip cache purge 2>/dev/null && echo "pip cache cleared" || echo "pip cache: nothing to clean"

# Old temp files (>7 days)
OLD_TMP=$(find /tmp -maxdepth 1 -mtime +7 -not -name "." 2>/dev/null | wc -l)
if [ "$OLD_TMP" -gt 0 ]; then
    find /tmp -maxdepth 1 -mtime +7 -not -name "." -exec rm -rf {} \; 2>/dev/null
    echo "Cleaned $OLD_TMP old /tmp items"
fi

# Old session backups
find /root/.openclaw/agents/main/sessions -name "*.reset.*" -delete 2>/dev/null
echo "Cleaned old session backups"
```

### Step 3: Report
```bash
echo ""
echo "Disk after: $(df -h / | tail -1 | awk '{print $4}') free"
```

## Error Handling
- If cleanup fails: Report which step failed, continue others
- Never delete active session files (only .reset.* backups)

## Quality Gates
- Must report disk space before AND after
- Must show what was cleaned and how much

## Output Rules
- No em dashes. Hyphens only.
- Report exact MB/GB freed
