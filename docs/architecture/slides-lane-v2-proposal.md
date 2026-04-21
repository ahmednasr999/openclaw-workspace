# Slides Lane v2 Proposal

## Executive Summary

Slides Lane v2 should keep the current OpenClaw `slides` skill as the primary deck-authoring lane and selectively import the strongest ideas from `ppt-master`.

Do not replace the current lane.
Do not adopt ppt-master's full workflow bureaucracy.
Do not switch the default authoring model away from PptxGenJS.

Instead, build a hybrid system:
- keep **PptxGenJS-native premium deck authoring** as the default path
- add a stronger **source-ingestion and normalization front end**
- add an optional **visual-intermediate lane** for hard-to-author diagrams and complex visuals
- formalize project artifact flow so deck work becomes easier to inspect, resume, and automate

The result should be a system that is:
- better at starting from messy source material
- still better than ppt-master at premium executive output
- more maintainable than a prompt-heavy SVG-first pipeline

---

## Strategic Position

### Keep as system of record
Current `slides` skill remains the system of record for:
- premium executive decks
- editorial / investor / board-level design
- direct editable `.pptx` authoring
- XML-based deck surgery when the user wants an existing template modified

### Import from ppt-master
Import only these categories:
1. source ingestion
2. content normalization
3. project workspace discipline
4. optional intermediate-representation lane for difficult visuals
5. stronger source-to-outline planning automation

### Explicit non-goals
Do **not**:
- migrate to an SVG-first default
- copy multi-role prompt bureaucracy verbatim
- make every deck go through strategist/image-generator/executor phases
- replace premium design judgment with a bigger pipeline

---

## Current State Assessment

### Current OpenClaw slides lane strengths
The current lane is strongest at:
- editable deck creation with PptxGenJS
- premium/executive/editorial quality bar
- helper-based layout authoring
- deterministic QA for overflow/font/rendering issues
- XML editing workflow for existing PPTX files
- explicit design-system guidance

This makes it the better default lane for Ahmed's real use cases, where the goal is not merely conversion, but persuasive, premium presentation output.

### Current gap areas
The main gaps relative to ppt-master are:
- no strong standardized front-end source ingestion package
- weaker document-to-outline normalization pipeline
- less explicit task-local workspace structure for deck projects
- no optional intermediate vector-conversion lane for hard visuals
- less structured automation for turning messy source content into a first-pass slide architecture

### ppt-master's real contributions
ppt-master contributes meaningful ideas in these areas:
- document/URL/PDF/DOCX/PPT ingestion into markdown
- project folder discipline
- explicit staged workflow
- SVG post-processing as a first-class layer
- real SVG-to-DrawingML conversion machinery

These are worth borrowing selectively.

---

## Design Principles for v2

1. **Default to the simplest complete path**
   - most decks should still be built directly in PptxGenJS
   - do not force heavyweight preprocessing unless the source complexity justifies it

2. **Treat source normalization as separate from slide design**
   - ingestion and content preparation should happen before layout work begins
   - this reduces design-phase thrash

3. **Keep premium judgment near the output**
   - design taste, slide hierarchy, rhythm, and persuasion should remain in the direct authoring lane
   - do not bury those decisions inside a rigid multi-stage prompt stack

4. **Use intermediate representations only when they solve a real problem**
   - SVG lane should be optional and targeted
   - not every slide needs it

5. **Every phase should leave inspectable artifacts**
   - if a deck is resumable, debuggable, and reviewable, automation gets safer

---

## Proposed v2 Architecture

## Layer 1 - Source Ingestion

Purpose:
Normalize messy source inputs into a clean project intake package.

Supported inputs:
- PDF
- DOCX / DOC
- PPTX
- URLs
- Markdown
- pasted text / notes
- image references used as design/style guidance

Proposed outputs:
- `sources/` raw inputs
- `normalized/` extracted markdown and parsed notes
- `intake.json` metadata manifest
- `assets/` imported images / extracted visual assets

Suggested v2 scripts:
- `scripts/slides_ingest.py`
- `scripts/slides_extract_sources.py`
- `scripts/slides_build_intake_manifest.py`

Responsibilities:
- move or copy all source files into task-local structure
- convert supported sources into markdown/text
- identify source type and extraction confidence
- produce normalized filenames and manifest metadata
- record source provenance for later QA

This is the biggest direct import opportunity from ppt-master.

---

## Layer 2 - Content Normalization and Deck Planning

Purpose:
Turn normalized source material into a usable deck brief before any slide authoring begins.

Outputs:
- `deck_brief.md`
- `slide_outline.json`
- `content_map.md`
- optional `visual_requests.json`

Recommended planning structure:
- deck objective
- audience
- tone
- target length
- slide-by-slide page type
- per-slide core message
- evidence/data references
- visuals needed
- unresolved assumptions

This should borrow the *idea* behind ppt-master's strategist phase, but without the role theater.

It should be one concise planning artifact, not a sprawling mandatory ritual.

Suggested behavior:
- classify each slide using our existing slide page-type discipline
- recommend visual rhythm and deck arc
- separate “content accepted” from “design accepted”
- highlight gaps early (missing numbers, missing charts, weak source quality)

Suggested v2 scripts or helper docs:
- `scripts/slides_plan_from_sources.py`
- `references/slides-planning-brief.md`

---

## Layer 3 - Primary Authoring Lane (Default)

This remains the current system:
- PptxGenJS-native deck authoring
- helper-based layout and text fitting
- Premium Executive Mode / Editorial Systems Mode
- render/montage/overflow/font QA

