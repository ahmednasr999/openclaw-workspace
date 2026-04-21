# OpenClaw Slides Execution Plan

## Goal

Turn the implementation backlog into an execution-ready sequence with exact per-file changes.

This plan assumes the current validated baseline is preserved:
- `slides_planner_validate.py` passing
- `slides_authoring_validate.py` passing
- `slides_integration_validate.py` passing

---

## Phase 1 - Safe helper split without breaking current flow

### 1. `assets/pptxgenjs_helpers/layout.js`

#### Keep as part of the safe default layer
Reason:
- currently used by generated stubs and starter examples
- exports only layout/diagnostic functions
- does not pull optional third-party packages

#### No behavioral rewrite required now
Only ensure this becomes the canonical safe import target.

---

### 2. `assets/pptxgenjs_helpers/`

#### Add directory structure
Create:
- `assets/pptxgenjs_helpers/safe/`
- `assets/pptxgenjs_helpers/optional/`

#### Move or mirror modules conceptually
Safe:
- `layout.js`
- any basic image sizing / SVG helpers that do not require undeclared packages

Optional:
- `text.js`
- `code.js`
- `latex.js`

#### Add index files
Create:
- `assets/pptxgenjs_helpers/safe/index.js`
- `assets/pptxgenjs_helpers/optional/index.js`

Safe index should export only guaranteed helpers.
Optional index should either:
- export advanced helpers, or
- throw clear errors when the environment lacks required packages

---

### 3. `scripts/slides_init_authoring_task.py`

#### Change helper copy behavior
Current behavior:
- copies the entire `assets/pptxgenjs_helpers` tree into task-local `authoring/pptxgenjs_helpers`

Required change:
- continue copying the helper tree for convenience
- but make generated `deck.js` import only from the safe layer by default

#### Change generated import line
Current generated stub uses:
- `require("./pptxgenjs_helpers/layout")`

Target:
- `require("./pptxgenjs_helpers/safe")`
  or
- `require("./pptxgenjs_helpers/safe/layout")`

#### Add header comment in generated `deck.js`
Include a short note:
- this deck uses safe helpers only by default
- optional helpers exist for advanced text/code/LaTeX workflows
- optional helpers may require extra packages not installed in every environment

#### Validation impact
- update `slides_authoring_validate.py` if the generated import path changes
- update `slides_integration_validate.py` if string assertions depend on old imports

---

### 4. `references/pptxgenjs-helpers.md`

#### Rewrite structure
Current doc mixes helper API and dependency notes.

Target structure:
1. safe helpers
2. optional helpers
3. dependency matrix
4. when to escalate from safe to optional

#### Add explicit helper classification table
Columns:
- helper
- layer
- extra dependency required
- common use case
- should default stub use it?

#### Add one operator rule
- default new decks to safe helpers only
- only use optional helpers when the slide requirement clearly needs them

---

### 5. `package.json`

#### Short-term change
No forced install expansion yet.

#### Optional future change
If later desired, use `optionalDependencies` rather than quietly turning advanced helpers into hard requirements.

---

## Phase 2 - Deck spec handshake

### 6. `scripts/slides_plan_from_sources.py`

#### Add new function
Create a planner-level function like:
- `build_deck_spec(entries, target_slide_count, outline)`

#### Emit `planning/deck_spec.json`
Suggested shape:

```json
{
  "objective": "...",
  "audience": "...",
  "tone": "...",
  "targetSlideCount": 7,
  "aspectRatio": "16:9",
  "styleMode": "editorial-default",
  "brandMode": "unbranded",
  "starterPack": "executive-summary",
  "imagePolicy": "optional-supporting-visuals",
  "editableOutputRequired": true,
  "polishLevel": "working-draft",
  "confidence": "medium",
  "unresolvedAssumptions": []
}
```

#### Extend `build_deck_brief(...)`
Add a section like:
- `## Deck spec`
- short bullets mirroring the JSON

#### Extend `write_outputs(...)`
Current outputs:
- `deck_brief.md`
- `slide_outline.json`
- `content_map.md`

Target outputs:
- `deck_brief.md`
- `slide_outline.json`
- `content_map.md`
- `deck_spec.json`

#### Add starter-pack recommendation logic
At minimum infer from:
- audience
- objective
- section types
- slide count band

Suggested first routing:
- 5 to 8 slides + executive audience -> `executive-summary`
- KPI / metrics heavy -> `kpi-story`
- timeline / next steps heavy -> `transformation-roadmap`
- operational cadence -> `weekly-operating-review`
- board / investment / ask language -> `board-proposal`

---

### 7. `scripts/slides_init_authoring_task.py`

#### Read `planning/deck_spec.json`
Current init reads:
- `slide_outline.json`
- registry

Target:
- also read `deck_spec.json` when present

#### Extend `build_authoring_manifest(...)`
Add top-level manifest fields:
- `deckSpec`
- `workflowState`
- `deliveryContract`

Example:

```json
"workflowState": {
  "completed": ["intake", "planning", "authoring-init"],
  "current": "authoring",
  "next": "build"
}
```

#### Extend `build_authoring_notes(...)`
Add a section near the top:
- objective
- audience
- tone
- starter pack
- style mode
- image policy
- polish level

#### Extend `build_deck_stub(...)`
Add a top-level constant in generated JS:
- `const deckSpec = ...`

