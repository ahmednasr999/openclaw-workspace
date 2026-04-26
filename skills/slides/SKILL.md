---
name: slides
description: Create, inspect, edit, or rebuild presentation slide decks (`.pptx`) with PptxGenJS, bundled layout helpers, and render/validation utilities. Use whenever a `.pptx` file is involved as input, output, or both, including building a new PowerPoint deck, recreating slides from screenshots/PDFs/reference decks, extracting content from an existing presentation, modifying slide content while preserving editable output, combining or splitting deck content, adding charts/diagrams/visuals, or diagnosing layout issues such as overflow, overlaps, and font substitution. Also use this skill when the user wants a deck to feel premium, luxury, executive, editorial, investor-grade, less template-like, or specifically like a designed product/UI system rather than a normal presentation.
---

# Slides

## Overview

Use PptxGenJS for slide authoring. Do not use `python-pptx` for deck generation unless the task is inspection-only. Keep editable output in JavaScript and deliver both the `.pptx` and the source `.js`.

Keep work in a task-local directory. Only copy final artifacts to the requested destination after render and validation pass.

This skill now has two layers:
- the **production pipeline**: intake, planning, JS authoring, rendering, XML editing, QA
- the **editorial system**: pattern selection, style tokens, anti-pattern rules, and premium/editorial quality guidance

Use both. The pipeline makes decks work. The editorial system makes them feel designed.

---

## Quick Reference

| Task | Default move |
|------|--------------|
| Read or extract deck content | `python -m markitdown deck.pptx` |
| Get visual overview fast | `python3 scripts/render_slides.py deck.pptx --output_dir rendered` then `python3 scripts/create_montage.py --input_dir rendered --output_file montage.png` |
| Create a new editable deck | Author in JavaScript with PptxGenJS |
| Edit an existing deck while preserving structure | Use the XML workflow in `references/minimax-editing.md` |
| Check layout safety | `python3 scripts/slides_test.py deck.pptx` and `python3 scripts/detect_font.py deck.pptx --json` |
| Raise visual quality | Load `references/slides-core-system.md` + relevant `pattern-*.md` files |
| Match a brand | Use `references/slides-brand-onboarding.md` + `references/slides-style-guide.md` |

Default split:
- **Inspection / extraction**: read, render, analyze existing deck
- **New deck creation**: build from scratch in JS
- **Existing-deck surgery**: unpack, edit, clean, repack through XML workflow

---

## Bundled Resources

- `assets/pptxgenjs_helpers/`: copy this into the deck workspace and import it locally instead of reimplementing helper logic. Default generated stubs should import from the safe helper layer first; optional advanced helpers live under `pptxgenjs_helpers/optional`.
- `scripts/slides_ingest.py`: import files/URLs into a task-local deck workspace with standard folders
- `scripts/slides_extract_sources.py`: convert imported sources into normalized Markdown/text where possible
- `scripts/slides_build_intake_manifest.py`: rebuild `planning/intake.json` and `planning/intake.md`
- `scripts/slides_plan_from_sources.py`: generate `deck_brief.md`, `slide_outline.json`, `content_map.md`, and `deck_spec.json`
- `scripts/slides_init_authoring_task.py`: copy helpers and create authoring stub, notes, and manifest from planning artifacts
- `scripts/render_slides.py`: rasterize `.pptx` or `.pdf` to per-slide PNGs
- `scripts/slides_test.py`: detect content that overflows the slide canvas
- `scripts/create_montage.py`: build a contact-sheet montage of rendered slides
- `scripts/detect_font.py`: report missing or substituted fonts as LibreOffice resolves them
- `scripts/ensure_raster_image.py`: convert SVG/EMF/HEIC/PDF-like assets into PNGs for quick inspection
- `references/pptxgenjs-helpers.md`: load only when you need helper API or dependency details

## What to borrow from strong HTML deck systems

Use these ideas here, but keep this lane PPTX-first:

