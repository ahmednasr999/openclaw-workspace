---
description: "Memory directory README: structure, conventions, and usage rules"
type: reference
topics: [system-ops]
updated: 2026-03-14
---

# memory/ — Knowledge-Only Directory

⚠️ **THIS DIRECTORY IS FOR MARKDOWN FILES ONLY**

Everything in here is indexed by the memory search engine.
Only `.md` files belong here.

## ❌ NEVER put these here:
- `node_modules/` or any npm packages
- `package.json`, `package-lock.json`
- Python scripts (`.py`)
- Shell scripts (`.sh`)
- Log files (`.log`)
- JSON data files
- Any code or executables

## ✅ Allowed:
- Daily notes: `YYYY-MM-DD.md`
- Context files: `active-tasks.md`, `pending-opus-topics.md`
- CV outputs, research notes, strategy docs

## Why this matters:
Code files pollute the embedding model. One `node_modules/` folder
can create thousands of noise chunks that corrupt every memory search.
