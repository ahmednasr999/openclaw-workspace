# Image-to-UI premium card workflow

## Source pattern

X article inspected 2026-05-01:
`https://x.com/LLMJunky/status/2049871598883115376`

Title: `Codex Guide: Images -> Real UI in 6 Steps`

The useful pattern is not the exact toolchain. The useful pattern is the workflow:

1. Use a high-taste image model or visual reference to establish the target aesthetic.
2. Convert that image/reference into controlled implementation through code/composition.
3. Iterate against the original visual until spacing, typography, layout, icons, footer, and mobile readability match the quality target.

## Ahmed content implication

For Ahmed's premium LinkedIn visuals, raw image generation alone is not enough. The default workflow should be:

1. **Taste target**
   - Start from the canonical hand-drawn sketchnote reference:
     `/root/.openclaw/workspace/media/inbound/234fe40d-96c3-4b4a-bf6f-dc1f75f91bbf.jpg`
   - Use the accepted quality-floor asset for craft parity:
     `/root/.openclaw/workspace/output/linkedin/return-on-tokens-rot-handdrawn-reference-quality-latest-2026-06-10.png`
   - Define one dominant handwritten hook and a compact flow/toolkit metaphor before generation.

2. **Visual generation**
   - Generate a premium hand-drawn sketchnote candidate that matches the reference direction.
   - Reject generic dark tech cards, stock backgrounds, infographic boxes, and social-template outputs immediately unless Ahmed explicitly asked for that direction.

3. **Controlled implementation**
   - If the generated output is close but not exact, move to local composition or code-based rendering instead of repeatedly asking for vague image edits.
   - Use code/composition to control typography, spacing, footer, safe areas, and brand hierarchy.

4. **Side-by-side verification**
   - Compare candidate against the reference on:
     - hand-drawn sketchnote concept fit
     - premium craft parity
     - mobile readability
     - footer/signature polish
     - toolkit/system metaphor

5. **Only then send or mark done**
   - Tool success, file creation, or CMO confirmation is not completion.
   - Completion requires an inspected artifact that passes the premium quality gate.

## Practical rule

When a premium card is weak, do not keep prompting blindly. Decide which failure class applies:

- **Taste failure:** regenerate from a stronger prompt/reference.
- **Structure failure:** rebuild around the hand-drawn paper, headline, compact flow, and toolkit/system metaphor.
- **Lettering/layout failure:** use controlled local composition/code.
- **Reference misuse:** discard and rebuild clean, never paste over the reference.

## Non-goals

- Do not import external skills wholesale.
- Do not post publicly from this workflow without explicit approval.
- Do not treat an image-to-frontend workflow as a replacement for Ahmed's premium visual quality gate.

## Next implementation opportunity

Adapt `/root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py` so its default output is the approved hand-drawn sketchnote concept, not the old dark execution-card format, then test it against the premium quality gate on one real post before making it a default production path.