- **Template-first authoring** beats blank-page authoring. Start from a known slide pattern and adapt it.
- **Starter decks** are better than empty stubs when the user wants speed. Favor a usable first pass with real structure.
- **Starter packs should shape the stub**, not just sit in metadata. The authoring stub should expose the pack's narrative and emphasis clearly.
- **Layout inventory matters**. Treat cover, agenda, metric, comparison, timeline, explainer, CTA, and closing as reusable primitives.
- **Theme audition is useful**, but in this lane it should mean token/palette swaps, not adopting an HTML runtime.
- **Do not fork into a parallel HTML deck system** unless the requested output is explicitly an HTML presentation.

---

## Editorial System Routing

For visual quality work, load these in order:

1. `references/slides-core-system.md`
2. `references/slides-style-guide.md`
3. `references/slides-anti-patterns.md`
4. relevant `references/pattern-*.md` files only

Available phase-1 pattern references:
- `references/pattern-cover.md`
- `references/pattern-section-divider.md`
- `references/pattern-agenda.md`
- `references/pattern-thesis-summary.md`
- `references/pattern-metric.md`
- `references/pattern-comparison.md`
- `references/pattern-process-timeline.md`
- `references/pattern-2-column-explainer.md`
- `references/pattern-closing.md`

Use `references/slides-brand-onboarding.md` when the deck should align to a client, product, or publication brand.

Brand-onboarding helper script:

```bash
python3 scripts/slides_brand_onboarding.py extracted-brand-signals.json --output planning/brand-token-proposal.md
```

Live website scan:

```bash
python3 scripts/slides_brand_onboarding.py --url https://example.com --output planning/brand-token-proposal.md
```

Browser-assisted extraction mode:

```bash
python3 scripts/slides_brand_onboarding.py --url https://example.com --browser --output planning/brand-token-proposal.md
```

Sandbox brand application:

```bash
python3 scripts/slides_apply_brand_example.py planning/brand-token-proposal.md --name "Brand Name" --output examples/brand-name-branded-showcase
```

One-shot brand demo workflow:

```bash
python3 scripts/slides_brand_demo.py --url https://example.com --name "Brand Name"
```

One-shot browser-assisted workflow:

```bash
python3 scripts/slides_brand_demo.py --url https://example.com --browser --name "Brand Name"
```

One-shot workflow with delivery-ready media copy:

```bash
python3 scripts/slides_brand_demo.py --url https://example.com --name "Brand Name" --copy-to-media
```

This workflow prints a `SUMMARY_JSON:` line with delivery-ready paths and an OpenClaw send hint.

Validation helper:

```bash
python3 scripts/slides_brand_onboarding_validate.py
python3 scripts/slides_apply_brand_example_validate.py
python3 scripts/slides_brand_demo_validate.py
```

### Example deck

Use the showcase example when you want a concrete visual reference for the new editorial patterns:

- `examples/editorial-pattern-showcase/deck.js`
- output deck: `examples/editorial-pattern-showcase/exports/slides-editorial-pattern-showcase.pptx`
- rendered previews: `examples/editorial-pattern-showcase/rendered/`
- quick scan montage: `examples/editorial-pattern-showcase/montage.png`

Current showcase coverage:
- cover
- section-divider
- agenda
- thesis-summary
- metric
- comparison
- 2-column-explainer
- process-timeline
- closing

Build it with:

```bash
cd examples/editorial-pattern-showcase
NODE_PATH=/root/.openclaw/workspace/skills/slides/node_modules node deck.js
```

---

## Legacy Design References To Keep Using

These remain active and useful:

- `references/minimax-design-system.md`: named palettes, style recipes, typography, spacing. Use when choosing a concrete palette and presentation-wide visual style.
- `references/minimax-slide-types.md`: legacy 5-type slide planning reference. Keep using for compatibility until planning scripts are upgraded to the new editorial pattern model.
- `references/minimax-pitfalls.md`: QA process and critical PptxGenJS pitfalls. Load before QA and delivery.
- `references/minimax-editing.md`: XML-based workflow for editing existing PPTX files.
- `references/slides-planning-brief.md`: planning artifact contract for intake materials.

