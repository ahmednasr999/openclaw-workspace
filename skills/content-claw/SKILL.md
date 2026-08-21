---
name: content-claw
description: "Use for LinkedIn/X content workflow support, content-pipeline decisions, and executive content system improvements."
metadata:
  owner: CMO
  status: draft
---

# Content Claw

Use this skill for Ahmed's executive content workflow when the task concerns content ideas, drafts, review, publishing preparation, or content-system improvements.

## Rules

- Content should be executive-level, practical, and aligned with Ahmed's positioning.
- LinkedIn posts should end with a question or CTA when appropriate.
- Do not post publicly without explicit approval.
- Do not post text-only when an image is expected.
- Before prompting or generating a normal static LinkedIn visual, use `/root/.openclaw/workspace/skills/nasr-visual-metaphor/SKILL.md` to produce and score an original physical-metaphor brief. Concept approval is not visual approval, and neither authorizes scheduling or publishing.
- For Ahmed LinkedIn static post visuals, the universal default is the approved hand-drawn sketchnote concept: warm off-white paper, black ink, restrained orange accents, toolkit/system metaphor, large handwritten headline, compact flow diagram, and Ahmed Nasr signature/footer. Reference: `/root/.openclaw/workspace/media/inbound/234fe40d-96c3-4b4a-bf6f-dc1f75f91bbf.jpg`; quality floor: `/root/.openclaw/workspace/output/linkedin/return-on-tokens-rot-handdrawn-reference-quality-latest-2026-06-10.png`.
- Do not use generic dark tech cards, cinematic stock backgrounds, or the old blue/gold executive card style for normal LinkedIn static visuals. Use that dark executive direction only when Ahmed explicitly asks for a reel/video/dark-card direction or for JobZoom-specific visuals.
- Premium visual completion requires a binary visual quality gate before any candidate is sent as done or published. Compare the candidate against the approved hand-drawn references on concept fit, craft parity, mobile readability, paper/ink/orange treatment, whitespace, and Ahmed signature/footer. Reject if it is only loosely similar, feels cheaper, flatter, generic, template-like, crowded, or missing the toolkit/system metaphor.
- Never use a reference image as a literal canvas with new text pasted over old text. Remake a clean visual in the same direction. Reject any old-text contamination, overlapping elements, generic infographic boxes, dense labels, unreadable small copy, sketch-filter artifacts, or accidental UI/poster artifacts.
- Done means an inspected candidate exists, passes the gate, and has a side-by-side comparison or equivalent visual evidence. Nudging another agent, generating a file, or receiving a successful tool response is not done.
- For premium card production, prefer the image-to-UI workflow in `docs/content-claw/image-to-ui-premium-card-workflow.md`: use image generation/reference for taste, then controlled code/composition for typography, spacing, footer, and mobile fidelity when raw generation is not precise enough.
- For posts explaining an AI agent, automation, or operating model, use `docs/content-claw/ai-agent-workflow-card-template.md` for the content anatomy, then compress it into the approved hand-drawn sketchnote concept. Do not copy dense horizontal dashboard layouts unless Ahmed explicitly asks.
- For multi-step CMO/content work, use the lightweight workflow-status pattern in `docs/content-claw/codex-social-ai-team-adaptation-2026-05-01.md` when it reduces ambiguity: current stage, next action, blocker, approved assets, publishing status, and quality gate. Do not create process theater for one-step tasks.
- When one idea should become multiple coordinated assets, use the NASR Campaign Graph in `docs/content-claw/nasr-campaign-graph.md`. Record the intake, asset relationships, stage gates, and tied performance feedback there. Keep Notion as the sole live approval and publishing source of truth.
- Before any LinkedIn handoff, scheduling preparation, or public posting approval request, run publisher QA: caption approved or clearly draft, creative approved and matched to caption, correct platform/date/ratio, alt text where useful, no unapproved claims, no private data, correct media paths, and explicit approval before any external post/schedule action.


## Modular Publishing Safety References

For detailed publishing safety, load only the needed file:

References:
- `references/linkedin-posting.md` - LinkedIn approval, upload, and s3key rules.
- `references/visual-quality.md` - premium visual reference and rejection rules.
- `references/notion-content-calendar.md` - content calendar source-of-truth.
- `references/duplicate-prevention.md` - live/local duplicate prevention before external writes.

