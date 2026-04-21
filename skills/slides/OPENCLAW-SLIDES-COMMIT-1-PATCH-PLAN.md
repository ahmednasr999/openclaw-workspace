# OpenClaw Slides Commit 1 Patch Plan

## Commit objective

Ship the first safe infrastructure improvement without changing slide behavior:
- separate safe vs optional helper usage
- keep current validated flow working
- make generated stubs safer by default
- avoid installing new dependencies in this commit

This commit should not change deck design quality directly.
It should reduce accidental breakage.

---

## Commit scope

### In scope
- helper-layer structure
- generated import path defaults
- clearer helper documentation
- validation updates required by import-path change

### Out of scope
- deck-spec handshake
- starter-pack logic
- style engine changes
- optional dependency installation
- major helper rewrites

---

## Files to add

### 1. `assets/pptxgenjs_helpers/safe/index.js`

## Purpose
Provide one stable safe import surface for generated stubs.

## Contents
Export only helpers that are safe in the current environment.

Initial content should be minimal and explicit, for example:
- import from `../layout`
- export:
  - `warnIfSlideHasOverlaps`
  - `warnIfSlideElementsOutOfBounds`
  - `compareElementPosition`
  - any other layout-only helpers that do not pull optional packages

## Rule
Do not re-export `codeToRuns`, `latexToSvgDataUri`, or text measurement helpers here.

---

### 2. `assets/pptxgenjs_helpers/optional/index.js`

## Purpose
Create a clearly marked advanced helper entry point.

## Contents
Re-export optional helpers from:
- `../code`
- `../text`
- `../latex`

Possible pattern:
- export direct requires for advanced environments
- if desired, wrap with friendly error messages later

For this commit, simple explicit re-export is enough.
The key point is separation, not fancy runtime handling yet.

---

## Files to edit

### 3. `scripts/slides_init_authoring_task.py`

## Change A, generated import path

### Current
Generated `deck.js` includes:
```js
const layoutHelpers = require("./pptxgenjs_helpers/layout");
```

### Target
Change to:
```js
const layoutHelpers = require("./pptxgenjs_helpers/safe");
```

This is the most important code change in the commit.

---

## Change B, generated file header comment

At the top of generated `deck.js`, before imports, add a short comment block like:

```js
// Slides Lane v2 authoring stub
// Default helper mode: safe
// Optional helpers for advanced text/code/LaTeX workflows live under
// ./pptxgenjs_helpers/optional and may require extra packages.
```

Purpose:
- make the safety model visible to future authors
- stop accidental assumptions about helper availability

---

## Change C, keep helper-copy behavior unchanged

Do not change task-local helper copying in this commit, except ensuring the new `safe/` and `optional/` folders are copied along with the rest of `pptxgenjs_helpers`.

Why:
- lower risk
- no need to rewrite workspace bootstrapping yet

---

### 4. `scripts/slides_authoring_validate.py`

## Required update

Add one new assertion that confirms the generated stub now points to the safe helper layer.

Add to `REQUIRED_SNIPPETS`:
```python
'require("./pptxgenjs_helpers/safe")'
```

Optionally remove dependence on the old direct layout import if any explicit assertion for that exists later.

Purpose:
- lock in the new safe default

---

### 5. `scripts/slides_integration_validate.py`

## Required update

Add one assertion that the generated `deck.js` contains the safe helper import.

Example:
```python
assert_true('require("./pptxgenjs_helpers/safe")' in deck_js, 'Generated deck.js missing safe helper import', failures)
```

Do not otherwise change integration logic in this commit.

Purpose:
- ensure end-to-end task generation uses the new safe layer

---

### 6. `references/pptxgenjs-helpers.md`

## Rewrite structure

### Replace the current helper listing with these sections:

#### Safe-by-default helpers
Include only helpers that are safe in the current default environment.
Examples:
- overlap warnings
- out-of-bounds warnings
- geometry / alignment helpers if they come from safe modules
- image helpers only if they do not require undeclared packages

#### Optional helpers
List clearly as optional:
- `autoFontSize(...)`
- `calcTextBox(...)`
- `codeToRuns(...)`
- `latexToSvgDataUri(...)`

#### Dependency matrix
Add a compact table:
- helper
- layer
- dependency requirements
- default generated stub uses it? yes/no

#### Operator rule
Add a short rule block:
- default new decks to safe helpers only
- use optional helpers only when the slide requirement actually needs them
- if optional helpers are used, validate environment support first

This doc update is required, not optional.
Otherwise the code split will still be confusing.

---

## Optional file edit, only if useful in same commit

### 7. `SKILL.md`

Add one small note under the PptxGenJS/helper guidance:
- generated authoring stubs default to safe helpers
- optional helpers live under `pptxgenjs_helpers/optional`

This is useful but not mandatory for Commit 1 if you want to keep the diff smaller.

---

## Exact patch order

### Step 1
Create:
- `assets/pptxgenjs_helpers/safe/index.js`
- `assets/pptxgenjs_helpers/optional/index.js`

### Step 2
Edit `scripts/slides_init_authoring_task.py`
- change generated import path
- add safety comment block in generated stub

### Step 3
Edit `scripts/slides_authoring_validate.py`
- assert safe helper import string

### Step 4
Edit `scripts/slides_integration_validate.py`
- assert safe helper import string

### Step 5
Rewrite `references/pptxgenjs-helpers.md`
- safe vs optional sections
- dependency matrix
- operator rule

### Step 6
Run validation
- `python3 scripts/slides_authoring_validate.py`
- `python3 scripts/slides_integration_validate.py`

Optional:
- `python3 scripts/slides_planner_validate.py`

---

## Expected result after Commit 1

### Behavior
- current deck generation still works
- current starter examples still work
- generated stubs now point to a safe helper surface
- optional advanced helpers are still available, but no longer implied as safe defaults

### Operator benefit
- lower chance of accidental dependency breakage
- clearer mental model for authors
- better foundation for future deck-spec and starter-pack work

---

## Risks to watch

### Risk 1
`safe/index.js` exports an insufficient subset and generated stubs lose expected layout helper functions.

### Mitigation
Export the same layout helpers the stub already relies on, just through the safe wrapper.

### Risk 2
Validation fails because string assertions still expect old import paths.

### Mitigation
Update validator assertions in the same commit.

### Risk 3
Future authors still import optional helpers directly from legacy files.

### Mitigation
Documentation plus stub header comment in this commit. Harder enforcement can come later.

---

## Definition of done

Commit 1 is done when all are true:
- safe helper index exists
- optional helper index exists
- generated `deck.js` imports `./pptxgenjs_helpers/safe`
- authoring validation passes
- integration validation passes
- helper doc clearly distinguishes safe vs optional

---

## Recommended commit message

`slides: split safe vs optional helper entrypoints for authoring stubs`
