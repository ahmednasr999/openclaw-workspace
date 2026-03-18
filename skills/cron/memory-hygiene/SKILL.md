---
name: memory-hygiene
description: "Weekly cleanup of MEMORY.md: remove stale entries, archive old daily notes, keep under 100 lines."
---

# Weekly Memory Hygiene

Keep MEMORY.md clean, current, and under 100 lines.

## Steps

### Step 1: Audit MEMORY.md
- Count current lines
- Identify entries older than 30 days
- Flag entries that contradict current state

### Step 2: Archive stale content
Move outdated entries to `memory/archives/` with date stamp.

### Step 3: Consolidate
- Merge duplicate entries
- Update outdated references
- Ensure all file paths are current

### Step 4: Verify size
MEMORY.md must be under 100 lines after cleanup.

### Step 5: Clean daily notes
Archive daily notes older than 14 days to `memory/archives/`.

### Step 6: Report
"🧹 Memory hygiene: [X] lines -> [Y] lines. [Z] entries archived."

## Error Handling
- If MEMORY.md is already clean: Report "No changes needed"
- Never delete entries without archiving first

## Quality Gates
- MEMORY.md under 100 lines
- All file path references verified
- No contradictory information remains
