---
name: executive-intelligence-brief
description: "Owns the deterministic daily cross-source intelligence ranking and routing workflow."
metadata:
  owner: CEO Ops
  status: active
---

# Executive Intelligence Brief

## Outcome

Produce one ranked executive brief from existing RSS, web/GCC, fintech, target-company and selected X inputs. Map every retained signal to Ahmed's positioning pillars and turn it into an implication and recommended action.

## Command

```bash
python3 /root/.openclaw/workspace/scripts/executive-intelligence-brief.py
```

## Inputs

- `data/rss-content-candidates-latest.json`
- latest valid `intel/fintech-radar/fintech-radar-*.json`
- today's raw `intel/intel-YYYY-MM-DD.md`, falling back to `intel/DAILY-INTEL.md`
- optional `data/x-intelligence-candidates-latest.json`
- optional `data/x-bookmarks-latest.json`
- optional curated `data/executive-intelligence-inbox.jsonl`
- optional feedback in `data/executive-intelligence-feedback.jsonl`

## Outputs

- `intel/DAILY-INTEL.md` and `intel/EXECUTIVE-INTELLIGENCE.md`
- dated `intel/executive-intelligence-YYYY-MM-DD.md`
- `data/executive-intelligence-latest.json`
- CMO review feed `data/executive-intelligence-content-candidates-latest.json`
- conservative run memory in `data/executive-intelligence-history.jsonl`

## Safety and quality gates

- Never auto-approve, schedule, publish, send, or trade.
- Investment and on-chain monitoring are outside this workflow.
- Reject weak, promotional, stale, duplicate or pillar-irrelevant signals.
- Keep source links and label uncertainty through the recommended validation action.
- A missing optional feed is feed-health information, not permission to invent content.
- Content outputs are review inputs only.

## Done means

- The script exits zero.
- JSON outputs parse.
- Ranked links are non-empty and unique.
- At least two source types appear when available.
- `tests/test_executive_intelligence.py` passes after code changes.