Checklists:
- `checklists/pre-publish.md` - before approval requests, scheduling, or publishing.
- `checklists/image-post-quality.md` - before saying a visual is ready.
- `checklists/post-publish-verification.md` - after publish or retry.

Default rule: draft locally, verify quality, check duplicates, and require the correct approval boundary before any public/external action.

## Premium Visual Quality Gate

Use this gate for every Ahmed LinkedIn premium card unless Ahmed explicitly chooses a different visual direction.

Canonical checklist: `docs/content-claw/premium-linkedin-visual-quality-gate.md`

Reference: `/root/.openclaw/workspace/media/inbound/234fe40d-96c3-4b4a-bf6f-dc1f75f91bbf.jpg`

Quality floor: `/root/.openclaw/workspace/output/linkedin/return-on-tokens-rot-handdrawn-reference-quality-latest-2026-06-10.png`

Pass requires all of the following:
- A NASR visual-metaphor brief selected one cognitive anchor, compared three materially different concepts, passed the 10/12 concept threshold, and checked recent-visual collision.
- Default LinkedIn static format is 4:5 portrait unless Ahmed or the content structure requires another ratio.
- Warm off-white paper or comparable premium paper texture.
- Black ink illustration with restrained orange accent lines/arrows.
- One large mobile-readable handwritten headline.
- Compact flow diagram, toolkit, system, or operating-model metaphor matched to the post thesis.
- Authentic hand lettering and linework, not a sketch filter.
- Strong whitespace and readable support labels.
- Refined Ahmed Nasr signature/footer.
- No old-text overlay, no copied reference canvas misuse, no crowded boxes, no dense labels, no generic dark tech cards, no tiny unreadable copy.
- Candidate has been inspected against the reference locally; preferably save a side-by-side comparison artifact.

Fail fast and iterate if any item fails. Do not tell Ahmed it is done until the artifact passes this gate or there is a specific blocker.

## Skillify Trigger

If a content workflow fails, repeats, or requires Ahmed to babysit, convert it into a durable CMO rule, script, checklist, or test under the NASR Skillify Protocol.

## Learned Improvements

### 2026-06-27 - Weekly Skill Tune-Up

**Reviewed lessons:**
- 2026-06-24, reference-led visuals failed when the concept, layout, and hierarchy did not match the reference before style was applied.
- 2026-06-26, the default LinkedIn visual direction was updated in memory but older active gates still pointed toward dark executive card language.
- 2026-06-26, sketchnote means handmade raster craft, not a clean vector flow using the right paper, ink, and orange palette.

**Improvement recommendation:**
For every Ahmed LinkedIn visual brief, extract the reference's composition, metaphor, hierarchy, and handmade craft requirements before writing prompts or producing controlled layouts. The gate should reject candidates that only preserve topic, color, or broad structure. Normal static visuals must read as handmade raster sketchnotes with imperfect ink, paper texture, hand-lettered hierarchy, toolkit/system metaphor, and Ahmed signature/footer; clean vector diagrams, polished icon systems, and dark executive cards are failures unless Ahmed explicitly requests that direction.

**Checklist status:** `eval/checklist.md` exists and points to the modular publishing and visual gates. Apply this recommendation as an overlay to `checklists/image-post-quality.md` and `docs/content-claw/premium-linkedin-visual-quality-gate.md`.

### 2026-05-02 - Weekly Skill Tune-Up

**Reviewed lessons:**
- 2026-04-29, CMO visuals followed the reference direction but still fell below reference-level craft.
- 2026-04-23, premium LinkedIn visuals failed when copy landed on Ahmed's face, backgrounds were generic, or the concept stayed in a disliked direction.
- 2026-04-21, LinkedIn visuals were selected by date/file availability instead of semantic match to the post thesis.

**Improvement recommendation:**
Before any premium LinkedIn visual is marked ready, run a three-part rejection gate: thesis match, platform-native composition, and reference-level craft parity. Reject candidates that merely imitate the template, look cheaper than the reference, use generic AI portrait logic, place copy over Ahmed's face/suit, or lack a clear execution metaphor tied to the post. If Ahmed dislikes the concept, stop polishing that direction and propose 2-3 fresh concepts instead.

**Checklist status:** `eval/checklist.md` exists and points to modular publishing and visual gates. Until deeper visual checks are needed, use it with `docs/content-claw/premium-linkedin-visual-quality-gate.md` plus the rejection gate above.
