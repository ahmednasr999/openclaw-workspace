# Core File Checksum Protocol

## Problem
Multiple C-Suite agents may read and write the same core files. Without coordination, Agent A can overwrite Agent B's changes.

## Solution
Before modifying any protected core file, perform a read-check-write cycle.

## Protected Files
All files listed in `config/tool-hooks.yaml` → `pre_hooks.core_file_guard.protected_files`

## Protocol

### Before Edit
1. Read the file's full content
2. Note the line count and first line as a lightweight fingerprint
3. Proceed with your modifications

### After Edit
1. Verify your edit was applied correctly by reading the result
2. Append to audit log: file modified, by whom, line count before/after

### Conflict Detection
If you read a file and notice content you didn't expect (e.g., a section was added since your last read):
1. DO NOT overwrite blindly
2. Re-read the full file
3. Merge your changes with the new content
4. If you can't merge cleanly → report to CEO and let them resolve

## Shared Memory Files (memory/shared/*)
These use a different protocol:
- Any agent can APPEND (add new entries at the bottom)
- Only CEO can MODIFY existing entries or DELETE
- Each entry is tagged with agent name and date for attribution
- Appending never conflicts - it's always safe

## When to Skip
- Files you own exclusively (agent-specific workspace files)
- Temporary files (/tmp/*)
- Log files (append-only, no conflict possible)
