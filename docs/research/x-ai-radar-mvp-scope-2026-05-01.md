# X AI radar MVP scope - 2026-05-01

## Goal

Produce one daily Telegram DM radar of high-signal AI/operator posts from X, using existing local/browser-first assets before paid APIs.

## MVP boundary

- Cadence: once daily at first, not 3x/day.
- Volume: collect roughly 20-30 candidate posts.
- Topics: AI agents, AI governance, automation, model releases, operator workflows, enterprise AI, execution systems.
- Exclude: crypto, markets, politics, memes, generic AI hype.
- Output: concise Telegram digest with source links, why it matters, and content angles for Ahmed.

## Extraction rule

For posts with images, extract both visible post text and readable image text before judging relevance.

## Implementation path

1. Use browser-based X collection from Ahmed-Mac/session where login state is reliable.
2. Save raw candidates to local JSONL with timestamp, author, URL, text, image OCR/text if available, engagement fields if visible, and screenshot path when useful.
3. Dedupe by URL/status id and near-duplicate text.
4. Score candidates by relevance, executive usefulness, and engagement where visible.
5. Generate one Telegram digest.
6. Run manually for 2-3 days before cron.

## Non-goals for MVP

- No paid X/API infrastructure yet.
- No 50k-impression hard filter until impressions are reliably extractable.
- No broad public posting automation.
- No JobZoom changes.

## Verification

A run is complete only when:

- At least 20 raw candidates are captured or a real X/login blocker is documented.
- Digest links resolve back to the source posts.
- Image-containing posts include image text when readable.
- Telegram delivery is confirmed.

## Next concrete step

Create a small manual runner that produces a sample JSONL + digest from one X session, then inspect quality before scheduling.
