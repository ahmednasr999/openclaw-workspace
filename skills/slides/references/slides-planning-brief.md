# Slides Planning Brief

Use this reference after source ingestion/extraction and before slide authoring.

## Goal

Turn normalized source material into a usable authoring plan, not just a summary.

The planning layer should produce:
- `planning/deck_brief.md`
- `planning/slide_outline.json`
- `planning/content_map.md`
- `planning/deck_spec.json`

## Minimum planning outputs

### 1. Deck brief
Must capture:
- objective
- audience
- tone
- recommended deck length
- proposed narrative arc
- strongest source materials
- missing inputs or unresolved assumptions
- a compact deck-spec summary

### 1a. Deck spec
Must capture:
- objective
- audience
- tone
- target slide count
- aspect ratio
- style mode
- brand mode
- starter pack recommendation
- starter narrative hint
- image policy
- editable-output requirement
- polish level
- overall confidence
- unresolved assumptions

### 2. Slide outline
For each proposed slide include:
- slide number
- slide type: `cover | toc | section-divider | content | summary`
- working title
- purpose
- key message
- source ids
- recommended layout direction
- visuals needed
- confidence

### 3. Content map
Map source ids to:
- what they contribute
- where they should appear
- whether the source is strong, partial, or weak

## Planning rules

- This is a planning artifact, not the final deck.
- Prefer concise, inspectable outputs over verbose prose.
- Every proposed slide should have one clear job.
- If the source material is weak, say so plainly.
- Separate facts from assumptions.
- Do not overfit to one source if several complementary sources exist.
- Default to 16:9 unless source context suggests otherwise.
- Use the existing slide page-type discipline from the slides skill.
- Plan from reusable slide patterns first, not from a blank canvas.
- Adjacent slides should not repeat the same composition unless that repetition is intentional.
- The outline should be strong enough that authoring can start from pattern selection rather than exploratory layout invention.

## Starter pattern discipline

The planner should also recommend a starter pack where possible, for example:
- `executive-summary`
- `weekly-operating-review`
- `kpi-story`
- `transformation-roadmap`
- `board-proposal`

This should live in `planning/deck_spec.json` and be propagated into authoring artifacts.


Before authoring, each slide should implicitly map to a starter layout family such as:
- cover
- agenda
- section divider
- thesis / summary
- metric / KPI
- comparison
- timeline / roadmap / process
- 2-column explainer
- closing / CTA

The exact visual execution can evolve during authoring, but the planner should already be narrowing the deck into these reusable buckets.

## Recommended heuristics

### Deck length
- very small source set -> 3 to 5 slides
- moderate source set -> 5 to 9 slides
- broad/report-style set -> 8 to 14 slides

### Narrative arc defaults
- Cover
- Context / TOC
- Problem / opportunity
- Core argument or solution
- Supporting evidence / examples
- Recommendation / next step
- Summary / close

Adapt as needed, do not force this if the source demands another arc.

## Confidence levels

Use one of:
- `high`
- `medium`
- `low`

Confidence should reflect source quality and planning certainty, not optimism.