---

## Phase-1 Compatibility Rule

The new editorial pattern system is the preferred design language, but current planning scripts may still emit legacy slide types from `minimax-slide-types.md`.

Until scripts are upgraded, map them like this:

| Editorial pattern | Legacy type |
|---|---|
| cover | Cover Page |
| section-divider | Section Divider |
| agenda | Table of Contents |
| thesis-summary | Content Page |
| metric | Content Page |
| comparison | Content Page |
| closing | Summary Page |

This lets you design with the new patterns while keeping current tooling stable.

---

## Workflow

### Creating a New Deck

1. **Research and requirements**: understand topic, audience, purpose, tone.
2. **Ingest sources into a task-local workspace** when source materials are involved:
   - `python3 scripts/slides_ingest.py <task_dir> <source1> [<source2> ...]`
   - `python3 scripts/slides_extract_sources.py <task_dir>`
3. **Build planning artifacts** before slide design when using imported sources:
   - load `references/slides-planning-brief.md`
   - run `python3 scripts/slides_plan_from_sources.py <task_dir>`
   - inspect `planning/deck_spec.json` before authoring
4. **Initialize the authoring workspace**:
   - run `python3 scripts/slides_init_authoring_task.py <task_dir>`
   - run task-local authoring with `NODE_PATH=/root/.openclaw/workspace/skills/slides/node_modules node authoring/deck.js`
5. **Confirm the minimum deck spec**:
   - objective
   - audience
   - tone
   - aspect ratio
   - starter pack
   - image policy
   - polish level
6. **Load editorial system references**:
   - always load `references/slides-core-system.md`
   - load `references/slides-style-guide.md`
   - load `references/slides-anti-patterns.md`
   - load only the relevant `pattern-*.md` files for the current slides
6. **Choose palette and recipe**:
   - load `references/minimax-design-system.md`
   - choose palette and style recipe that fit topic and audience
7. **Classify each slide before authoring**:
   - use editorial patterns first
   - fall back to legacy type mapping only where tooling still requires it
8. **Set slide size** up front. Default to 16:9 (`LAYOUT_WIDE`) unless the source material clearly uses another aspect ratio.
9. **Build the deck** in JavaScript with explicit theme font, stable spacing, and editable native elements when practical.
10. **Render and review** with `render_slides.py`, then build a montage with `create_montage.py`.
11. **Run QA**:
   - load `references/minimax-pitfalls.md`
   - use `references/slides-anti-patterns.md` for editorial QA
   - verify page number badges where the template system expects them
12. **Deliver** the `.pptx`, the authoring `.js`, and any generated assets required to rebuild the deck.

### Workflow state model

Use these states explicitly when debugging or handing work off:
- intake
- extraction
- planning
- authoring-init
- build
- render
- QA
- delivery

If a stage fails, diagnose that stage first instead of treating the whole lane as one opaque workflow.

### Delivery contract

Default delivery bundle:
- final `.pptx`
- source `deck.js`
- `authoring_manifest.json`
- `authoring_notes.md`
- rendered review assets when useful
- planning artifacts when traceability matters

Load `references/slides-troubleshooting.md` when the workflow breaks or a stage is ambiguous.

### Editing an Existing Deck

1. Load `references/minimax-editing.md`.
2. Copy source to `template.pptx`, extract with `markitdown`, plan slide mapping.
3. Unpack → edit XML → clean orphaned files → repack. Always write to `/tmp/` first.
4. Validate with `render_slides.py` and `slides_test.py`.

---

## Theme Object Contract

The compile script passes a theme object with these exact keys:

| Key | Purpose | Example |
|-----|---------|---------|
| `theme.primary` | darkest color, titles | `"22223b"` |
| `theme.secondary` | dark accent, body text | `"4a4e69"` |
| `theme.accent` | mid-tone accent | `"9a8c98"` |
| `theme.light` | light accent | `"c9ada7"` |
| `theme.bg` | background color | `"f2e9e4"` |

Colors are 6-char hex without `#`.

