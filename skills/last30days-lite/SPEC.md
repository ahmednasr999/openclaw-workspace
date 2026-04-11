# NASR Research v2 — Specification
**Date:** 2026-04-10
**Status:** Draft

---

## 1. Problem Statement

Our current `last30days-lite` skill is a single Tavily search + LLM synthesis. It works for quick lookups but has these gaps:

1. **No query planning** — searches the raw topic string, misses semantic relationships
2. **No cross-source clustering** — same story appears from Reddit, X, and YouTube as three separate items
3. **No engagement scoring** — treats a 10-upvote Reddit comment the same as a 5,000-upvote one
4. **No entity disambiguation** — "Peter Steinberger" and "@steipete" are two queries, not one
5. **No deduplication** — identical findings appear multiple times with different sources

The goal is NOT to build another `last30days-skill` (heavy, auth-heavy, scope-heavy). It is to build a **lean, reliable research layer** that improves on the current stack materially while staying maintainable.

---

## 2. Architecture

```
topic string
    │
    ▼
┌─────────────────────────┐
│   1. Pre-research       │  ← NEW: resolve handles, subs, channels
│      Resolver           │
└──────────┬──────────────┘
           │ resolved query plan
           ▼
┌─────────────────────────┐
│   2. Source Search      │  ← existing: Tavily + optional Reddit via ScrapeCreators
│      (parallel)         │
└──────────┬──────────────┘
           │ raw results
           ▼
┌─────────────────────────┐
│   3. Normalize &        │  ← NEW: canonical schema, per-source metadata
│      Score              │
└──────────┬──────────────┘
           │ scored items
           ▼
┌─────────────────────────┐
│   4. Cluster &          │  ← NEW: merge same-entity across sources
│      Dedupe              │
└──────────┬──────────────┘
           │ clusters
           ▼
┌─────────────────────────┐
│   5. Render             │  ← existing: LLM synthesis into brief
│      & Save             │
└─────────────────────────┘
```

### Phase 1 scope (this build)
- Steps 1 and 3
- Source: Tavily (existing) + Reddit via Tavily `site:reddit.com` queries (primary, no auth) + auth-free Reddit JSON API (soft-fail fallback)
- No new auth requirements for Phase 1

### Phase 2 scope (this build)
- Step 2: parallel multi-lane search
- Step 4: deterministic cross-source clustering + dedupe
- Step 2b: optional GitHub signals via `gh` when auth is available

### Phase 3 scope (this build — was "later")
- [x] OpenClaw gateway as primary LLM path (no API key required)
- [x] OpenAI direct as secondary fallback (when key present)
- [x] Deterministic resolver fallback (strong multi-query variant, not weak generic)
- [x] Reddit lane integrated (Tavily `site:reddit.com` primary; auth-free Reddit JSON soft-fail with explicit HTTP 403/429 logging)
- [x] LLM resolver uses `openclaw/main` alias → routes to `openai-codex/gpt-5.4` via OpenClaw gateway
- [x] Tavily gate tightened: tavily lane now requires `primary_hits ≥ required_hits OR (primary ≥ 1 AND distinctive ≥ 2 AND coverage ≥ 0.5)` to block tangential social results
- [x] Explicit ranking profiles (person-balanced, code-balanced, repo-centric, general-balanced)
- [x] GitHub source weight capped on non-code topics via profile system
- [ ] Prompt injection hardening
- [ ] Per-author caps

---

## 3. Components

### 3a. Pre-research Resolver (`scripts/resolver.py`)

**Purpose:** Convert a topic string into a structured query plan before any search fires.

**Input:** topic string, e.g. `"Peter Steinberger"` or `"AI agents for enterprise"`

**Output:**
```json
{
  "canonical_topic": "Peter Steinberger",
  "type": "person",
  "queries": {
    "reddit":    ["Peter Steinberger", "steipete"],
    "hackernews": ["Peter Steinberger"],
    "web":       ["Peter Steinberger OpenAI 2026", "Peter Steinberger GitHub"],
    "youtube":   ["Peter Steinberger interview", "Peter Steinberger podcast"]
  },
  "handles":    {"x": "@steipete", "github": "steipete"},
  "subreddits": ["r/openclaw", "r/programming"],
  "channels":   [],
  "confidence": "high"
}
```

**Resolution rules:**

| Input pattern | Type | Action |
|---|---|---|
| `@handle` | x_handle | expand via web search |
| github.com/USER | github | extract username |
| Known company/person name | person | web lookup for social handles |
| Product/tool name | product | web lookup for company + founder |
| Generic topic | topic | generate related queries |
| Plain text | topic | use as-is + generate variations |

