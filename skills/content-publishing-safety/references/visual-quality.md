# Visual Quality Rules

## Default reference

Universal default for Ahmed LinkedIn static post visuals:

`/root/.openclaw/workspace/media/inbound/234fe40d-96c3-4b4a-bf6f-dc1f75f91bbf.jpg`

Reference-quality floor for the hand-drawn style:

`/root/.openclaw/workspace/output/linkedin/return-on-tokens-rot-handdrawn-reference-quality-latest-2026-06-10.png`

## Quality bar

Premium visual must match the approved hand-drawn sketchnote concept and craft level, not just its rough structure.

Pass requires:

- Warm off-white paper or comparable premium paper texture.
- Black ink illustration with restrained orange accents.
- One clear large handwritten headline.
- Compact flow diagram, toolkit, system, or operating-model metaphor matched to the caption thesis.
- Authentic hand-drawn lettering and linework, not a sketch filter or generic template.
- Strong whitespace, readable at mobile size.
- Ahmed Nasr signature/footer treatment.

Reject if:

- Generic dark tech card, stock photo, or SaaS template unless Ahmed explicitly requested that direction.
- Flat, cheap, under-designed, or sketch-filter-like.
- Old reference text contaminates the image.
- Crowded boxes, dense labels, tiny unreadable copy, or overlapping elements.
- Missing the hand-drawn paper, ink, orange-accent, and Ahmed-signature treatment.
- Uses the dark executive card style for a normal LinkedIn static visual.

## Daily publish gate

For automated daily LinkedIn publishing, the Notion image intent must include a reference-checked QA marker such as `Visual QA: PASS - reference-checked handmade sketchnote`. The marker means the actual image, not only the prompt or palette, was compared against the approved hand-drawn sketchnote reference.

The daily publisher must fail closed if the visual is unreviewed, too dark, blue-card dominated, or still points to a rejected legacy asset.

## Done means

An inspected candidate exists and passes the gate. Tool success, file creation, or nudging another agent is not done.
