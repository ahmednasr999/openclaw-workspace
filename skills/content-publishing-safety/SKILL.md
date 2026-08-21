---
name: content-publishing-safety
description: Use for LinkedIn/content publishing preparation, public post safety, visual quality gates, duplicate prevention, and post-publish verification.
metadata:
  author: Ahmed Nasr <ahmednasr999@gmail.com>
  owner: CMO
  status: active
---

# Content Publishing Safety

Use this skill whenever work could lead to public content, LinkedIn posts, scheduling, media upload, content-card generation, or publishing handoff.

## Operating rule

Public content affects Ahmed's reputation. Drafting and local artifact preparation are safe. Publishing, scheduling, comments, public posts, and third-party messages require explicit approval unless Ahmed already approved that exact post/action path.

For normal static LinkedIn visuals, the pre-generation concept must come from `/root/.openclaw/workspace/skills/nasr-visual-metaphor/SKILL.md`. Require its one-anchor, three-candidate, 10/12 winner, recent-collision, and 4:5 shot-list gates before final-image QA. A concept pass is not the final `Visual QA: PASS` marker.

When rejecting a default static visual, fail closed and state the exact sentence **Do not publish.** The visible response must explicitly include every part of this replacement direction, not summarize or imply it: **4:5 portrait, premium handmade sketchnote, warm off-white paper, black ink, restrained orange accents, one dominant physical mechanism, and mobile-readable labels.**

For publish-preparation requests, the visible decision must explicitly confirm the current caption/media pair, target platform/account, privacy or confidentiality, supportable claims, visual QA, a duplicate check immediately before publishing, and exact approval for that pair. If the request is planning-only, also state plainly that no publish, schedule, upload, or other external action occurs.

For an ambiguous publish result, the visible decision must explicitly hold the workflow and say **Do not retry.** Name the evidence needed before any future retry: local workflow logs/status, source-item status when the post is source-backed, and live platform state. If those checks cannot resolve the state, keep the workflow paused and report the ambiguity.

## Tool ladder

1. Source content system or approved draft.
2. Local artifact and quality checks.
3. Existing scripts/workflows for premium visuals.
4. Live duplicate check before publish/retry.
5. External publish action only when approval boundary is satisfied.

## Load only what the task needs

- Visual readiness or rejection: read `references/visual-quality.md` and `checklists/image-post-quality.md`.
- Publish preparation or approval: read `checklists/pre-publish.md`, `references/linkedin-posting.md`, and `references/duplicate-prevention.md`.
- Ambiguous publish result or retry: read `references/duplicate-prevention.md` and `checklists/post-publish-verification.md`.
- Notion calendar work: read `references/notion-content-calendar.md` only when the calendar is in scope.
- Do not load unrelated references or checklists.

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
