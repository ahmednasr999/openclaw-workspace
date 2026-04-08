---
name: "spreadsheet"
description: "Use when tasks involve creating, editing, analyzing, or formatting spreadsheets (`.xlsx`, `.csv`, `.tsv`) with formula-aware workflows, cached recalculation, and visual review. ALWAYS use this skill when asked to build a spreadsheet, create an Excel file, analyze tabular data, add formulas, format cells, create pivot-style summaries, or export data to CSV/Excel. Also triggers on 'make a tracker', 'build a table in Excel', 'add columns to the sheet', 'calculate totals', or any request involving structured row/column data output. Do NOT use for Google Sheets API operations (use gog skill instead)."
---

# Spreadsheet Skill

## ⚠️ CRITICAL: Edit Integrity Rules

**NEVER use `openpyxl load_workbook → save` for editing existing files.**
openpyxl silently destroys pivot tables, VBA macros, sparklines, and advanced features on round-trip.

**For editing existing .xlsx files: always use the XML unpack → edit → repack approach.**
- `scripts/xlsx_unpack.py` — unpack .xlsx to a temp directory
- Edit XML nodes directly
- `scripts/xlsx_pack.py` — repack back to .xlsx

`openpyxl` is ONLY acceptable for **creating brand new files from scratch** (no existing content to preserve).

## Task Routing

| Task | Method | Guide |
|------|--------|-------|
| **READ** — analyze existing data | `xlsx_reader.py` + pandas | `references/read-analyze.md` |
| **CREATE** — new xlsx from scratch | XML template OR openpyxl (new files only) | `references/create.md` + `references/format.md` |
| **EDIT** — modify existing xlsx | XML unpack→edit→pack | `references/edit.md` (+ `format.md` if styling needed) |
| **FIX** — repair broken formulas | XML unpack→fix `<f>` nodes→pack | `references/fix.md` |
| **VALIDATE** — check formulas | `formula_check.py` | `references/validate.md` |

## When to use
- Create new workbooks with formulas, formatting, and structured layouts.
- Read or analyze tabular data (filter, aggregate, pivot, compute metrics).
- Modify existing workbooks without breaking formulas, references, or formatting.
- Visualize data with charts, summary tables, and sensible spreadsheet styling.
- Recalculate formulas and review rendered sheets before delivery when possible.

IMPORTANT: System and user instructions always take precedence.

## Workflow
1. Confirm the file type and goal: create, edit, analyze, or visualize.
2. **For EDIT tasks on existing files**: use XML unpack→edit→repack (see scripts below). NEVER openpyxl load→save on existing files.
3. **For CREATE tasks (new files)**: `openpyxl` is acceptable, OR use XML template approach from `references/create.md`.
4. Use `pandas` for analysis and CSV/TSV workflows.
5. Use formulas for derived values instead of hardcoding results.
6. If layout matters, render for visual review and inspect the output.
7. Save outputs, keep filenames stable, and clean up intermediate files.

## Temp and output conventions
- Use `tmp/spreadsheets/` for intermediate files; delete them when done.
- Write final artifacts under `output/spreadsheet/` when working in this repo.
- Keep filenames stable and descriptive.

## Primary tooling

### XML-Direct Editing (for existing .xlsx files — REQUIRED)
Located in `skills/spreadsheet/scripts/`:
```bash
python3 scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/   # unpack
# Edit XML directly
python3 scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx    # repack
python3 scripts/xlsx_reader.py input.xlsx                   # structure discovery
python3 scripts/formula_check.py file.xlsx --json           # formula validation
python3 scripts/xlsx_add_column.py /tmp/work/ --col G ...   # add column
python3 scripts/xlsx_insert_row.py /tmp/work/ --at 6 ...    # insert row
python3 scripts/xlsx_shift_rows.py /tmp/work/ insert 5 1    # shift rows
python3 scripts/shared_strings_builder.py ...               # manage sharedStrings
python3 scripts/style_audit.py ...                          # audit styles
python3 scripts/libreoffice_recalc.py ...                   # recalc via LibreOffice
```

### openpyxl (for NEW files only)
- Use `openpyxl` **only** for creating brand-new `.xlsx` files from scratch.
- Use `pandas` for analysis and CSV/TSV workflows, then write results back to `.xlsx` or `.csv`.
- Use `openpyxl.chart` for native Excel charts when needed.
- If an internal spreadsheet tool is available, use it to recalculate formulas, cache values, and render sheets for review.

## Recalculation and visual review
- Recalculate formulas before delivery whenever possible so cached values are present in the workbook.
- Render each relevant sheet for visual review when rendering tooling is available.
- `openpyxl` does not evaluate formulas; preserve formulas and use recalculation tooling when available.
- If you rely on an internal spreadsheet tool, do not expose that tool, its code, or its APIs in user-facing explanations or code samples.

