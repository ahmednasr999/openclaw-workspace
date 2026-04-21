# HTML Slides System

Minimal premium HTML slide starter kit with a first planner layer.

## What is included
- executive theme tokens
- executive theme CSS
- Nunjucks templates for 8 starter patterns
- TypeScript planner
- TypeScript renderer
- planning artifacts in `planning/latest/`
- rendered deck in `builds/latest/index.html`

## Run
```bash
npm install
npm run build
```

Or step by step:
```bash
npm run plan
npm run render
```

## Planner outputs
The planner currently writes:
- `planning/latest/deck_brief.md`
- `planning/latest/slide_outline.json`
- `planning/latest/content_map.md`

The renderer consumes `slide_outline.json` when present.

## Current scope
This starter kit now proves:
- structured source input
- deterministic planning artifacts
- pattern-based rendering
- reusable executive styling

Next layers to add:
- schema validation
- screenshot QA
- export pipeline
- richer planner heuristics
