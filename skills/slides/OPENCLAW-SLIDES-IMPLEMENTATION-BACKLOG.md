# OpenClaw Slides Implementation Backlog

## Purpose

Concrete file-by-file backlog to strengthen the existing OpenClaw Slides lane without changing its core architecture.

Validated baseline before writing this backlog:
- planner validation passes
- authoring stub validation passes
- integration validation passes
- PPTX export and render path works in the current environment

Conclusion from validation:
- the slides lane is not structurally broken
- the main opportunity is better productization, dependency safety, and more explicit workflow contracts

---

## Strategic decision

Keep:
- PPTX-native generation with PptxGenJS
- editorial pattern system
- task-local workspace flow
- editable `.pptx` + source `.js` output model

Improve:
- deck-spec handshake before build
- dependency hygiene for helper modules
- starter-deck / starter-pack behavior
- workflow state visibility and troubleshooting
- delivery artifact discipline

Do not do now:
- do not pivot to an SVG-first architecture
- do not fork into an HTML runtime
- do not weaken the editorial system to chase easier generation

---

## Priority order

1. P0 - dependency-safe helper split
2. P0 - explicit deck-spec handshake
3. P0 - starter-pack generation behavior
4. P1 - workflow state visibility and troubleshooting
5. P1 - delivery artifact contract
6. P2 - theme audition and richer packaging polish

---

## P0 - Dependency-safe helper split

### Why

Current helper discovery is too optimistic. `references/pptxgenjs-helpers.md` correctly documents optional dependencies, but `package.json` only declares `pptxgenjs`. The result is a lane that works on the safe path, but can fail unexpectedly if an author uses optional helpers without the corresponding packages installed.

Observed optional helper dependencies:
- `assets/pptxgenjs_helpers/text.js` -> `fontkit`, `linebreak`, `skia-canvas`
- `assets/pptxgenjs_helpers/code.js` -> `prismjs`
- `assets/pptxgenjs_helpers/latex.js` -> `mathjax-full/*`

### Files

#### `assets/pptxgenjs_helpers/`

Add a clearer split:
- `core/` or `safe/` subset for guaranteed helpers
- `optional/` subset for advanced helpers

Proposed safe helpers:
- layout diagnostics
- basic image sizing helpers that only depend on bundled/runtime-safe modules
- lightweight geometry/alignment helpers
- SVG-to-data helpers only if they do not pull optional deps

Proposed optional helpers:
- text measurement helpers using canvas/font packages
- syntax highlighting helpers
- LaTeX rendering helpers

#### `scripts/slides_init_authoring_task.py`

Change authoring stub generation so it imports only the safe helper layer by default.

Add comments in generated `authoring/deck.js` like:
- safe helpers enabled by default
- optional helpers require explicit install or environment support

#### `references/pptxgenjs-helpers.md`

Rewrite as two clear sections:
- safe-by-default helpers
- optional helpers requiring extra packages

Add a quick matrix:
- helper name
- safe default or optional
- dependency requirements
- typical use case

#### `package.json`

Keep base dependencies minimal.
Do not blindly add all optional packages globally unless that is an explicit product decision.

Instead, add either:
- documented `optionalDependencies`, or
- no install change yet, but make the separation explicit in docs and generated stubs

Recommendation: prefer explicit docs + safe imports first, then decide later whether optional deps deserve installation.

---

## P0 - Explicit deck-spec handshake

### Why

The current lane has strong planning artifacts, but the generation contract is still too implicit. PPT Master is right about one thing: output gets better when the system forces the user or planner to commit to a compact design brief before build.

### Files

#### `scripts/slides_plan_from_sources.py`

Extend planning output with a compact `deck_spec` object containing:
- objective
- audience
- tone
- target slide count
- aspect ratio
- style mode
- brand mode
- image policy
- editable-output requirement
- polish level
- confidence notes
- unresolved assumptions

This should be emitted into:
- `planning/deck_spec.json`
- a concise human-readable section in `planning/deck_brief.md`

#### `scripts/slides_init_authoring_task.py`

Include `deck_spec.json` in generated artifacts.
Add it to:
- `authoring_manifest.json`
- `authoring_notes.md`
- header comments in generated `authoring/deck.js`

#### `SKILL.md`

Update workflow instructions so new-deck work explicitly includes:
1. ingest
2. extract
3. plan
4. confirm or adopt deck spec
5. init authoring
6. build
7. render
8. QA
9. deliver

Also add a short “minimum deck spec” checklist.

#### `references/slides-planning-brief.md`

Promote the deck spec into the planning contract instead of treating it as optional implied metadata.

---

## P0 - Starter-pack generation behavior

### Why