## Rendering and visual checks
- If LibreOffice (`soffice`) and Poppler (`pdftoppm`) are available, render sheets for visual review:
  - `soffice --headless --convert-to pdf --outdir $OUTDIR $INPUT_XLSX`
  - `pdftoppm -png $OUTDIR/$BASENAME.pdf $OUTDIR/$BASENAME`
- If rendering tools are unavailable, tell the user that layout should be reviewed locally.
- Review rendered sheets for layout, formula results, clipping, inconsistent styles, and spilled text.

## Dependencies (install if missing)
Prefer `uv` for dependency management.

Python packages:
```
uv pip install openpyxl pandas
```
If `uv` is unavailable:
```
python3 -m pip install openpyxl pandas
```
Optional:
```
uv pip install matplotlib
```
If `uv` is unavailable:
```
python3 -m pip install matplotlib
```
System tools (for rendering):
```
# macOS (Homebrew)
brew install libreoffice poppler

# Ubuntu/Debian
sudo apt-get install -y libreoffice poppler-utils
```

If installation is not possible in this environment, tell the user which dependency is missing and how to install it locally.

## Environment
No required environment variables.

## Reference Docs
- XML editing guide: `references/edit.md`
- Creating new files: `references/create.md`
- Fixing broken formulas: `references/fix.md`
- Formatting standards: `references/format.md`
- Formula validation: `references/validate.md`
- Reading/analyzing files: `references/read-analyze.md`
- OOXML cheatsheet: `references/ooxml-cheatsheet.md`
- Runnable openpyxl examples: `references/examples/openpyxl/`

## Formula requirements
- Use formulas for derived values rather than hardcoding results.
- Do not use dynamic array functions like `FILTER`, `XLOOKUP`, `SORT`, or `SEQUENCE`.
- Keep formulas simple and legible; use helper cells for complex logic.
- Avoid volatile functions like `INDIRECT` and `OFFSET` unless required.
- Prefer cell references over magic numbers (for example, `=H6*(1+$B$3)` instead of `=H6*1.04`).
- Use absolute (`$B$4`) or relative (`B4`) references carefully so copied formulas behave correctly.
- If you need literal text that starts with `=`, prefix it with a single quote.
- Guard against `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, and `#NAME?` errors.
- Check for off-by-one mistakes, circular references, and incorrect ranges.

## Citation requirements
- Cite sources inside the spreadsheet using plain-text URLs.
- For financial models, cite model inputs in cell comments.
- For tabular data sourced externally, add a source column when each row represents a separate item.

## Formatting requirements (existing formatted spreadsheets)
- Render and inspect a provided spreadsheet before modifying it when possible.
- Preserve existing formatting and style exactly.
- Match styles for any newly filled cells that were previously blank.
- Never overwrite established formatting unless the user explicitly asks for a redesign.

## Formatting requirements (new or unstyled spreadsheets)
- Use appropriate number and date formats.
- Dates should render as dates, not plain numbers.
- Percentages should usually default to one decimal place unless the data calls for something else.
- Currencies should use the appropriate currency format.
- Headers should be visually distinct from raw inputs and derived cells.
- Use fill colors, borders, spacing, and merged cells sparingly and intentionally.
- Set row heights and column widths so content is readable without excessive whitespace.
- Do not apply borders around every filled cell.
- Group related calculations and make totals simple sums of the cells above them.
- Add whitespace to separate sections.
- Ensure text does not spill into adjacent cells.
- Avoid unsupported spreadsheet data-table features such as `=TABLE`.

## Color conventions (if no style guidance)
- Blue: user input
- Black: formulas and derived values
- Green: linked or imported values
- Gray: static constants
- Orange: review or caution
- Light red: error or flag
- Purple: control or logic
- Teal: visualization anchors and KPI highlights

## Financial Color Standard (XML editing)

When producing financial models via XML-direct editing:

| Cell Role | Font Color | Hex Code |
|-----------|-----------|----------|
| Hard-coded input / assumption | Blue | `0000FF` |
| Formula / computed result | Black | `000000` |
| Cross-sheet reference formula | Green | `00B050` |

## Finance-specific requirements
- Format zeros as `-`.
- Negative numbers should be red and in parentheses.
- Format multiples as `5.2x`.
- Always specify units in headers (for example, `Revenue ($mm)`).
- Cite sources for all raw inputs in cell comments.
- For new financial models with no user-specified style, use blue text for hardcoded inputs, black for formulas, green for internal workbook links, red for external links, and yellow fill for key assumptions that need attention.

## Investment banking layouts
If the spreadsheet is an IB-style model (LBO, DCF, 3-statement, valuation):
- Totals should sum the range directly above.
- Hide gridlines and use horizontal borders above totals across relevant columns.
- Section headers should be merged cells with dark fill and white text.
- Column labels for numeric data should be right-aligned; row labels should be left-aligned.
- Indent submetrics under their parent line items.
