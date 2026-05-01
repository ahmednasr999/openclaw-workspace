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
   - Start from the canonical execution-card reference:
     `/root/.openclaw/workspace/output/jobzoom-visuals/ahmed-linkedin-ai-execution-card-4k.jpg`
   - Define one dominant hook and one short support line before generation.

2. **Visual generation**
   - Generate a 9:16 premium candidate that matches the reference direction.
   - Reject generic infographic/social-template outputs immediately.

3. **Controlled implementation**
   - If the generated output is close but not exact, move to local composition or code-based rendering instead of repeatedly asking for vague image edits.
   - Use code/composition to control typography, spacing, footer, safe areas, and brand hierarchy.

4. **Side-by-side verification**
   - Compare candidate against the reference on:
     - format compliance
     - premium craft parity
     - mobile readability
     - footer polish
     - execution/system metaphor

5. **Only then send or mark done**
   - Tool success, file creation, or CMO confirmation is not completion.
   - Completion requires an inspected artifact that passes the premium quality gate.

## Practical rule

When a premium card is weak, do not keep prompting blindly. Decide which failure class applies:

- **Taste failure:** regenerate from a stronger prompt/reference.
- **Structure failure:** rebuild as 9:16 execution-card format.
- **Typography/layout failure:** use controlled local composition/code.
- **Reference misuse:** discard and rebuild clean, never paste over the reference.

## Non-goals

- Do not import external skills wholesale.
- Do not post publicly from this workflow without explicit approval.
- Do not treat an image-to-frontend workflow as a replacement for Ahmed's premium visual quality gate.

## Next implementation opportunity

Adapt `/root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py` so its default output is 9:16 execution-card format, not square, then test it against the premium quality gate on one real post before making it a default production path.
