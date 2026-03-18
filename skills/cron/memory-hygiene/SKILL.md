---
name: memory-hygiene
description: "Weekly cleanup of MEMORY.md: remove stale entries, archive old daily notes, verify size and consistency."
---

# Weekly Memory Hygiene

Keep memory files clean, current, and under limits. Run every command. Report actual numbers.

## Steps

### Step 1: Audit MEMORY.md
```bash
cd /root/.openclaw/workspace
echo "=== MEMORY.md ==="
echo "Lines: $(wc -l < MEMORY.md)"
echo "Size: $(wc -c < MEMORY.md | awk '{printf "%.1fKB", $1/1024}')"

# Check for stale references (files that no longer exist)
python3 << 'STALE'
import re
with open("MEMORY.md") as f:
    content = f.read()
paths = re.findall(r'`([^`]+\.(py|sh|json|md|html|pdf))`', content)
import os
stale = []
for path, ext in paths:
    full = path if path.startswith("/") else f"/root/.openclaw/workspace/{path}"
    if not os.path.exists(full) and not os.path.exists(path):
        stale.append(path)
print(f"Stale references: {len(stale)}")
for s in stale[:10]:
    print(f"  - {s}")
STALE
```

### Step 2: Audit daily notes
```bash
cd /root/.openclaw/workspace/memory
echo "=== DAILY NOTES ==="
echo "Total: $(find . -name '20*.md' -not -name 'master-*' -not -name 'active-*' -not -name 'ats-*' -not -name 'lessons-*' -not -name 'insights*' | wc -l)"
echo "Older than 14 days:"
find . -name '20*.md' -not -name 'master-*' -mtime +14 -exec echo "  {}" \;

echo ""
echo "Recent (last 7 days):"
find . -name '20*.md' -not -name 'master-*' -mtime -7 -exec echo "  {} ($(wc -l < {})L)" \;
```

### Step 3: Archive old daily notes
```bash
cd /root/.openclaw/workspace/memory
mkdir -p archives

# Move daily notes older than 14 days
OLD=$(find . -maxdepth 1 -name '20*.md' -not -name 'master-*' -not -name 'active-*' -mtime +14 | wc -l)
if [ "$OLD" -gt 0 ]; then
    find . -maxdepth 1 -name '20*.md' -not -name 'master-*' -not -name 'active-*' -mtime +14 -exec mv {} archives/ \;
    echo "Archived $OLD old daily notes"
else
    echo "No old daily notes to archive"
fi
```

### Step 4: Check learnings files
```bash
cd /root/.openclaw/workspace
echo "=== LEARNINGS ==="
echo "LEARNINGS.md: $(wc -l < .learnings/LEARNINGS.md) lines, $(grep -c '^## 20' .learnings/LEARNINGS.md) entries"
echo "ERRORS.md: $(wc -l < .learnings/ERRORS.md 2>/dev/null || echo '0') lines"

# Check pending sync
if [ -f .learnings/pending-sync.json ]; then
    PENDING=$(python3 -c "import json; d=json.load(open('.learnings/pending-sync.json')); print(len(d.get('pending', d) if isinstance(d, dict) else d))" 2>/dev/null)
    echo "Pending sync: $PENDING items"
else
    echo "Pending sync: none"
fi
```

### Step 5: Verify active-tasks.md
```bash
cd /root/.openclaw/workspace/memory
echo "=== ACTIVE TASKS ==="
echo "Lines: $(wc -l < active-tasks.md)"
echo "Tasks: $(grep -c '^\- \[' active-tasks.md)"
echo "Completed: $(grep -c '^\- \[x\]' active-tasks.md)"
echo "Open: $(grep -c '^\- \[ \]' active-tasks.md)"

# Check for tasks older than 30 days
python3 << 'TASKS'
import re, datetime
with open("active-tasks.md") as f:
    content = f.read()
dates = re.findall(r'20\d{2}-\d{2}-\d{2}', content)
now = datetime.date.today()
old = [d for d in dates if (now - datetime.date.fromisoformat(d)).days > 30]
print(f"References older than 30d: {len(old)}")
TASKS
```

### Step 6: Report
```
Memory Hygiene - [DATE]
MEMORY.md: [X] lines ([Y]KB)
Daily notes: [X] total, [Y] archived, [Z] recent
Learnings: [X] entries, [Y] pending sync
Active tasks: [X] open, [Y] completed
Stale references: [X]
Actions taken: [list]
```

## Error Handling
- Never delete files without archiving first
- If MEMORY.md is already clean: Report "No changes needed"
- If file missing: Report which file, don't crash

## Quality Gates
- MEMORY.md under 200 lines
- Zero daily notes older than 14 days in active directory
- Zero pending sync items
- All file references in MEMORY.md point to existing files

## Output Rules
- No em dashes. Hyphens only.
- Report exact line counts and sizes
- List every archived file by name
