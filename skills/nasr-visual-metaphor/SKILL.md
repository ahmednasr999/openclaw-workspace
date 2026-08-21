---
name: nasr-visual-metaphor
description: Use this whenever Ahmed Nasr needs a LinkedIn static-visual concept, sketchnote brief, image prompt, visual metaphor, concept refresh, or critique of a proposed content visual. Turn an executive thesis into an original physical metaphor, score competing concepts, produce a 4:5 shot list and generation prompt, and apply concept-level rejection gates before image generation. This is the required concept-engine step for Ahmed's normal hand-drawn LinkedIn visuals; it does not authorize generation, approval, scheduling, or publishing.
metadata:
  owner: CMO
  status: active
  source_inspiration: process principles observed in Ian Xiaohei Illustrations; no character, composition, or brand assets copied
---

# NASR Visual Metaphor

Use this skill to make Ahmed's static visuals memorable because the idea is physically clear, not merely because the surface style is consistent.

The skill owns concept invention and the pre-generation brief. `content-claw` owns visual quality and publishing preparation. `content-publishing-safety` and `linkedin` retain approval, duplicate, scheduling, and publishing gates.

## Required inputs

Start from the caption, outline, or a one-sentence thesis. Resolve these before proposing art:

- the one belief the reader should retain
- the operating tension, failure, or change behind it
- the executive action or decision implied
- any claim that must remain evidence-bound
- the intended platform and format

If a full caption exists, do not summarize every paragraph into the image. Select one cognitive anchor.

## Default output

For a normal Ahmed LinkedIn static visual, produce a concept brief before producing or requesting an image. The brief must contain:

1. thesis
2. cognitive anchor
3. three metaphor candidates
4. scorecard and winner
5. one shot list
6. text inventory
7. production prompt
8. negative constraints
9. QA and collision-check notes

Use the exact template in `references/brief-template.md`.

## Workflow

### 1. Compress the thesis

Write one sentence in the form:

`When [condition], [mechanism] causes [consequence], so leaders should [action].`

This prevents the image from becoming a topic poster. The visual must explain the mechanism, not decorate the subject.

### 2. Select one cognitive anchor

Choose the single relationship the image should make unforgettable:

- hidden system behind a simple interface
- bottleneck or handoff
- sequence or decision order
- control versus speed
- ownership versus activity
- signal versus noise
- compounding or leakage
- local optimization versus end-to-end outcome
- fragile dependency versus resilient system

Do not combine two anchors in one static image. Route a genuinely multi-part idea to a carousel.

### 3. Generate three physical metaphors

Use `references/metaphor-engine.md`. Each candidate must specify:

- one dominant object or scene
- one visible action
- a direct mapping from physical elements to business meaning
- what the orange accent reveals
- why the concept is fresh for Ahmed's recent feed

Prefer a cutaway, cross-section, jam, counterweight, relay, tool, control mechanism, or backstage/frontstage reveal when it makes causality visible. Literal topic icons such as robots, glowing brains, hospital crosses, handshakes, dashboards, and app-logo mosaics do not count as metaphors.

An anonymous operator, hand, or executive figure may appear only when human action clarifies ownership or decision rights. It must be restrained and serious, never a recurring mascot, cute character, cartoon identity, or imitation of another creator's visual language.

### 4. Run the originality collision check

Inspect the most recent ten Ahmed static visuals or their visual-intent records when available. Reject a candidate if it repeats the same dominant object, camera/composition, or mechanism used recently, even if the labels differ.

Also reject concepts that reproduce a source repository's character, example composition, signature motif, or recognizable scene. Borrow process principles, not identity.

If recent assets are unavailable, state that the collision check is provisional instead of pretending it passed.

### 5. Score and select

Score all three candidates using `references/qa-rubric.md`. The winner needs at least 10/12, no zero, and a clean originality check.

If no concept clears the threshold, generate three new metaphors. Do not promote the least weak option.

### 6. Build the shot list

Design one 4:5 portrait composition, normally 1080 x 1350 or an equivalent 4:5 generation size.

Default anatomy:

- one mobile-readable handwritten hook of 3-8 words
- one dominant physical system occupying roughly 45-60% of the canvas
- one visible causal action
- three to five supporting labels, normally one to three words each
- one restrained orange path, lever, fault, handoff, or control signal
- generous breathing room
- exact `Ahmed Nasr` signature/footer

Keep total rendered copy under roughly 28 words, including labels but excluding the signature. A single static image should feel like one memorable executive sketch, not a miniature presentation.

### 7. Apply the NASR surface system

Use this default unless Ahmed requests another direction:

- premium warm off-white paper with subtle natural texture
- authentic black-ink hand drawing and hand lettering
- restrained orange accents used only to show the key path, intervention, or tension
- confident executive tone with a slightly unexpected physical metaphor
- imperfect human linework without sketch-filter artifacts
- no dark tech treatment, blue/gold execution card, stock photo, or polished vector icon system

The first reaction should be “that is an interesting mechanism,” followed within one second by “I understand the point.”

### 8. Write the production prompt

Describe the physical scene before the style. Preserve exact required text in a separate inventory. Include composition, action, hierarchy, material, palette, whitespace, and exclusions.

Do not ask an image model to invent the business logic. The brief must already resolve the metaphor.

### 9. Inspect and loop

After generation, inspect the actual image against both this concept brief and the quality gates in:

- `/root/.openclaw/workspace/skills/content-claw/references/visual-quality.md`
- `/root/.openclaw/workspace/skills/content-claw/checklists/image-post-quality.md`
- `/root/.openclaw/workspace/docs/content-claw/premium-linkedin-visual-quality-gate.md`

Classify failure before iterating:

- concept failure: the metaphor is unclear, generic, derivative, or semantically wrong; return to step 3
- composition failure: the idea works but hierarchy, density, or mobile readability fails; revise the shot list
- craft failure: the idea and layout work but the handmade finish, lettering, or footer is weak; regenerate or locally refine
- text failure: wording is wrong or illegible; reduce copy and repair only if the image remains clean

Do not keep polishing a failed concept.

## Stop rules

- Do not create a final asset when the active workflow requires brief approval first, unless Ahmed explicitly asks for immediate generation.
- Do not mark a visual approved, scheduled, published, or QA-passed from a concept brief.
- Do not fabricate evidence or imply that a visual claim is verified when the caption is not.
- Do not overwrite an already approved caption/visual pair without Ahmed's explicit request.
- Do not publicly post or schedule through this skill.

## References

- `references/metaphor-engine.md` for candidate invention and novelty lenses
- `references/qa-rubric.md` for scoring and rejection gates
- `references/brief-template.md` for the required handoff format
- `eval/checklist.md` for skill-output validation
