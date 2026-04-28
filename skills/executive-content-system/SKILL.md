---
name: executive-content-system
description: Use this for Ahmed Nasr executive LinkedIn content strategy, CMO content workflow improvements, post drafts, content matrices, voice calibration, post scoring, LinkedIn profile positioning, carousel or premium visual planning, and adapting creator-style social-media systems into Ahmed's GCC executive brand. Trigger whenever the user asks to write, improve, score, plan, repurpose, or systematize LinkedIn/executive content for Ahmed, especially if a post/image/carousel/analytics/profile/content-calendar workflow is involved.
metadata:
  owner: CMO
  source_inspiration: charlie947/social-media-skills audit
  status: active
---

# Executive Content System

Use this skill to turn Ahmed's content work into a disciplined executive publishing system, not generic creator output.

This skill adapts the useful patterns from `charlie947/social-media-skills` into OpenClaw and Ahmed's CMO workflow:
- voice files as source of truth
- content matrix ideation
- angle-first post planning
- performance-backed scoring
- visual routing for image/carousel assets
- approval gates before external publishing

Do not copy Charlie Hills examples, tone, pinned-comment humour, or clickbait defaults. Ahmed's lane is senior GCC executive positioning.

## Source-of-truth files

Read the most relevant files before drafting or changing workflow:

- `/root/.openclaw/workspace/USER.md` for Ahmed profile and preferences
- `/root/.openclaw/workspace/MEMORY.md` for durable content rules
- `/root/.openclaw/workspace/skills/content-claw/SKILL.md` for current CMO rules
- `/root/.openclaw/workspace-cmo/content-strategy.md` for pillars and publishing workflow
- `/root/.openclaw/workspace-cmo/references/content-performance.json` when scoring against performance
- `/root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py` for premium single-image card workflows

If a file outside the workspace cannot be read with the `read` tool, use `exec` with a targeted `sed`/`python` command. Do not treat tool-scope errors as evidence that the file is missing.

## Ahmed's executive content position

Default positioning:
- GCC digital transformation executive
- healthcare transformation and digital health
- PMO, governance, execution control, and transformation delivery
- fintech, payments, and GCC market execution
- AI automation systems with practical operating-model implications
- next executive role visibility without sounding like a job seeker

Default audience:
- GCC executives
- transformation leaders
- healthcare and fintech leaders
- board/PMO/strategy stakeholders
- recruiters and hiring managers for VP/C-suite roles

Default voice:
- direct, practical, executive, grounded
- decision-oriented rather than inspirational
- specific examples over broad claims
- no generic motivational content
- no creator-bro clickbait
- no em dashes
- LinkedIn posts should end with a question or CTA unless there is a strong reason not to

## Workflow selector

First classify the request:

| Request type | Use this path |
|---|---|
| Create weekly ideas or topic bank | Content matrix |
| Draft a LinkedIn post | Post writer |
| Improve or critique a post | Post scorer |
| Decide visual format | Visual router |
| Build carousel/infographic plan | Carousel/infographic brief |
| Profile positioning | Profile optimizer |
| Analyze performance/export | Analytics review |
| Improve the system itself | Workflow improvement |

Ask a question only if one missing decision blocks safe progress. Otherwise make a reasonable assumption and state it briefly.

## Content matrix path

Use for topic planning, weekly calendars, or “what should I post?” requests.

Inputs:
- time horizon: today, this week, month, campaign
- active pillar if supplied
- target outcome: engagement, executive positioning, recruiter visibility, thought leadership, lead generation

Default pillars from CMO strategy:
1. Digital Transformation Insights
2. PMO and Leadership
3. GCC Tech Ecosystem
4. Personal Career Stories

Formats to rotate:
- contrarian executive opinion
- field lesson from delivery
- framework/checklist
- failure pattern
- boardroom question
- regional trend reaction
- story-to-lesson
- one sharp operating rule

Output a table:

```markdown
| Priority | Pillar | Format | Hook | Angle | Evidence needed | Visual fit | Why it matters |
```

Keep ideas specific enough to draft immediately. Avoid vague topics like “AI in healthcare”. Prefer “Why 92% model accuracy can still fail adoption in hospitals”.

## Post writer path

Before writing, identify:
- pillar
- target audience
- angle
- evidence/example
- CTA
- visual expectation

If the user provides only a topic, propose 2-3 angles first and recommend one. For low-risk requests, draft the recommended version immediately after the angles.

Draft rules:
- 120-250 words by default unless asked otherwise
- mobile-friendly short paragraphs
- one clear hook in the first line
- concrete executive insight by line 3
- one story, example, number, or operational pattern when available
- no hashtags unless requested or existing CMO workflow requires them
- end with a question or CTA
- never invent Ahmed achievements, metrics, roles, or company facts

