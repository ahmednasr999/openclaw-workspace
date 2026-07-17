---
name: content-publishing-safety
description: Use for LinkedIn/content publishing preparation, public post safety, visual quality gates, duplicate prevention, and post-publish verification.
metadata:
  owner: CMO
  status: active
---

# Content Publishing Safety

Use this skill whenever work could lead to public content, LinkedIn posts, scheduling, media upload, content-card generation, or publishing handoff.

## Operating rule

Public content affects Ahmed's reputation. Drafting and local artifact preparation are safe. Publishing, scheduling, comments, public posts, and third-party messages require explicit approval unless Ahmed already approved that exact post/action path.

## Tool ladder

1. Source content system or approved draft.
2. Local artifact and quality checks.
3. Existing scripts/workflows for premium visuals.
4. Live duplicate check before publish/retry.
5. External publish action only when approval boundary is satisfied.

## References

- `references/linkedin-posting.md` - LinkedIn publish rules and Composio gotchas.
- `references/visual-quality.md` - premium visual quality source and rejection rules.
- `references/notion-content-calendar.md` - content calendar source-of-truth.
- `references/duplicate-prevention.md` - live/local duplicate prevention before external writes.

## Checklists

- `checklists/pre-publish.md` - before requesting approval or publishing.
- `checklists/image-post-quality.md` - before sending visual as ready.
- `checklists/post-publish-verification.md` - after publishing or retrying.

## Done means

- Draft/caption and media are matched.
- Approval boundary is satisfied.
- Visual or media passed quality gate if expected.
- Publish/retry checked for duplicates.
- Final live state or staged artifact was inspected.

## Learned Improvements

### 2026-06-27 - Weekly Skill Tune-Up

**Reviewed lessons:**
- 2026-06-26, LinkedIn visual defaults conflicted across gates and allowed a bad dark-card visual to reach a live post.
- 2026-06-26, the corrected visual still failed because it looked like a clean vector flow diagram instead of a handmade sketchnote.
- 2026-06-26, daily LinkedIn publishing needed a hard `Visual QA: PASS - reference-checked handmade sketchnote` marker tied to the actual asset.

**Improvement recommendation:**
Before any normal Ahmed LinkedIn static visual is approved, scheduled, published, or described as ready, fail closed unless the actual image has been inspected against the handmade sketchnote reference and the source record carries `Visual QA: PASS - reference-checked handmade sketchnote`. Auto-fail polished vector-like flows, deterministic diagrams, generic dark tech cards, and assets that only match the palette or topic. Treat the marker as proof of visual review, not as a substitute for duplicate checks, approval boundaries, or post-publish verification.

**Checklist status:** No `eval/checklist.md` exists for this skill. Use `checklists/image-post-quality.md`, `checklists/pre-publish.md`, `checklists/post-publish-verification.md`, and `references/visual-quality.md` as the active evaluation checklist.
