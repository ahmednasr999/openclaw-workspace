---
name: slides
description: Create and edit presentation slide decks (`.pptx`) with PptxGenJS, bundled layout helpers, and render/validation utilities. Use when tasks involve building a new PowerPoint deck, recreating slides from screenshots/PDFs/reference decks, modifying slide content while preserving editable output, adding charts/diagrams/visuals, or diagnosing layout issues such as overflow, overlaps, and font substitution.
---

# Slides

## Overview

Use PptxGenJS for slide authoring. Do not use `python-pptx` for deck generation unless the task is inspection-only; keep editable output in JavaScript and deliver both the `.pptx` and the source `.js`.

Keep work in a task-local directory. Only copy final artifacts to the requested destination after rendering and validation pass.

## Bundled Resources

- `assets/pptxgenjs_helpers/`: Copy this folder into the deck workspace and import it locally instead of reimplementing helper logic.
- `scripts/render_slides.py`: Rasterize a `.pptx` or `.pdf` to per-slide PNGs.
- `scripts/slides_test.py`: Detect content that overflows the slide canvas.
- `scripts/create_montage.py`: Build a contact-sheet style montage of rendered slides.
- `scripts/detect_font.py`: Report missing or substituted fonts as LibreOffice resolves them.
- `scripts/ensure_raster_image.py`: Convert SVG/EMF/HEIC/PDF-like assets into PNGs for quick inspection.
- `references/pptxgenjs-helpers.md`: Load only when you need API details or dependency notes.

## Design System

Load these references when creating decks from scratch or when visual quality matters:

- `references/minimax-design-system.md`: **18 color palettes** (with names, hex values, styles, use cases), font reference, **4 style recipes** (Sharp/Soft/Rounded/Pill with exact spacing tokens), typography scale, and spacing scale. Load before choosing colors or visual style.
- `references/minimax-slide-types.md`: **5 page type templates** with layout options, font hierarchies, content elements, and per-type workflows. Load when planning the slide outline.
- `references/minimax-pitfalls.md`: QA process and critical PptxGenJS pitfalls. Load before QA and delivery.
- `references/minimax-editing.md`: XML-based workflow for editing existing PPTX files (unpack → edit → repack). Load when modifying an existing deck rather than creating from scratch.

## Workflow

### Creating a New Deck

1. **Research & Requirements** — Understand topic, audience, purpose, and tone.
2. **Select Color Palette** — Load `references/minimax-design-system.md`. Choose one of the 18 named palettes that fits the topic and audience. Map the 5 palette colors to the theme object: `primary`, `secondary`, `accent`, `light`, `bg`.
3. **Select Style Recipe** — Still in `references/minimax-design-system.md`. Choose one style recipe (Sharp & Compact / Soft & Balanced / Rounded & Spacious / Pill & Airy) that fits the presentation tone. Apply its spacing and corner-radius tokens consistently throughout.
4. **Plan Slide Outline** — Load `references/minimax-slide-types.md`. Classify **every slide as exactly one of 5 types: Cover, TOC, Section Divider, Content, Summary**. Plan content and layout per slide. Ensure visual variety — do NOT repeat the same layout across slides.
5. **Set slide size** up front. Default to 16:9 (`LAYOUT_WIDE`) unless the source material clearly uses another aspect ratio.
6. **Copy `assets/pptxgenjs_helpers/`** into the working directory and import the helpers from there.
7. **Build the deck** in JavaScript with an explicit theme font, stable spacing, and editable PowerPoint-native elements when practical.
8. **Render & review** with `render_slides.py`, build a montage with `create_montage.py`, and fix layout issues.
9. **Run QA** — Load `references/minimax-pitfalls.md`. Extract text with `python -m markitdown output.pptx`, check for placeholder text, verify page number badges (required on all slides except Cover). Run `slides_test.py` for overflow. Run `detect_font.py` for font substitutions.
10. **Deliver** the `.pptx`, the authoring `.js`, and any generated assets required to rebuild the deck.

### Editing an Existing Deck

1. Load `references/minimax-editing.md` for the full XML-based workflow.
2. Copy source to `template.pptx`, extract with `markitdown`, plan slide mapping.
3. Unpack (zipfile) → edit XML → clean orphaned files → repack. Always write to `/tmp/` first.
4. Validate with `render_slides.py` and `slides_test.py`.

## Theme Object Contract

The compile script passes a theme object with these **exact keys** — never use other names:

| Key | Purpose | Example |
|-----|---------|---------|
| `theme.primary` | Darkest color, titles | `"22223b"` |
| `theme.secondary` | Dark accent, body text | `"4a4e69"` |
| `theme.accent` | Mid-tone accent | `"9a8c98"` |
| `theme.light` | Light accent | `"c9ada7"` |
| `theme.bg` | Background color | `"f2e9e4"` |

Colors are **6-char hex without `#`**. Never use `#FF0000` — use `"FF0000"`.

## Authoring Rules

- Set theme fonts explicitly. Do not rely on PowerPoint defaults if typography matters.
- Use `autoFontSize`, `calcTextBox`, and related helpers to size text boxes; do not use PptxGenJS `fit` or `autoFit`.
- Use bullet options, not literal `•` characters.
- Use `imageSizingCrop` or `imageSizingContain` instead of PptxGenJS built-in image sizing.
- Use `latexToSvgDataUri()` for equations and `codeToRuns()` for syntax-highlighted code blocks.
- Prefer native PowerPoint charts for simple bar/line/pie/histogram style visuals so reviewers can edit them later.
- For charts or diagrams that PptxGenJS cannot express well, render SVG externally and place the SVG in the slide.
- Include both `warnIfSlideHasOverlaps(slide, pptx)` and `warnIfSlideElementsOutOfBounds(slide, pptx)` in the submitted JavaScript whenever you generate or substantially edit slides.
- Fix all unintentional overlap and out-of-bounds warnings before delivering. If an overlap is intentional, leave a short code comment near the relevant element.
- `createSlide()` must be synchronous — **never `async`**. `compile.js` won't await it.
- **Never reuse option objects** across PptxGenJS calls — use factory functions instead.
- Body text and captions must **not** use bold. Reserve bold for titles and headings.
- Vary layouts across slides — do not repeat the same structure.

## Recreate Or Edit Existing Slides

- Render the source deck or reference PDF first so you can compare slide geometry visually.
- Match the original aspect ratio before rebuilding layout.
- Preserve editability where possible: text should stay text, and simple charts should stay native charts.
- If a reference slide uses raster artwork, use `ensure_raster_image.py` to generate debug PNGs from vector or odd image formats before placing them.
- For XML-based editing of existing PPTX templates, load `references/minimax-editing.md`.

## Validation Commands

Examples below assume you copied the needed scripts into the working directory. If not, invoke the same script paths relative to this skill folder.

```bash
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

Load `references/pptxgenjs-helpers.md` if you need the helper API summary or dependency details.
