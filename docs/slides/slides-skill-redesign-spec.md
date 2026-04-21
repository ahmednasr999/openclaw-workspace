# Slides Skill Redesign Spec

## Purpose

Redesign the `slides` skill from a capable PPTX production toolkit into a tighter editorial system with explicit taste rules, pattern grammars, and a style-token layer.

This spec borrows the strongest structural ideas from `diagram-design` and adapts them to slide authoring rather than diagram authoring.

---

## Executive summary

The current `slides` skill is strong at:
- intake and planning
- JS/PptxGenJS authoring
- helper bundles and validation
- XML editing workflow for existing decks

The current `slides` skill is weaker at:
- encoding visual taste as reusable rules
- separating global design logic from page-pattern logic
- enforcing anti-patterns
- using a clean semantic token system
- constraining generation through explicit page grammars

### Redesign goal

Move from:
- toolkit + planning + rendering

to:
- editorial slide system + page-pattern grammar + tokenized visual language + existing build/render QA pipeline

---

## Design principles to adopt

### 1. Encode taste as rules, not adjectives

Avoid asking the model to make slides feel:
- premium
- luxury
- board-ready
- modern

without load-bearing constraints.

Replace vague style requests with:
- anti-patterns
- page grammars
- focal rules
- spacing constraints
- typography roles
- semantic color roles
- information density rules

### 2. Separate global rules from page-pattern rules

Global editorial system rules should live in one place.

Pattern-specific layout logic should live in separate pattern references and load only when relevant.

### 3. Keep context small

Do not load the entire slide universe for every deck.

Default load should be:
- `SKILL.md`
- one core design-system reference
- one pattern reference at a time
- optional brand/style guide

### 4. Constrain before generating

Every slide should be classified into exactly one page pattern before layout is generated.

Pattern selection should happen before slide rendering.

### 5. Style should be tokenized

No slide pattern should define raw colors inline unless for a deliberate exception.

All patterns should consume semantic roles from a single style guide.

---

## Recommended new information architecture

```text
slides/
├── SKILL.md
├── references/
│   ├── slides-core-system.md
│   ├── slides-style-guide.md
│   ├── slides-brand-onboarding.md
│   ├── slides-anti-patterns.md
│   ├── pattern-cover.md
│   ├── pattern-section-divider.md
│   ├── pattern-agenda.md
│   ├── pattern-thesis-summary.md
│   ├── pattern-metric.md
│   ├── pattern-comparison.md
│   ├── pattern-process-timeline.md
│   ├── pattern-2-column-explainer.md
│   ├── pattern-full-bleed-visual.md
│   ├── pattern-closing.md
│   ├── slides-planning-brief.md
│   ├── minimax-editing.md
│   ├── minimax-pitfalls.md
│   └── pptxgenjs-helpers.md
├── examples/
│   ├── cover-01/
│   ├── metric-01/
│   ├── comparison-01/
│   ├── timeline-01/
│   └── closing-01/
├── scripts/
└── assets/
```

---

## Core references and their responsibilities

## 1. `slides-core-system.md`

This becomes the visual and editorial operating system.

It should define:
- deck philosophy
- hierarchy rules
- focal-point rule
- information density targets
- asymmetry vs symmetry guidance
- typography-first composition rules
- slide sequencing rules
- rhythm rules across a deck
- page classification logic
- what makes a slide feel premium/editorial/systemic

### Must include
- “one dominant focal element” rule
- “equal-weight layouts are suspicious” rule
- “remove one element before adding one” rule
- “cards are not default structure” rule
- “slides should read as designed artifacts, not template instances” rule

---

## 2. `slides-style-guide.md`

Single source of truth for semantic tokens.

### Color roles
Use semantic names like:
- `bg`
- `surface`
- `surface-2`
- `text-primary`
- `text-secondary`
- `text-soft`
- `rule`
- `rule-strong`
- `accent`
- `accent-soft`
- `warning`
- `success`
- `data-link`

