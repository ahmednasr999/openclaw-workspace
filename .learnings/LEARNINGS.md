# Learnings Log

*Corrections, knowledge gaps, and best practices.*
*Format: [LRN-YYYYMMDD-XXX]*

---

## [LRN-20260304-001] best_practice

**Logged**: 2026-03-04T10:23:00Z
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
QMD embed fails on VPS without GPU, falls back to CPU at ~500 B/s (unusable)

### Details
QMD uses node-llama-cpp for local GGUF embeddings. On our Hostinger VPS (no GPU, 2 CPU cores), it tries to build llama.cpp with CUDA, fails, falls back to CPU. Embedding 459 chunks would take 30+ minutes. Fix: set searchMode to "search" (BM25 only) which works instantly.

### Suggested Action
For any VPS without GPU: always use QMD in BM25-only mode (searchMode: "search"). Only enable vector search if remote embedding provider is available.

### Metadata
- Source: error
- Related Files: ~/.openclaw/openclaw.json
- Tags: qmd, embeddings, gpu, vps
- Pattern-Key: infra.no_gpu_embedding_fallback

---


### 2026-03-05: Never use sed to delete markdown table rows
**What happened:** Used `sed -i` to remove a row from pipeline.md. It left a blank line that broke the table rendering on GitHub.
**What to do:** Always use the `edit` tool with exact old/new text replacement when modifying markdown tables. Never use sed for table row operations.

### 2026-03-05: Pipeline table sorting rules
**Rule:** Active Pipeline table: always sorted by Applied date (newest first). Radar Needs Action table: always sorted by Priority (🔴 High first, then 🟡 Medium, then 🟢 Low).
**Applies to:** Every pipeline.md update.

### 2026-03-05: Never replace table row with empty string
**What happened:** Used edit tool to replace a table row with empty string `""`. This left a blank line that broke the markdown table rendering. Happened twice in one session.
**What to do:** When removing a row, include it together with the adjacent row in old_string, and put only the adjacent row in new_string. This eliminates the blank line cleanly.

### 2026-03-05: Never conclude a file doesn't exist after checking one path
**What happened:** Ahmed asked about LinkedIn cookies. Checked `/root/.openclaw/config/` (wrong), concluded "no cookies", asked Ahmed to provide them. They were at `/root/.openclaw/workspace/config/` all along. Wasted time and broke trust.
**What to do:** (1) Always run `find /root -name "*filename*"` before saying "not found". (2) Read the script that uses the file to find the correct path. (3) Never guess paths, always verify.

### 2026-03-05: Always use linkedin-jd-fetcher.py for full JDs before ATS scoring
**What happened:** Scored Anduril at 85% based on job title alone. Full JD revealed Secret Clearance requirement and defense-only focus, dropping real score to 64%. Wasted time generating a CV for a role that's a poor fit.
**What to do:** Always fetch full JD with `linkedin-jd-fetcher.py` BEFORE scoring or generating CVs. Never score based on title alone.