**Implementation:**
- Phase 1: LLM call to the resolver model to generate the query plan
- Each `queries.*` list is max 3 queries
- Confidence field: `high` if type detected, `medium` if generic

**Output file:** `~/.cache/nasr-research/<slug>/resolve.json`

### 3b. Result Normalizer (`scripts/normalize.py`)

**Purpose:** Convert raw Tavily results into a canonical item schema.

**Schema:**
```json
{
  "id": "hash of url+title",
  "title": "...",
  "url": "...",
  "source": "tavily|reddit|hn|web",
  "source_sub": "r/...",
  "published_date": "YYYY-MM-DD",
  "engagement": {
    "upvotes": 0,
    "comments": 0,
    "shares": 0
  },
  "relevance_signal": 0.0,
  "recency_score": 0.0,
  "final_score": 0.0,
  "entities": ["Peter Steinberger", "OpenAI"],
  "snippet": "..."
}
```

**Scoring:**
- `relevance_signal`: from Tavily relevance score (0-1)
- `recency_score`: `1 - (days_old / 30)` for recency penalty
- `final_score`: `relevance_signal * 0.5 + recency_score * 0.5`
- Per-source bonus: Reddit with engagement gets `+0.1`; HN with high score gets `+0.1`

### 3c. Orchestrator (`scripts/nasr_research.py`)

**CLI:**
```bash
python3 nasr_research.py "<topic>" [--save-dir ~/Documents/NASR-Research/]
```

**Flow:**
1. Run resolver → query plan
2. Run parallel Tavily search for each query in `queries.*`
3. Normalize results → scored items
4. Render synthesis (LLM call)
5. Save to `save-dir/{topic-slug}.md`

---

## 4. Output Format

```markdown
# Research Brief: {topic}

**Generated:** {date} | **Sources:** {n} | **Top Score:** {score:.2f}

## Overview
{synthesis paragraph}

## Key Findings
- **{source}** [{source_sub}]: finding text (score: 0.XX)
  - Source: URL | Published: date

## Communities Active
{r/RedditName: n findings} | {HN tags}

## Signals
| Platform | Signal |
|---|---|
| Reddit | top post: N upvotes, N comments |
| Hacker News | top post: N points |
| Web | N sources, top domain |

## Research Notes
{freeform synthesis}

---
Sources: {list of URLs}
```

---

## 5. Auth & Dependencies

| Requirement | Status | Notes |
|---|---|---|
| Tavily API | ✅ Already configured | `config/tavily.json` |
| Python 3.12+ | ✅ VPS has 3.13 | No special deps |
| ScrapeCreators | ⏳ Optional | Phase 2 |
| gh CLI | ✅ Available | Optional GitHub signals lane when auth is present |
| No new keys for Phase 2 | ✅ | GitHub lane reuses existing `gh` auth only |

---

## 6. Phases

### Phase 1 (NOW)
- [ ] resolver.py (LLM-based query planning)
- [ ] normalize.py (canonical schema + scoring)
- [ ] nasr_research.py (orchestrator, CLI)
- [ ] Update SKILL.md to use new scripts
- [ ] Test on 3 real topics
- [ ] Save library behavior

### Phase 2
- [x] Parallel multi-lane search
- [x] Cross-source clustering and dedupe
- [x] Optional GitHub signals source
- [ ] Per-author caps

### Phase 3
- [ ] Prompt injection hardening
- [ ] Stronger entity resolution
- [ ] Single-pass comparison mode

---

## 7. File Structure

```
skills/last30days-lite/
├── SKILL.md
├── SPEC.md               ← this file
├── scripts/
│   ├── nasr_research.py  ← orchestrator + CLI
│   ├── resolver.py       ← pre-research query planner
│   ├── normalize.py      ← canonical schema + scoring
│   └── render.py         ← output template
├── docs/
│   └── design-notes.md   ← decisions and rationale
└── tests/
    └── test_resolver.py  ← unit tests
```

---

## 8. Design Decisions

1. **LLM-based resolver** — explicit planning beats rule heuristics. One model call to generate query variants is cheap and more robust than regex.
2. **Canonical schema** — all sources normalize to one item type. Easy to swap scoring weights later.
3. **Deterministic clustering** — duplicate merges rely on explicit canonical URL and title/entity overlap rules, not opaque embeddings.
4. **GitHub lane is opportunistic** — use `gh` if auth is present, skip cleanly otherwise.
5. **Save library** — every run auto-saves to `~/Documents/NASR-Research/` and keeps raw lane JSON in cache for inspection.
6. **No cron for this skill** — ad hoc research only. Watchlist mode deferred to a later phase.
