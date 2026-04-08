# LinkedIn Autoresearch Loop

A Karpathy-style feedback loop for continuously improving LinkedIn post quality.

## System Overview

```
Notion Draft → Score (10 binary Qs) → Log → Post → Track Engagement → Improve Prompt → Repeat
```

## Core Files

| File | Purpose |
|------|---------|
| `scripts/linkedin-score-post.py` | Scores a post using 10 binary eval questions |
| `scripts/linkedin-improve-prompt.py` | Analyzes winners/losers, generates improved prompt |
| `data/linkedin-research-log.json` | Persistent log of all scored posts + prompt history |

## The 10 Binary Eval Questions

Score each as YES=1, NO=0 (max 10):

1. **RESULT/TRANSFORMATION** — Hook describes a result or transformation, not just a topic.
2. **SPECIFIC_PERSON** — Features a specific person or story, not just a company.
3. **SCROLL_STOPPER** — First line creates a curiosity gap / scroll-stopper.
4. **METRIC** — Includes a specific metric or data point.
5. **HOOK_LENGTH** — Hook is under 300 characters.
6. **CTA** — Ends with a question or CTA for engagement.
7. **ACHIEVE_FRAME** — Framing is about what YOU can achieve, not what a tool/company does.
8. **NOT_PRESS_RELEASE** — Does not sound like a press release or changelog.
9. **CONTEXT_RICH** — Explains WHY, not just WHAT.
10. **URGENCY** — Creates a sense of urgency or exclusivity.

## Workflow

### Daily (Automated via cron)

1. `linkedin-auto-poster.py` fetches today's scheduled post from Notion
2. Calls `linkedin-score-post.py` to score it before publishing
3. Scores are written to `data/linkedin-research-log.json`
4. Post is published via Composio
5. Post URL is recorded in the log (engagement remains null, filled manually later)

### Manual Improvement Loop

```bash
# After collecting engagement data, run:
python3 scripts/linkedin-improve-prompt.py
```

This reads the research log, identifies winners (score ≥7 AND good engagement) and losers, finds patterns in which questions separate them, and generates an improved prompt version. Logs the change to `prompt_history`.

## Research Log Schema

```json
{
  "posts": [{
    "date": "YYYY-MM-DD",
    "post_text": "...",
    "eval_score": 7,
    "questions": [1,0,1,1,0,1,1,0,1,1],
    "engagement": { "likes": 45, "comments": 8, "shares": 3 },
    "prompt_version": 2,
    "prompt_used": "..."
  }],
  "current_prompt": "...",
  "prompt_history": [
    {"version": 1, "prompt": "...", "date": "...", "reason": "..."}
  ]
}
```

## Prompt Versioning Rules

- Version increments each time `linkedin-improve-prompt.py` generates a new version
- Each post records which prompt_version generated it
- Correlation analysis compares winners vs losers on a per-question basis
- A question is "critical" if winners pass it significantly more than losers

## Model

Uses MiniMax-M2.7 (free tier) for scoring. Fast and sufficient for binary yes/no.

## Integration with linkedin-writer skill

The `linkedin-writer` skill generates posts. This autoresearch loop evaluates and improves the prompts used by that skill over time.
