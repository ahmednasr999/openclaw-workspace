# Global Fintech Executive Radar MVP

## Objective

Create an internal, worldwide fintech intelligence wire that converts live market signals into an executive decision brief. Fundraising and M&A are first-class lanes alongside regulation, payments, digital banking, infrastructure, and leadership moves.

The canonical agent instruction is `prompts/fintech-radar-daily.md`. Keep outcome,
output, boundaries, and verification there. This document defines the product
contract and must not duplicate the full operating prompt.

## Evidence contract

- Discovery sources may surface a story but cannot establish it as fact.
- Primary and corroborated evidence rank above reporting-only items.
- Every daily Radar must include one ready-to-review LinkedIn post and an actual
  1080x1350 PNG visual. A visual concept or generation prompt alone is not a
  completed deliverable.
- If either the supporting evidence, post text, or image is missing, the content
  opportunity remains blocked and must be labelled incomplete.
- The image is complete only after `scripts/fintech-radar-visual-contract.py`
  validates a 1080x1350 PNG, copies it to both `output/fintech-radar/` and
  `/root/.openclaw/media/fintech-radar/`, and writes a matching SHA-256 manifest.
- Telegram delivery must use the media-safe copy or the current final-response
  attachment path. A generated image outside those paths is not deliverable.
- Publishing remains manual and requires Ahmed's approval.
- No public post, external alert, configuration change, or investment claim may rely on a discovery-only item.
- Facts and interpretation remain separate.
- Missing amounts, valuation, investors, or deal terms stay undisclosed rather than inferred.

## MVP terminal states

- Success: a current brief is generated with source labels, a capital ledger, GCC relevance, and at least one usable story.
- Clean noop: the pipeline runs correctly but finds no qualifying developments.
- Blocked: all search/source paths fail.
- Approval required: public website, external distribution, paid data, credentials, or public posting.

## Rollout

1. Generate and review one real internal sample.
2. Tune source quality and ranking using observed false positives.
3. Run manually for several days.
4. Add deterministic daily scheduling only after output quality is proven.
5. Consider a public product only after the internal wire consistently saves time or finds material opportunities.