Use `references/slides-style-guide.md` to think semantically, then map the chosen palette into the theme object required by the build pipeline.

---

## Authoring Rules

### Editorial Systems Mode v2

Use when the benchmark is a product page, design manual, operating model, technical poster, system artifact, or editorial composition rather than a conventional presentation template.

Rules:
- typography is part of the visual engine
- build from a grid first
- use a small reusable component family
- accent is restrained and intentional
- one focal element per slide
- composition should feel deliberate, not improvised

### Premium Executive Mode v2

Use when the user wants premium, luxury, board-level, founder-grade, investor-ready, or explicitly says the current output feels too plain, too corporate, too templated, or not high-end enough.

Rules:
- one dominant focal element
- avoid equal-weight layouts
- prefer editorial composition over consultant composition
- create a real hero moment every 2 to 3 slides
- subtraction beats decorative accumulation
- charts and comparisons should feel art-directed, not default analytics objects

### Default quality bar

Do not create boring slides.

Minimum standard:
- every slide has a clear visual idea
- one color system dominates with restrained accent use
- layouts vary across the deck
- hierarchy is obvious at a glance
- text-heavy slides compensate with stronger composition

### PptxGenJS and production rules

- set theme fonts explicitly
- use `autoFontSize`, `calcTextBox`, and related helpers, not PptxGenJS `fit` / `autoFit`
- use bullet options, not literal bullet characters
- use `imageSizingCrop` or `imageSizingContain` instead of built-in image sizing
- use `latexToSvgDataUri()` for equations and `codeToRuns()` for syntax-highlighted blocks
- prefer native PowerPoint charts for simple editable charts
- use external SVG when PptxGenJS cannot express the diagram well
- include both `warnIfSlideHasOverlaps(slide, pptx)` and `warnIfSlideElementsOutOfBounds(slide, pptx)` in generated or substantially edited decks
- `createSlide()` must be synchronous
- never reuse option objects across PptxGenJS calls
- body text and captions should not use bold by default

---

## QA

### Technical QA

- `python3 scripts/slides_test.py deck.pptx`
- `python3 scripts/detect_font.py deck.pptx --json`
- `python -m markitdown deck.pptx`
- render + montage review

### Editorial QA

Ask slide by slide:
- what is the focal point?
- what pattern is this slide using?
- is one element clearly dominant?
- does this look editorial or template-like?
- can one more element be removed?
- is the accent restrained enough?

If the slide feels neat but safe, it is probably still under-designed.

---

## Recreate Or Edit Existing Slides

- render the source deck or reference PDF first
- match the original aspect ratio before rebuilding layout
- preserve editability where possible
- use `ensure_raster_image.py` for odd formats before placement
- use `references/minimax-editing.md` for XML-based editing of templates

---

## Validation Commands

```bash
# Build a task-local intake package from sources
python3 scripts/slides_ingest.py work/task-001 source.pdf notes.md https://example.com/page
python3 scripts/slides_extract_sources.py work/task-001
python3 scripts/slides_build_intake_manifest.py work/task-001
python3 scripts/slides_plan_from_sources.py work/task-001
python3 scripts/slides_init_authoring_task.py work/task-001
NODE_PATH=/root/.openclaw/workspace/skills/slides/node_modules node work/task-001/authoring/deck.js

# Render slides to PNGs for review
python3 scripts/render_slides.py deck.pptx --output_dir rendered

# Build a montage for quick scanning
python3 scripts/create_montage.py --input_dir rendered --output_file montage.png

# Check for overflow beyond the original slide canvas
python3 scripts/slides_test.py deck.pptx

# Detect missing or substituted fonts
python3 scripts/detect_font.py deck.pptx --json

# Extract text for content QA
python -m markitdown deck.pptx

# Check for leftover placeholder text
python -m markitdown deck.pptx | grep -iE "xxxx|lorem|ipsum|placeholder|this.*(page|slide).*layout"
```

Load `references/pptxgenjs-helpers.md` when you need helper API summary or dependency details.
