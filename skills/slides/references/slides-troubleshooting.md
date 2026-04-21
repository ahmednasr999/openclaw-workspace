# Slides Troubleshooting

Use this when the slides lane fails at a specific stage. Treat the workflow as staged, not as one opaque command.

---

## Workflow states

| State | Expected artifact | Success signal | Common failure | Next move |
|---|---|---|---|---|
| intake | `sources/sources.json` | sources registered | missing input path / URL ingest issue | re-run `slides_ingest.py`, verify source path |
| extraction | normalized source text/files | extracted text exists | unsupported source or weak extraction | inspect extracted output, verify source readability |
| planning | `deck_brief.md`, `slide_outline.json`, `content_map.md`, `deck_spec.json` | files exist and look coherent | poor pattern routing, weak deck spec, missing sections | inspect planning artifacts before authoring |
| authoring-init | `authoring/deck.js`, `authoring_notes.md`, `authoring_manifest.json` | files generated cleanly | planning artifact missing or stale | re-run `slides_init_authoring_task.py` after fixing planning |
| build | `.pptx` in `exports/` | PPTX written successfully | JS runtime error, helper import issue | run `node authoring/deck.js`, inspect stack trace |
| render | slide PNGs | rendered images exist | LibreOffice / conversion problem | run `render_slides.py` directly and inspect stderr |
| QA | montage/text/font reports | no unresolved issues remain | overlap, overflow, placeholder text, missing fonts | fix and re-run affected checks |
| delivery | final artifact bundle | `.pptx` + `.js` + notes/manifest available | missing expected artifacts | verify manifest delivery contract |

---

## Common failures

### 1. Missing optional JS dependency

Symptoms:
- `Cannot find module 'skia-canvas'`
- `Cannot find module 'prismjs'`
- `Cannot find module 'mathjax-full/...'

Meaning:
- the deck is using optional helpers, not just the safe helper layer

What to do:
1. confirm whether the stub should have used only `./pptxgenjs_helpers/safe`
2. if optional helpers are truly needed, verify environment support first
3. otherwise remove optional-helper usage and fall back to safe helpers

---

### 2. `NODE_PATH` missing

Symptoms:
- local deck build fails to resolve `pptxgenjs`
- helper imports work but package imports do not

What to do:
- run with:

```bash
NODE_PATH=/root/.openclaw/workspace/skills/slides/node_modules node authoring/deck.js
```

Do not guess another node_modules path unless the workspace actually changed.

---

### 3. Missing fonts or substitutions

Symptoms:
- layout drift after render
- typography looks wrong
- `detect_font.py` reports missing/substituted fonts

What to do:
1. run:

```bash
python3 scripts/detect_font.py deck.pptx --json
```
2. confirm theme fonts are explicitly set
3. prefer stable installed fonts when portability matters
4. re-render after any font change, because line breaks can shift

---

### 4. Render failure

Symptoms:
- `render_slides.py` fails
- no PNGs generated
- PPTX exists but render review is blocked

Likely causes:
- LibreOffice / `soffice` issue
- PDF conversion issue
- broken PPTX structure from authoring mistake

What to do:
1. confirm the PPTX was actually created
2. run `render_slides.py` directly on the exported PPTX
3. inspect stderr before changing deck code
4. if the PPTX is invalid, go back to build stage and inspect the JS/runtime error

---

### 5. Overlap warnings

Symptoms:
- `warnIfSlideHasOverlaps(...)` logs warnings

What to do:
- do not ignore them automatically
- first check if the overlap is intentional
- if not intentional, simplify layout before micro-adjusting positions
- re-render the affected slide after each fix

---

### 6. Out-of-bounds warnings

Symptoms:
- `warnIfSlideElementsOutOfBounds(...)` logs elements extending beyond slide bounds

What to do:
- reduce width/height or reposition the offending element
- re-check titles, badges, and support panels first because they often drift near edges
- re-render after adjustment

---

### 7. Placeholder text left in deck

Symptoms:
- `placeholder`, `hero field`, `support field`, `lorem`, `xxxx`, etc. remain in final deck

What to do:
1. extract deck text:

```bash
python -m markitdown deck.pptx
```
2. grep for placeholders:

```bash
python -m markitdown deck.pptx | grep -iE "xxxx|lorem|ipsum|placeholder|hero field|support field"
```
3. replace or intentionally remove before declaring done

---

### 8. Task directory feels incomplete or stale

Symptoms:
- old planning artifacts remain after source changes
- authoring notes contradict slide outline
- deck spec no longer matches request

What to do:
1. regenerate in order:

```bash
python3 scripts/slides_extract_sources.py <task_dir>
python3 scripts/slides_plan_from_sources.py <task_dir>
python3 scripts/slides_init_authoring_task.py <task_dir> --force
```
2. do not patch around stale planning files manually unless there is a specific reason

---

## Fast recovery checklist

If something breaks, check in this order:
1. did planning artifacts generate cleanly?
2. does `deck_spec.json` match the actual request?
3. does `authoring/deck.js` build with the expected `NODE_PATH`?
4. was the exported PPTX actually created?
5. do rendered PNGs exist?
6. do text extraction and font checks reveal silent quality issues?

If any answer is no, fix that stage before moving forward.
