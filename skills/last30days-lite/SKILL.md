---
name: last30days
version: "2.1.0"
description: "Research any topic from the last 30 days. Uses LLM query planning, Tavily + Reddit + HN community signals, optional GitHub signals, deterministic dedupe/clustering, and synthesis. NASR Research v2. Use when Ahmed asks in chat to research a person, product, company, or topic over the last 30 days. Triggers on phrases like 'last30days Peter Steinberger', 'research OpenClaw for the last 30 days', 'run last30days on AI agents enterprise', or 'research Claude Code, max 10 items'."
argument-hint: 'last30days Peter Steinberger, research OpenClaw for the last 30 days, run last30days on AI agents enterprise max 10 items'
allowed-tools: Bash, Read, Write
homepage: https://clawhub.ai/skills/last30days
tags:
  - research
  - tavily
  - deep-research
  - reddit
  - web-search
  - social-media
  - citations
  - multi-source
---

# last30days v2 — NASR Research v2

Research any topic using LLM-powered query planning, multi-lane search, canonical scoring, deterministic dedupe/clustering, and synthesis. Saves every run to `~/Documents/NASR-Research/` as a research brief.

## Quick start

### In Telegram/chat
Say any of these:

```text
last30days Peter Steinberger
research OpenClaw for the last 30 days
run last30days on AI agents enterprise
research Claude Code, max 10 items
```

### In terminal
```bash
python3 skills/last30days-lite/scripts/nasr_research.py "Peter Steinberger"
```

Or from anywhere:
```bash
python3 ~/.openclaw/workspace/skills/last30days-lite/scripts/nasr_research.py "Peter Steinberger"
```

## Architecture

```
topic
  └─> resolver.py  (LLM query planner)
        ├─ reddit queries
        ├─ web queries
        ├─ HN queries
        └─ handles, subreddits resolved
  └─> nasr_research.py  (orchestrator)
        ├─ parallel Tavily searches
        ├─ Reddit lane via Tavily site:reddit.com + public fallback
        ├─ HN lane via public Algolia search
        ├─ optional GitHub lane via gh CLI
        ├─ normalize.py (canonical schema + scoring)
        ├─ deterministic cluster + dedupe pass
        └─ LLM synthesis → brief
```

## Pipeline steps

### 1. Resolve (resolver.py)
Uses an LLM to generate a structured query plan:
- Expands person names → social handles, subreddits, related queries
- Expands product names → company, founder, competitor queries
- Generates topic variants for better coverage
- Writes query plan to `~/.cache/nasr-research/<slug>/resolve.json`

### 2. Search (Tavily + Reddit + HN + optional GitHub)
Runs the query plan across multiple lanes in parallel:
- Tavily remains the main web discovery source
- Reddit first uses Tavily `site:reddit.com` discovery, then falls back to public legacy JSON when possible
- HN uses the public Algolia API, no auth required
- GitHub uses `gh api` only when `gh auth status` succeeds; same soft-fail behavior
- Raw lane payloads are saved to the cache directory for inspection

### 3. Normalize + Score (normalize.py)
Converts raw results to canonical `ResearchItem` schema:
- Computes `recency_score`: `1 - (days_old / 30)`
- Applies an explicit **ranking profile** selected by topic type:
  - `person-balanced`: favors community/web evidence, suppresses repo noise
  - `code-balanced`: keeps GitHub useful for tooling-heavy topics
  - `repo-centric`: keeps GitHub dominant for explicit repo queries
  - `general-balanced`: boosts HN/Reddit slightly and keeps GitHub supportive
- Final score: relevance × 0.45 + recency × 0.43 + engagement × 0.12, adjusted by profile and source blending

### 4. Cluster + Dedupe
Before synthesis, items are merged deterministically when they are obviously the same story:
- Exact canonical URL match
- Exact normalized title match
- High title token overlap
- Title similarity plus entity overlap
- Cluster metadata is preserved in JSON (`cluster_size`, `cluster_sources`, `cluster_reasons`)

### 5. Synthesize
Calls LLM on the top deduped items to write a tight research brief:
- 3-5 key takeaways
- Source signals highlighted (upvotes, comments, points)
- Under 600 words

### 5. Save
Writes two files to `~/Documents/NASR-Research/`:
- `{topic-slug}.md` — human-readable brief
- `{topic-slug}.json` — full structured data with all items + scores

## Options

```
python3 nasr_research.py "<topic>" \
  [--save-dir DIR]    # default: ~/Documents/NASR-Research/
  [--max-items N]     # default: 20
```

## Environment

| Variable | Required | Source |
|---|---|---|
| TAVILY_API_KEY | Yes | `config/tavily.json` (already configured) |
| OPENAI_API_KEY | No (gateway used instead) | Host env or `~/.env` |

## Design decisions

1. **LLM resolver** — one model call generates query variants. More robust than regex rules.
2. **OpenClaw gateway first** — synthesis and resolver use the local gateway (no API key needed). OpenAI direct is a secondary fallback.
3. **Canonical schema** — all sources normalize to one item type. Easy to adjust weights later.
4. **Community lanes first** — Reddit and HN are treated as public community signal sources, with soft-fail behavior.
5. **Auto-save library** — every run writes to the save dir, building a personal research library.
6. **Deterministic dedupe** — cluster rules are explicit and inspectable in the saved JSON.
7. **GitHub is opportunistic** — useful when `gh` auth exists, safely skipped otherwise.
8. **No cron** — ad hoc research only.

## Spec

See `SPEC.md` for the full architecture specification.
