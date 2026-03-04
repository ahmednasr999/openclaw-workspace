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