### Typography roles
Use semantic names like:
- `display`
- `title`
- `section`
- `body`
- `caption`
- `meta`
- `data`
- `eyebrow`

### Spacing and geometry roles
Use tokens like:
- `grid-unit`
- `page-margin-x`
- `page-margin-y`
- `module-gap`
- `card-radius`
- `rule-weight`

### Why
This lets all patterns inherit a coherent system instead of embedding local style decisions.

---

## 3. `slides-brand-onboarding.md`

A first-run style gate modeled on the strongest part of `diagram-design`.

### Purpose
Before generating the first client-facing deck in a new task or project:
- check if the style guide is still on default tokens
- ask whether to:
  - use default
  - infer from website / brand source
  - paste tokens manually

### Workflow
- fetch brand source
- extract rough palette and typography
- map to semantic slide roles
- show proposed diff
- only write after approval

### Important constraint
Brand extraction is a proposal system, not truth.
Always preview before applying.

---

## 4. `slides-anti-patterns.md`

This file should explicitly define what bad slides look like.

### Add anti-patterns such as
- title plus bullets on white with no composition
- equal-sized cards across the page without hierarchy
- dashboard-like micro-panels on every slide
- too many outlines and small boxes
- weak focal point
- too many accent colors
- heavy shadows and decorative gloss
- symmetrical layouts where no true comparison exists
- “consulting template sludge”
- repeated layout structure slide after slide
- charts dropped in with no art direction
- excessive use of bold in body copy
- decorative icons without information value

### Role
This file should be loaded in planning and again in QA.

---

## Page-pattern system

Each slide must be classified into exactly one pattern.

Recommended starting pattern set:
- Cover
- Section Divider
- Agenda
- Thesis / Summary
- Metric / KPI
- Comparison / Decision
- Process / Timeline
- Two-Column Explainer
- Full-Bleed Visual / Statement
- Closing / Call to Action

This is intentionally smaller and more editorial than the current 5 high-level page types.

---

## Pattern contract

Every `pattern-*.md` file should follow the same schema.

### Required sections
1. Best for
2. Use when
3. Don’t use when
4. Required content inputs
5. Optional content inputs
6. Layout logic
7. Hierarchy rules
8. Focal-point rule
9. Visual treatment guidance
10. Common anti-patterns
11. Example structures
12. QA checklist

---

## Example pattern definitions

## `pattern-cover.md`

Define:
- when to use
- acceptable structures
- title/subtitle/meta hierarchy
- hero-image or field treatment rules
- asymmetry preference
- anti-patterns like logo soup, centered safe layouts by default, weak title scale

## `pattern-thesis-summary.md`

Define:
- use for executive takeaway slides
- required inputs:
  - thesis
  - 2 to 4 supporting statements
  - optional proof point
- layout rule:
  - one dominant thesis block
  - support items secondary
- anti-patterns:
  - all points equal weight
  - summary slide as bullet dump

## `pattern-metric.md`

Define:
- use for KPI / performance story
- required inputs:
  - metric
  - label
  - time context
  - implication
- layout rule:
  - metric is hero
  - explanation is subordinate
- anti-patterns:
  - too many metrics on one slide
  - chart dominating when the number is the story

## `pattern-comparison.md`

Define:
- use for decision, option tradeoff, before/after
- rule:
  - symmetry only when the decision genuinely requires symmetry
  - otherwise recommendation side should dominate
- anti-patterns:
  - both sides visually equal when recommendation is already known

## `pattern-process-timeline.md`

Define:
- use for sequence, plan, roadmap
- rule:
  - strong directional flow
  - time anchors clear
  - no gratuitous icons
- anti-patterns:
  - 8 tiny steps in one row
  - visual uniformity with no phase hierarchy

---

## Changes to existing planning flow

Current planning is strong operationally. Keep it.

But change the semantic output.

### Current planning outputs to preserve
- `deck_brief.md`
- `slide_outline.json`
- `content_map.md`

### New requirement
`slide_outline.json` should classify each slide into a new editorial page pattern, not just a generic page type.

