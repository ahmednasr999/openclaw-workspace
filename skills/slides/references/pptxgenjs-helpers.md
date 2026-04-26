# PptxGenJS Helpers

## When To Read This

Read this file when you need helper API details, command examples for the bundled Python scripts, or dependency guidance for a slide-generation task.

## Default rule

Default new decks to the safe helper layer.

- Safe helpers live under `assets/pptxgenjs_helpers/safe/`
- Optional helpers live under `assets/pptxgenjs_helpers/optional/`
- Generated authoring stubs should use safe helpers by default
- Only use optional helpers when the slide requirement actually needs them
- If you use optional helpers, verify environment support first

---

## Safe-by-default helpers

These are appropriate for generated stubs and default authoring flows.

- `warnIfSlideHasOverlaps(slide, pptx)`: Detect likely overlaps during authoring
- `warnIfSlideElementsOutOfBounds(slide, pptx)`: Detect elements extending past slide bounds
- `compareElementPosition(slide, a, b)`: Compare element geometry relationships
- `alignSlideElements(slide, indices, alignment)`: Align selected slide elements
- `distributeSlideElements(slide, indices, direction)`: Evenly distribute selected elements
- `getSlideDimensions(slide, pptx)`: Read slide dimensions from pptxgenjs internals
- `inferElementType(obj)`: Infer slide-object type for diagnostics

Current safe entrypoint:
- `require("./pptxgenjs_helpers/safe")`

---

## Optional helpers

These are useful, but they are not guaranteed safe in every environment because they rely on extra packages.

- `autoFontSize(textOrRuns, fontFace, opts)`: Pick a font size that fits a fixed box
- `calcTextBox(fontSizePt, opts)`: Estimate text-box geometry from font size and content
- `calcTextBoxHeightSimple(fontSizePt, numLines, leading?, padding?)`: Quick text height estimate
- `codeToRuns(source, language)`: Convert source code into rich-text runs for `addText`
- `latexToSvgDataUri(texString)`: Render LaTeX to SVG for crisp equations

Current optional entrypoint:
- `require("./pptxgenjs_helpers/optional")`

Use optional helpers only when the slide truly needs that capability.

---

## Helper matrix

| Helper | Layer | Extra dependencies | Default generated stub uses it? |
|---|---|---|---|
| `warnIfSlideHasOverlaps` | safe | none beyond current lane | yes |
| `warnIfSlideElementsOutOfBounds` | safe | none beyond current lane | yes |
| `compareElementPosition` | safe | none beyond current lane | no |
| `alignSlideElements` | safe | none beyond current lane | no |
| `distributeSlideElements` | safe | none beyond current lane | no |
| `getSlideDimensions` | safe | none beyond current lane | no |
| `autoFontSize` | optional | `skia-canvas`, `linebreak`, `fontkit` | no |
| `calcTextBox` | optional | `skia-canvas`, `linebreak`, `fontkit` | no |
| `codeToRuns` | optional | `prismjs` | no |
| `latexToSvgDataUri` | optional | `mathjax-full` | no |

---

## Dependency notes

JavaScript helper modules currently rely on these packages when advanced features are used:

- Core authoring: `pptxgenjs`
- Text measurement: `skia-canvas`, `linebreak`, `fontkit`
- Syntax highlighting: `prismjs`
- LaTeX rendering: `mathjax-full`

Python scripts expect these packages:

- `Pillow`
- `pdf2image`
- `python-pptx`
- `numpy`

System tools used by Python scripts:

- `soffice` / LibreOffice for PPTX to PDF conversion
- Poppler tools for PDF size/raster support used by `pdf2image`
- `fc-list` for font inspection
- Optional rasterization tools for `ensure_raster_image.py`: Inkscape, ImageMagick, Ghostscript, `heif-convert`, `JxrDecApp`

---

## Script notes

- `render_slides.py`: Convert a deck to PNGs. Good for visual review and diffing.
- `slides_test.py`: Add a gray border outside the original canvas, render, and check whether any content leaks into the border.
- `create_montage.py`: Combine multiple rendered slide images into a single overview image.
- `detect_font.py`: Distinguish between fonts that are missing entirely and fonts that are installed but substituted during rendering.
- `ensure_raster_image.py`: Produce a PNG from common vector or unusual raster formats so you can inspect or place the asset easily.

---

## Practical rules

- Default to `LAYOUT_WIDE` unless the source material says otherwise.
- Set font families explicitly before measuring text.
- Use `valign: "top"` for content boxes that may grow.
- Prefer native PowerPoint charts over rendered images when the chart is simple and likely to be edited later.
- Use SVG instead of PNG for diagrams whenever possible.
- Prefer safe helpers by default, and escalate to optional helpers only with intent.