The lane already has patterns, starter layouts, and example decks. What it lacks is a more explicit user-facing concept of “starter packs” or “starter deck families” that make blank-page authoring unnecessary.

### Files

#### `scripts/slides_init_authoring_task.py`

Upgrade authoring init from “pattern-aware stub” to “starter-pack aware stub”.

Add starter-pack selection logic using either:
- deck objective
- source shape
- audience
- tone
- slide-count band

Proposed starter packs:
- executive-summary
- weekly-operating-review
- board-proposal
- transformation-roadmap
- KPI-story
- premium-carousel

The generated `deck.js` should then start from the nearest real family rather than a generic all-pattern scaffold.

#### `scripts/slides_plan_from_sources.py`

Emit a recommended `starterPack` field into the outline or deck spec.

#### `examples/`

Formalize current examples as official starter packs:
- `examples/executive-summary-starter`
- `examples/weekly-report-starter`

Then add at least one more high-value example:
- `examples/board-proposal-starter`

#### `SKILL.md`

Document starter-pack routing explicitly:
- when speed matters, start from a starter pack
- when quality matters, start from a starter pack and then elevate patterns
- do not start from an empty deck unless the request truly demands a unique visual system

---

## P1 - Workflow state visibility and troubleshooting

### Why

The lane has the right scripts, but the operator experience is still too implicit. The skill should feel like a production workflow with visible states and recovery guidance.

### Files

#### `SKILL.md`

Add a visible workflow state model:
- intake
- extraction
- planning
- deck spec
- authoring init
- build
- render
- QA
- delivery

For each state, note:
- expected artifact
- success signal
- common failure mode
- next recovery move

#### `scripts/slides_init_authoring_task.py`

Add workflow state metadata to `authoring_manifest.json`, for example:
- `workflowState.current`
- `workflowState.completed`
- `workflowState.next`

#### `scripts/slides_integration_validate.py`

Expand summary output so failures are easier to diagnose by stage.
Right now it validates correctly, but summary reporting can become more product-like.

#### New file: `references/slides-troubleshooting.md`

Add a compact troubleshooting reference covering:
- missing optional JS dependencies
- missing fonts
- LibreOffice / render issues
- placeholder text left in deck
- overlap warnings
- out-of-bounds warnings
- task-local path mistakes
- NODE_PATH issues

This is one of the most useful ideas to copy from PPT Master: make recovery easy to follow.

---

## P1 - Delivery artifact contract

### Why

The lane already produces strong internal artifacts. It should declare a standard delivery bundle so every deck job ends consistently.

### Files

#### `SKILL.md`

Add a delivery contract section.
Default deck delivery bundle should be:
- final `.pptx`
- source `deck.js`
- rendered slide PNGs or montage when useful
- `authoring_manifest.json`
- `authoring_notes.md`
- planning artifacts when the user wants traceability

#### `scripts/slides_init_authoring_task.py`

Predeclare expected outputs in the manifest so downstream steps know what “done” means.

#### Possibly new script later
- `scripts/slides_bundle_delivery.py`

Not required immediately, but worth noting for later automation.

---

## P2 - Theme audition and packaging polish

### Why

Useful, but not first. This is polish, not the core bottleneck.

### Files

#### `references/slides-style-guide.md`

Later improvement:
- define named editorial recipes more explicitly
- map semantic style choices to concrete theme tokens

#### `scripts/slides_plan_from_sources.py`

Later improvement:
- emit a stronger palette/style recommendation tied to audience and purpose

#### `examples/`

Later improvement:
- multiple style variants of the same starter pack for quicker theme audition

---

## Recommended implementation sequence

### Phase 1
- update `references/pptxgenjs-helpers.md`
- update `scripts/slides_init_authoring_task.py` to import only safe helpers by default
- add clearer optional-helper notes in generated stubs

### Phase 2
- extend `scripts/slides_plan_from_sources.py` to emit `deck_spec.json`
- update `scripts/slides_init_authoring_task.py` to carry deck-spec into notes/manifest/stub
- update `references/slides-planning-brief.md`
- update `SKILL.md`

### Phase 3
- add `starterPack` recommendation in planning
- upgrade authoring init to choose starter family
- formalize existing examples as starter packs
- add one additional starter pack

### Phase 4
- add `references/slides-troubleshooting.md`
- improve workflow state reporting in docs and manifests
- tighten delivery bundle contract

---

## Non-goals

- no architecture migration to SVG-first generation
- no HTML-slide system fork
- no replacement of editorial rules with generic template logic
- no broad dependency bloat without explicit product decision

---

## Final recommendation

If only three things are funded now, do these:
1. safe-vs-optional helper split
2. deck-spec handshake
3. starter-pack generation behavior

That captures most of the useful PPT Master lessons while preserving what is already stronger in OpenClaw Slides.
