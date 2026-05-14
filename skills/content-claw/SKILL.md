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
- For the premium content-card workflow, universal default reference is `/root/.openclaw/workspace/output/jobzoom-visuals/ahmed-linkedin-ai-execution-card-4k.jpg`. Use the Ahmed LinkedIn AI execution card format for every LinkedIn post visual unless Ahmed explicitly chooses another direction. The generator `/root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py` remains the implementation path, but default outputs should match this execution-card format.
- Premium content-card completion requires a binary visual quality gate before any candidate is sent as done. Compare the candidate against the reference on two axes: format compliance and premium craft parity. Reject if it is only structurally similar but feels cheaper, flatter, more generic, more stock-like, less cinematic, weaker in gold/white typography, weaker in depth, weaker in footer polish, or missing an execution/system metaphor.
- Never use the reference image as a literal canvas with new text pasted over old text. Remake a clean card in the same direction. Reject any old-text contamination, overlapping text, generic infographic boxes, dense labels, unreadable small copy, or accidental UI/poster artifacts.
- Done means an inspected candidate exists, passes the gate, and has a side-by-side comparison or equivalent visual evidence. Nudging another agent, generating a file, or receiving a successful tool response is not done.
- For premium card production, prefer the image-to-UI workflow in `docs/content-claw/image-to-ui-premium-card-workflow.md`: use image generation/reference for taste, then controlled code/composition for typography, spacing, footer, and mobile fidelity when raw generation is not precise enough.
- For posts explaining an AI agent, automation, or operating model, use `docs/content-claw/ai-agent-workflow-card-template.md` for the content anatomy, then compress it into the 9:16 execution-card format. Do not copy dense horizontal dashboard layouts unless Ahmed explicitly asks.
- For multi-step CMO/content work, use the lightweight workflow-status pattern in `docs/content-claw/codex-social-ai-team-adaptation-2026-05-01.md` when it reduces ambiguity: current stage, next action, blocker, approved assets, publishing status, and quality gate. Do not create process theater for one-step tasks.
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

Reference: `/root/.openclaw/workspace/output/jobzoom-visuals/ahmed-linkedin-ai-execution-card-4k.jpg`

Pass requires all of the following:
- 9:16 executive card format with one dominant mobile-readable headline and one short support line.
- Dark cinematic executive boardroom/city/execution atmosphere with real depth, not flat wallpaper.
- Polished gold/white typography hierarchy comparable to the reference.
- Blue/gold accent system and a purposeful execution/system metaphor.
- Refined Ahmed-branded footer.
- No old-text overlay, no copied reference canvas misuse, no dense labels, no generic infographic boxes, no tiny unreadable copy.
- Candidate has been inspected against the reference locally; preferably save a side-by-side comparison artifact.

Fail fast and iterate if any item fails. Do not tell Ahmed it is done until the artifact passes this gate or there is a specific blocker.

## Skillify Trigger

If a content workflow fails, repeats, or requires Ahmed to babysit, convert it into a durable CMO rule, script, checklist, or test under the NASR Skillify Protocol.

## Learned Improvements

### 2026-05-02 - Weekly Skill Tune-Up

**Reviewed lessons:**
- 2026-04-29, CMO visuals followed the reference direction but still fell below reference-level craft.
- 2026-04-23, premium LinkedIn visuals failed when copy landed on Ahmed's face, backgrounds were generic, or the concept stayed in a disliked direction.
- 2026-04-21, LinkedIn visuals were selected by date/file availability instead of semantic match to the post thesis.

**Improvement recommendation:**
Before any premium LinkedIn visual is marked ready, run a three-part rejection gate: thesis match, platform-native composition, and reference-level craft parity. Reject candidates that merely imitate the template, look cheaper than the reference, use generic AI portrait logic, place copy over Ahmed's face/suit, or lack a clear execution metaphor tied to the post. If Ahmed dislikes the concept, stop polishing that direction and propose 2-3 fresh concepts instead.

**Checklist status:** `eval/checklist.md` is not present for this skill. Until one exists, use `docs/content-claw/premium-linkedin-visual-quality-gate.md` plus the rejection gate above.
