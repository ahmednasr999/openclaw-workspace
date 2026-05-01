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
