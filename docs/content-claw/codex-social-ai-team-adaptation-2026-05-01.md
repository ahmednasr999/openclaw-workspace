# Codex Social AI Team Adaptation - 2026-05-01

Source reviewed: `https://github.com/stevenflanagan1/codex-social-ai-team`

## Decision

Do not install the skill pack wholesale.

Use it as a pattern source only. The repository is built for generic SMB social media operations, while Ahmed's workflow is executive LinkedIn positioning with stricter visual quality, approval, and privacy requirements.

## Why Not Install Wholesale

- It would overlap with existing `content-claw`, CMO, Notion/content-pipeline, and LinkedIn safety workflows.
- It would add prompt bloat through many broad skills that are not Ahmed-specific.
- Its default assumptions are client/SMB and multi-platform social operations, not Ahmed's executive AI/PMO/GCC positioning.
- It includes optional publishing/scheduling ideas that must remain approval-gated in this environment.

## Patterns Worth Adapting

### 1. Workflow status block

Use for multi-step CMO/content work where state can otherwise get lost.

```text
# Content Workflow Status

Workstream:
Current stage:
Last completed:
Next action:
Blocked by:
Approved assets:
Publishing status:
Quality gate:
Updated:
```

Rules:
- Keep it short.
- Update only when it reduces ambiguity.
- Do not create process theater for one-step tasks.
- If blocked, name the exact blocker and the next safe action.

### 2. Publisher QA checklist

Before any LinkedIn handoff, scheduling preparation, or posting approval request, verify:

- Caption approved or explicitly marked draft.
- Creative approved and visually matches the caption.
- Correct platform and date/time.
- Correct ratio and export format.
- Alt text drafted when useful.
- No unapproved claims, invented facts, or unsupported metrics.
- No private/client/system data exposed.
- Handles, links, filenames, and media paths are correct.
- For image posts, media is actually attached/uploadable and not text-only by mistake.
- Final user approval obtained before public posting or third-party scheduling.

### 3. Carousel/document-post story arcs

Useful arcs for LinkedIn carousels and document posts:

- Hook -> tension -> insight -> steps -> CTA
- Problem -> mistakes -> better way -> example -> CTA
- Myth -> truth -> proof -> application -> CTA
- Before -> turning point -> after -> lesson -> CTA
- Checklist -> point 1 -> point 2 -> point 3 -> save/share CTA
- Case study -> context -> action -> result -> takeaway -> CTA

Ahmed-specific constraint: compress the story into executive, practical, mobile-readable content. Avoid generic quote-card sequences.

### 4. Creative brief and prompt log

For premium visuals, preserve enough context to reproduce or review the work:

```text
Concept:
Target audience:
Message:
Visual direction:
Reference asset:
Prompt used:
Generated asset path:
Local composition path:
Quality review:
Decision: pass/fail
```

Use this with the image-to-UI premium card workflow. The reference sets taste and atmosphere; local composition controls exact copy, spacing, footer, and mobile fidelity.

### 5. Privacy/share check

Before exporting, sharing, or publishing a content pack, scan for:

- credentials and tokens
- private client data
- local system paths that should not be public
- hidden `.env` files
- CV/job-search/private strategy material
- accidental screenshots or metadata exposing sensitive context

Implement as Linux/OpenClaw-native checks if this becomes recurring. Do not use the repo's PowerShell script directly.

## Integration Points

Patch only the local workflow guidance:

- `skills/content-claw/SKILL.md`
- future CMO reports/status files when needed
- optional future checklist/script if this repeats

No gateway/runtime/config changes are needed.

## Stop Rules

- Do not add all upstream skills.
- Do not copy generic SMB voice rules over Ahmed's voice.
- Do not introduce third-party publishing integrations without explicit approval.
- Do not turn every small content task into a heavy workflow-status process.