Use it immediately for:
- output metadata comments
- starter family selection
- future palette/style switching

---

### 8. `references/slides-planning-brief.md`

#### Add deck-spec contract explicitly
New minimum planning output list should become:
1. `deck_brief.md`
2. `slide_outline.json`
3. `content_map.md`
4. `deck_spec.json`

#### Define required deck-spec fields
Include:
- objective
- audience
- tone
- deck length
- aspect ratio
- starter pack
- style mode
- unresolved assumptions

---

### 9. `SKILL.md`

#### Update workflow section
Current flow is already solid, but make the handshake explicit:
1. ingest
2. extract
3. plan
4. inspect / confirm deck spec
5. init authoring
6. build
7. render
8. QA
9. deliver

#### Add a short “minimum deck spec” block
This should be a very compact operating checklist, not a long essay.

---

## Phase 3 - Starter-pack behavior

### 10. `scripts/slides_init_authoring_task.py`

#### Replace generic stub-only posture
Current generated `deck.js` is a universal scaffold with renderers for all patterns.

Keep that scaffolding, but add a starter-pack routing layer.

#### Add starter pack constant
Example:
- `const STARTER_PACK = deckSpec.starterPack || "executive-summary";`

#### Add starter-pack bootstrap section
Three options, in order of simplicity:

Option A, recommended now:
- keep one generated universal deck
- add starter-pack-specific comments, token presets, and slide ordering hints

Option B, stronger:
- select among embedded starter structures during stub generation

Option C, later:
- copy from real starter templates in `examples/`

Recommendation:
- do A now
- evolve to C later once example structure is standardized

#### Add starter-pack-specific token presets
Examples:
- `executive-summary`
- `weekly-operating-review`
- `board-proposal`

This can initially be comments plus starter composition hints, not a full theme engine.

---

### 11. `examples/`

#### Formalize current examples as starter packs
Existing:
- `examples/executive-summary-starter`
- `examples/weekly-report-starter`

Make them the canonical references for:
- starter naming
- slide rhythm
- expected export path
- rendered QA shape

#### Add one more pack
Create:
- `examples/board-proposal-starter`

Why this one first:
- high leverage for executive / investor / strategy decks
- directly aligned with the PPT Master comparison work

---

### 12. `scripts/slides_planner_validate.py`

#### Add fixture coverage for starter-pack recommendation
Current validation checks pattern selection.

Extend fixtures or validation output to also verify recommended `starterPack` for representative cases.

---

## Phase 4 - Workflow state and troubleshooting

### 13. `SKILL.md`

#### Add workflow-state table
For each stage define:
- artifact expected
- command or action
- success signal
- typical failure
- next move

Keep it short and operational.

#### Add standard delivery contract section
Default bundle:
- `.pptx`
- source `deck.js`
- manifest
- notes
- rendered review assets when relevant

---

### 14. `scripts/slides_integration_validate.py`

#### Improve final summary output
Current output is correct but thin.

Add stage-level summary fields like:
- `ingestOk`
- `planningOk`
- `authoringInitOk`
- `buildOk`
- `renderOk`
- `patternsDetected`
- `starterPack`
- `deckSpecPresent`

This improves debugging without changing logic much.

---

### 15. New file `references/slides-troubleshooting.md`

#### Add compact sections
- missing optional JS dependency
- NODE_PATH missing
- font substitution / missing fonts
- render failed because LibreOffice or conversion layer missing
- overlap warnings
- out-of-bounds warnings
- leftover placeholder content
- task dir not initialized fully

#### Add “what to do next” for each
This is where PPT Master’s workflow discipline is genuinely worth copying.

---

## Phase 5 - Delivery bundle discipline

### 16. `scripts/slides_init_authoring_task.py`

#### Add `deliveryContract` into manifest
Example:

```json
"deliveryContract": {
  "required": [
    "exports/*.pptx",
    "authoring/deck.js",
    "authoring/authoring_manifest.json",
    "authoring/authoring_notes.md"
  ],
  "optional": [
    "rendered/*.png",
    "montage.png",
    "planning/deck_brief.md",
    "planning/content_map.md",
    "planning/deck_spec.json"
  ]
}
```

This gives the lane a cleaner definition of done.

---

## Recommended commit sequence

### Commit 1
Safe helper split and docs
- helper folder structure
- safe imports in generated stubs
- helper reference rewrite

### Commit 2
Deck-spec handshake
- planner emits `deck_spec.json`
- init carries deck spec into manifest / notes / stub
- docs updated

### Commit 3
Starter-pack behavior
- starter pack recommendation
- init uses starter pack metadata
- starter examples normalized

### Commit 4
Workflow state + troubleshooting
- docs
- integration summary improvement
- troubleshooting reference

### Commit 5
Delivery contract
- manifest contract
- polish and validation updates

---

## Stop / no-go rules

Do not do these in the same pass:
- helper split plus broad dependency install plus style engine rewrite
- architecture pivot toward SVG-first generation
- HTML lane experimentation inside the core slides skill
- major starter-pack refactor without validation updates

One clean change family at a time.

---

## Final recommendation

The first implementation pass should be:
1. safe helper split
2. deck spec emission + propagation
3. starter-pack recommendation plumbing

That is the highest-value complete move.