Example:
```json
{
  "slide_number": 4,
  "pattern": "metric",
  "purpose": "Show the single KPI that justifies the recommendation",
  "focal_element": "72% automation coverage",
  "supporting_content": [
    "baseline was 31%",
    "achieved in 9 months",
    "reduces handoff delay"
  ]
}
```

### Add these planning fields
- `pattern`
- `focal_element`
- `dominant_message`
- `density_target`
- `visual_risk_notes`

---

## Changes to `SKILL.md`

`SKILL.md` should become a routing and orchestration layer, not a large all-in-one instruction dump.

### It should do these things
- explain when to use the skill
- route to relevant references
- enforce first-run style gate
- require per-slide pattern classification
- require use of the style guide
- require anti-pattern review before delivery
- preserve existing build and QA commands

### It should stop trying to carry
- all taste rules inline
- all page-type detail inline
- all design-system detail inline

Those belong in dedicated references.

---

## Recommended migration plan

## Phase 1 - structure without behavior change

Create new files:
- `slides-core-system.md`
- `slides-style-guide.md`
- `slides-brand-onboarding.md`
- `slides-anti-patterns.md`
- first 6 pattern files

Update `SKILL.md` to route to them.

Do not change scripts yet.

### Success criteria
- references exist
- routing is clear
- current slide build pipeline still works

---

## Phase 2 - planning upgrade

Update planning workflow so `slide_outline.json` includes:
- pattern
- focal element
- dominant message
- density target

Potential targets:
- `scripts/slides_plan_from_sources.py`
- authoring notes generated by `slides_init_authoring_task.py`

### Success criteria
- slide plans classify slides with richer editorial semantics
- authoring stubs surface those semantics cleanly

---

## Phase 3 - example library

Add high-quality examples for each major pattern.

### Why
Examples are part of the product, not documentation fluff.
They anchor quality better than abstract prose alone.

Recommended first examples:
- cover
- thesis summary
- metric
- comparison
- process timeline
- closing

### Success criteria
- each pattern has at least one canonical example
- examples are visually distinct but system-consistent

---

## Phase 4 - brand onboarding support

Add optional tooling to support style extraction and token proposal.

Important: this should remain approval-gated.

### Success criteria
- first-run style gate works
- default and branded modes are both supported
- token changes are localized to one file

---

## QA model changes

Current technical QA remains necessary.
Keep:
- render review
- montage review
- overflow checks
- font checks
- placeholder checks

### Add editorial QA pass
For each slide ask:
- what is the focal point?
- is one element clearly dominant?
- what pattern is this slide using?
- does the layout match the pattern grammar?
- is there unnecessary symmetry?
- is the accent restrained?
- does this feel designed or merely arranged?
- can one element be removed to make the slide stronger?

### Add deck-level QA pass
Ask:
- does the deck have rhythm?
- are there enough hero moments?
- are 2 to 3 adjacent slides too structurally similar?
- does the visual system remain coherent across patterns?

---

## What to preserve from the current skill

Do not throw away the strong parts.

Preserve:
- JS/PptxGenJS as default authoring path
- intake and extraction scripts
- planning artifact workflow
- authoring task initialization
- XML editing workflow for existing decks
- render + montage + overflow + font QA
- helper bundle strategy

The redesign should upgrade the editorial operating layer, not replace the production pipeline.

---

## Recommended first implementation moves

If doing the redesign incrementally, start here:

1. Create `slides-style-guide.md`
2. Create `slides-anti-patterns.md`
3. Create 6 pattern files
4. Refactor `SKILL.md` routing
5. Upgrade planning output to include `pattern` and `focal_element`

This yields most of the gain quickly without destabilizing the build flow.

---

## Final recommendation

The `slides` skill should evolve into:
- a production-grade PPTX pipeline
- wrapped in a constrained editorial system

The key shift is:

**stop treating “premium” as a rendering request, and start treating it as a system of rules, pattern choices, and anti-pattern avoidance.**