Output:

```markdown
## Recommended angle
[one sentence]

## Draft
[post text]

## Visual recommendation
[none / premium statement card / chart card / carousel / executive photo / infographic]

## Notes
- [evidence needed or risk]
- [why this fits Ahmed]
```

## Post scorer path

Use performance where available. Prefer `/root/.openclaw/workspace-cmo/references/content-performance.json` for historical local signals.

Score 5 dimensions, each out of 10:
1. Hook strength
2. Executive credibility
3. Value density
4. Voice fit
5. Publish readiness

Output:

```markdown
## Score
[XX]/50 - [verdict]

| Dimension | Score | Reason |
|---|---:|---|

## Top fixes
1. [specific change]
2. [specific change]
3. [specific change]

## Publish decision
[Ready / Revise / Needs evidence / Needs visual / Do not publish]
```

Rules:
- Do not reward clickbait if it weakens executive trust.
- A draft with generic AI language cannot score above 35.
- A draft with invented or unsupported claims must be marked “Needs evidence” or “Do not publish”.
- If an image was expected, publishing text-only is not ready unless Ahmed explicitly approves that downgrade.

## Visual router path

Choose the artifact type based on content structure:

| Content pattern | Visual recommendation |
|---|---|
| One sharp claim | Premium statement card |
| Framework, maturity model, operating model | Chart/card or carousel |
| Comparison or trade-off | Split card or 2x2 matrix |
| Data/statistic | Metric card with source note |
| Career story | Text-first post or executive photo card |
| Multi-step method | Carousel |
| Abstract concept | Avoid abstract art. Use a concrete executive/business scene |

Default single-image path:
- use `/root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py`
- premium, executive, dark/cinematic, topic-relevant
- do not use text-only publishing when an image is expected

Image quality rules:
- background must make sense before reading text
- no generic AI glow, random geometry, meaningless robots, or stock-photo clichés
- typography must be readable on mobile
- Ahmed Nasr lockup should stay consistent when used
- regenerate if text is clipped or background fights readability

## Carousel/infographic brief path

Do not generate final assets before a brief is accepted unless Ahmed explicitly asks for immediate generation.

Brief format:

```markdown
## Carousel brief
- Goal:
- Audience:
- Slide count:
- Core narrative:
- Slide outline:
  1. [hook]
  2. [point]
  3. [point]
- Visual system:
- Approval question:
```

Executive carousel defaults:
- 6-8 slides
- 1080x1350 if image carousel
- boardroom-grade typography
- one idea per slide
- narrative flow: shift -> risk -> rule -> implication -> action -> question

## Profile optimizer path

Use when improving LinkedIn profile, About section, headline, Featured section, or recruiter-facing positioning.

Default goal: make Ahmed credible for GCC VP/C-suite transformation roles without sounding desperate or over-branded.

Output sections:
- headline options
- About section
- Featured section plan
- experience positioning notes
- banner/profile visual prompts if requested

Never fabricate credentials, titles, dates, employers, or metrics. For CV/career specifics, read master CV data before asserting facts.

## Analytics review path

Use when reviewing LinkedIn analytics, post history, content-performance JSON, or weekly CMO reports.

Look for:
- hook styles that perform
- visual vs text-only difference
- pillar performance
- posting-day/time patterns if data exists
- comments/reactions quality, not only counts
- repeatable formats worth codifying

If data is thin, say so. Do not fake statistically significant conclusions from a tiny sample.

## Workflow improvement path

Use when Ahmed asks to adapt a repo, improve the CMO system, or codify repeated work.

Process:
1. Identify reusable pattern.
2. Compare to existing CMO workflow.
3. Keep one owner, usually CMO/content-claw.
4. Preserve approval gates for public posting and third-party messages.
5. Add the smallest durable fix: rule, checklist, script, skill, eval, or cron.
6. Verify by reading the resulting file or running the smallest available validation.

## Approval and safety gates

Never without explicit approval:
- publish to LinkedIn
- send LinkedIn messages/comments
- email anyone
- change Notion publish status to a live/external state unless workflow already permits it

Before claiming content work is complete, verify the actual artifact:
- draft text exists
- image exists if expected
- calendar/status updated if requested
- live post URL and rendered content checked if published

## Reference files

Load only when needed:
- `references/brand-archetype.md` for Ahmed's Operator/Educator/Contrarian mix, tone, signature phrases, and words to avoid
- `references/adaptation-notes.md` for what was adapted from charlie947/social-media-skills and what was rejected
- `references/scoring-rubric.md` for deeper post scoring
- `references/visual-router.md` for visual format decisions
