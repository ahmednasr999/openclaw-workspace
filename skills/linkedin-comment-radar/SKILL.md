---
name: linkedin-comment-radar
description: Discover fresh LinkedIn posts by topic or hashtag, rank them for comment opportunities, and draft ready to post comments in Ahmed voice. Use when asked to find posts for engagement, build a top 10 table by freshness plus engagement, or generate URL plus comment pairs.
metadata: {"openclaw":{"emoji":"📡"}}
---

# LinkedIn Comment Radar

## Overview
Use this skill to run a repeatable pipeline for LinkedIn comment opportunities: discovery, filtering, ranking, and optional comment drafting.

## Workflow
1. Discover candidate posts with operator based search.
2. Apply freshness gate first.
3. Extract available engagement metrics.
4. Rank posts and return a clean table.
5. Draft comments only after user confirms shortlist.

## Discovery Query Standard
**For Ahmed's engagement, use these rules:**

**Freshness:** Last 24 hours (today only), not 7 days

**Geography:** GCC countries only:
- Saudi Arabia / UAE / Qatar / Bahrain / Kuwait / Oman
- Use: "Saudi Arabia" OR "UAE" OR "Dubai" OR "Riyadh" OR "Qatar" OR "Bahrain" OR "Kuwait" OR "Oman"

**Topics:** 
- Digital Transformation, PMO, Program Management, Healthcare IT, Leadership, AI in business

**Sort by:** Top engagement (most reactions/comments first)

**Query pattern:**
```
site:linkedin.com/posts after:2026-03-12 ("Digital Transformation" OR "PMO" OR "Healthcare" OR "AI" OR "Leadership") (Saudi OR UAE OR Dubai OR Riyadh OR Qatar OR Bahrain) -jobs -hiring -apply
```

Rules:
- Freshness: 24 hours max
- GCC geo required in post or author location
- Sort by engagement (likes, comments)
- Exclude job/hiring noise

## Ranking Rules
Use Post Quality Score (PQS 0-100):
1. Freshness (30)
2. Author signal (25)
3. Topic fit (25)
4. Engagement proxy (20)

If reactions are missing, mark as `N/A` and use comments proxy.
Default threshold: PQS >= 40.

## Output Format
When user asks for metrics only, return:

| Post | How old | # Reactions |
|---|---:|---:|
| Post 1 | 20h | 10 |

When user asks for posting pack, return one by one:
1) URL
2) Comment draft

## Comment Style Rules
- Enforce `references/comment-style-guide.md` as a hard lint check before output.
- Keep comments 2 to 4 lines, direct and practical.
- Start with insight, never generic praise openers.
- Include one concrete anchor: governance, cadence, owner, metric, or value.
- Add one sharp question in about 40 percent of comments.
- No em dashes.
- Match Ahmed executive tone.

## Escalation and Fallback
- If search surface is stale, tighten `after:` window.
- If reactions are unavailable, continue with comments count and label limitation.
- If user asks to stop drafting, switch to metrics only mode.

## Resources
- `scripts/run_radar.py`: optional helper to run discovery plus metadata extraction.
- `references/query-templates.md`: reusable templates by objective.