This should remain default for:
- premium executive decks
- board decks
- investor decks
- operating reviews
- product and strategy presentations

Enhancements to this lane in v2:
- consume `slide_outline.json` directly
- support a cleaner task-local project structure
- support reusable deck manifests
- support better source traceability per slide

Suggested additions:
- every slide can optionally carry source references in code comments or metadata
- render QA can report issues by slide type and source section
- deck generation can persist a compact manifest for resume/debug

---

## Layer 4 - Optional Visual Intermediate Lane

Purpose:
Handle complex visuals that are awkward in direct PptxGenJS.

Use only when needed for:
- dense diagrams
- process maps
- custom infographics
- highly art-directed vector compositions
- AI-generated structured visuals that need cleanup before placement

Important:
This lane should **not** replace primary slide authoring.
It should produce visual components for insertion into the main deck.

Possible outputs:
- cleaned SVG assets
- converted PNG fallback assets
- optional editable conversion artifacts when feasible

Possible build directions:
1. lightweight SVG asset workflow only
2. SVG-to-native conversion for limited shape families
3. selective reuse of ppt-master conversion ideas for diagrams only

Recommendation:
Start with option 1, then evaluate option 2 later.

Do **not** begin by trying to replicate ppt-master's full SVG-to-PPTX architecture.
That is a bigger engineering program than we need right now.

---

## Layer 5 - QA and Finalization

Current QA should remain and expand.

Keep:
- render slides
- create montage
- overflow detection
- font substitution detection
- markitdown extraction checks

Add:
- source coverage check: did all required source sections land somewhere?
- placeholder audit across all generated artifacts
- visual-rhythm audit: repeated layout overuse
- deck-manifest summary for reproducibility

Suggested outputs:
- `qa/report.json`
- `qa/report.md`
- `exports/`
- `rendered/`

---

## Proposed Task-Local Workspace Structure

```text
<task-dir>/
├── sources/                # original inbound materials
├── normalized/             # markdown/text extracted from sources
├── assets/                 # imported/extracted images, logos, diagrams
├── planning/
│   ├── intake.json
│   ├── deck_brief.md
│   ├── slide_outline.json
│   └── content_map.md
├── authoring/
│   ├── deck.js
│   ├── helpers/
│   └── generated_assets/
├── rendered/               # slide PNGs
├── qa/
│   ├── report.json
│   └── report.md
└── exports/
    ├── final.pptx
    └── source.js
```

This is cleaner than the current looser flow and less sprawling than ppt-master's full process tree.

---

## Build Priorities

### Priority 1 - Source ingestion front end
Build first.

Why:
- biggest current gap
- immediately useful
- low conceptual risk
- improves every future deck workflow

Deliverables:
- standardized intake structure
- source conversion wrappers
- manifest generation

### Priority 2 - Planning artifact generation
Build second.

Why:
- reduces slide-authoring ambiguity
- improves consistency across larger decks
- captures source-to-slide intent explicitly

Deliverables:
- deck brief
- slide outline
- content map

### Priority 3 - Projectized deck workflow
Build third.

Why:
- makes work resumable and inspectable
- easier automation, debugging, and handoff

Deliverables:
- standard task-local directories
- export conventions
- QA artifact storage

### Priority 4 - Optional visual intermediate lane
Build fourth.

Why:
- valuable, but narrower
- more engineering risk
- can become a rabbit hole if done too early

Deliverables:
- isolated SVG asset workflow
- insertion path into primary deck authoring lane

### Priority 5 - Deep conversion R&D
Build only if repeated need justifies it.

Why:
- high effort
- likely diminishing returns if direct PptxGenJS remains good enough for most work

This is where any serious borrowing from ppt-master's DrawingML conversion ideas would belong.

---

## What To Borrow Exactly

### Borrow now
- standardized source import conventions
- source-to-markdown conversion wrappers
- project manifest discipline
- explicit normalized artifact storage
- content planning before deck generation
- deterministic post-processing mindset

### Borrow later if proven necessary
- selective SVG post-processing ideas
- diagram/visual cleanup pipeline
- conversion utilities for limited visual classes

### Do not borrow
- role-sprawl as doctrine
- mandatory strategist/image-generator/executor ritual for every project
- SVG-first default architecture
- excessive prompt governance as a substitute for code structure

---

## Risks

### Risk 1 - Overbuilding the pipeline
If v2 becomes a giant preflight ritual, it will slow normal deck work.

Mitigation:
- make ingestion/planning lightweight by default
- allow bypass for simple decks

### Risk 2 - Losing premium quality focus
If automation expands but design judgment weakens, output quality will drop.

Mitigation:
- keep premium/editorial QA at the center
- protect direct authoring lane as the primary path

### Risk 3 - SVG rabbit hole
A sophisticated SVG conversion lane can consume a lot of engineering time.

Mitigation:
- keep it optional
- start narrow
- use it for specific hard visuals only

---

## Recommended Next Implementation Move

Implement **Priority 1 + Priority 2 only** as the first v2 slice:

1. build source ingestion wrapper
2. build intake manifest
3. build deck-brief / slide-outline planner
4. wire those outputs into the existing slides skill

This gives the highest leverage with the lowest risk.

---

## Final Recommendation

Slides Lane v2 should be:
- **our current slides lane** for authoring quality
- **plus ppt-master's best front-end workflow ideas**
- **plus an optional future visual-intermediate lane**

That is the right synthesis.

Do not switch systems.
Do not rewrite around SVG.
Do not copy the bureaucracy.

Keep the premium authoring core.
Strengthen the intake and planning layers.
Add a hard-visual lane only where it genuinely improves output.
