---
description: "Skill graph pattern for multi-platform content production: 1 topic → 10 native posts via wikilinked markdown files"
type: reference
topics: [knowledge, linkedin-content]
updated: 2026-03-14
---

# Content Skill Graph Pattern

**Source:** @deronin_ on X (Mar 14, 2026)
**Relevance:** When Ahmed expands beyond LinkedIn (newsletter, X, etc.)

## Concept

30+ markdown files wired together with [[wikilinks]] that turn an AI agent into a full content team. One topic input → 10 platform-native outputs, each rethought for the platform (not reformatted).

## Structure

```
/content-skill-graph
├── index.md          — entry point, briefing, node map
├── platforms/        — x.md, linkedin.md, ig.md, tiktok.md
├── voice/            — brand-voice.md, platform-tone.md
├── engine/           — hooks.md, repurpose.md, scheduling.md
└── audience/         — builders.md, casual.md
```

## Key Principles

1. **Each file = one knowledge node** with wikilinks to related nodes
2. **index.md is a briefing, not a file list.** Contains: who you are, node map with context, execution instructions
3. **Platform files encode native rules:** angle, hook style, voice, structure, format, length, frequency
4. **1 input → 10 different outputs:** same topic, different thinking per platform
5. **Agent follows wikilinks automatically** to gather context

## Example: Inside x.md

"Use [[hooks]], contrarian hooks perform best here. Match [[brand-voice]] but more casual. Audience is [[builders]]. Write this FIRST, then expand for [[linkedin]]. See [[repurpose]]."

## Output Differentiation (Not Reformatting)

- X: contrarian thread, lowercase casual, step-by-step
- LinkedIn: personal narrative, professional tone, 1500 words
- Instagram: 7-slide carousel, visual-first, bold claim on slide 1
- TikTok: 45-sec raw screen recording script
- YouTube: SEO title + structured outline, 8-min format

## Applicability to Our System

**Current state:** LinkedIn only (1 platform), content engine live
**Trigger to activate:** When Ahmed wants to expand to X, newsletter, or other channels
**Related:** P2 in pending-opus-topics (Weekly Newsletter)

**What we'd build:**
- `voice/ahmed-voice.md` — writing style rules (exists in linkedin-writer skill)
- `engine/hooks.md` — hook formulas for Ahmed's audience
- `engine/repurpose.md` — 1 LinkedIn post → X thread, newsletter intro
- `audience/gcc-executives.md` — target audience profile and what resonates

**Quote:** "One flat file gives you a tool. A graph gives you a team."

---
*Links: [[../mocs/linkedin-content.md]] | [[../mocs/knowledge.md]] | [[content-strategy.md]]*
