---
name: premium-frontend-design
description: Use this for frontend UI creation, redesign, UI audits, landing pages, dashboards, web apps, React/Next/Vue/Svelte components, CSS/Tailwind polish, design-system cleanup, or when the user wants an interface to look premium, executive, product-grade, less generic, less AI-generated, or more visually polished. Apply especially before coding UI, reviewing existing frontend code, or improving spacing, typography, hierarchy, motion, responsive behavior, states, and accessibility.
---

# Premium Frontend Design

This skill raises frontend output above generic AI UI. It is adapted for OpenClaw work: serious product UI, executive dashboards, LinkedIn/brand tools, internal systems, and polished web apps. Use taste-skill style discipline without blindly copying its more theatrical defaults.

## Core stance

Build interfaces that feel:
- clear before clever
- premium without being loud
- executive/product-grade, not portfolio-dribbble
- responsive and accessible by default
- complete, with real states and no placeholders

Do not over-style serious dashboards. Visual polish should improve trust, comprehension, and decision speed.

## Before coding or editing UI

1. Inspect the existing stack and files before choosing patterns.
2. Check `package.json` before importing third-party UI, animation, icon, state, or font packages.
3. Use the project’s existing framework and styling system unless the user asks to change it.
4. Prefer targeted upgrades over rewrites for existing products.
5. Identify the user’s intent:
   - new build
   - redesign/polish
   - audit only
   - component implementation
   - dashboard/data UI
   - landing/marketing page

## Default design dials

Use these as defaults and adjust based on the product context.

| Dial | Default | Meaning |
|---|---:|---|
| Design variance | 5/10 | enough asymmetry to avoid generic layout, restrained for business UI |
| Motion intensity | 3/10 | subtle hover/focus/transitions, no theatrical motion by default |
| Visual density | 5/10 | balanced product UI; dashboards may go 7, marketing pages may go 3 |

Escalate only when requested:
- portfolio/creative brand: variance 7-8, motion 5-6
- executive dashboard: variance 3-5, motion 1-3, density 6-8
- luxury/editorial page: variance 6-8, motion 3-5, density 2-4

## Design quality rules

### Typography

- Use the existing font if the product already has one. Do not churn fonts casually.
- If choosing a new font, prefer modern sans families with character: Geist, Satoshi, Outfit, Cabinet Grotesk, IBM Plex Sans, or similar.
- For dashboards, keep typography calm and highly readable. Avoid decorative serif display fonts.
- Limit paragraph width to roughly 60-75 characters.
- Use tighter tracking for large display text, normal tracking for body text, and tabular numbers for metrics.
- Avoid giant 5-line hero headings. Adjust width, font size, and line-height so the heading breathes.

### Color and surfaces

- Use one primary accent. Avoid competing accent colors.
- Avoid oversaturated AI-purple/neon gradients unless the brand explicitly calls for them.
- Prefer off-black and tinted neutrals over pure black.
- Keep gray families consistent: do not mix warm and cool grays randomly.
- Use cards only when they create meaningful grouping. For dense dashboards, separators and whitespace often beat card soup.
- Shadows should be subtle and physically plausible, not default gray blur everywhere.

### Layout

- Use CSS Grid for multi-column layouts. Avoid fragile flex percentage math.
- Use explicit containers, commonly 1200-1440px max width for product pages.
- Avoid default “centered hero + three equal feature cards” unless it is truly the right pattern.
- Break monotony with asymmetric grids, varied section rhythms, split layouts, or editorial alignment, but keep mobile simple.
- Never use `h-screen` for mobile-sensitive full-height sections. Prefer `min-h-[100dvh]` or content-driven spacing.
- On mobile, collapse aggressive desktop layouts to one clear column with safe spacing and no horizontal scroll.

### States and interaction

Every production UI needs states:
- loading: skeletons that match the layout shape
- empty: composed empty state with clear next action
- error: inline, specific, recoverable
- hover: visible but not noisy
- active/pressed: subtle `scale(0.98)` or `translateY(1px)`
- focus: keyboard-visible focus ring
- disabled: obvious and accessible

Do not ship a happy-path-only component if the UI can load, fail, be empty, or accept input.

### Motion

Default to restrained motion:
- transitions 150-300ms
- transform and opacity only
- no animation of `top`, `left`, `width`, or `height`
- no custom cursors
- no scroll-jacking
- no heavyweight GSAP/Framer dependency unless already installed or clearly justified

Use advanced motion only when it supports comprehension or the user explicitly wants a highly expressive marketing/portfolio experience.

### Content realism

- Replace placeholder names like John Doe, Jane Smith, Acme, and Lorem Ipsum with believable domain-relevant content.
- Avoid fake-perfect metrics like 99.99%, 50%, $100 unless they are real.
- Avoid generic AI copy: “elevate”, “seamless”, “unleash”, “next-gen”, “game-changing”, “transform your workflow”.
- For Ahmed/NASR work, use executive language: crisp, decision-oriented, operationally credible.

## Implementation rules

- Check dependencies before importing libraries. If a package is missing, either use native CSS/available packages or clearly state the install needed before relying on it.
- Keep component architecture simple. Split interactive leaf components only when needed.
- Preserve accessibility: semantic HTML, labels, ARIA only when semantic HTML is insufficient, keyboard states, contrast.
- Preserve performance: optimize images, avoid layout shifts, avoid repaint-heavy effects on scrolling containers.
- Do not introduce dead links, placeholder comments, TODOs, or unfinished branches.

## Audit workflow for existing UI

When asked to improve or review an existing frontend:

1. Inspect representative pages/components and global styles.
2. Produce a short diagnosis grouped by:
   - hierarchy
   - spacing/layout
   - color/surface
   - states/accessibility
   - responsiveness
   - content realism
3. Fix the highest-impact issues first. Prefer 3-7 targeted changes over a full redesign.
4. Verify with at least one concrete gate:
   - build/typecheck/lint
   - screenshot
   - responsive inspection
   - direct file inspection when no runtime exists

## Output format

For implementation closeout, report:
- files changed
- what improved visually/functionally
- checks run
- remaining risks, if any

For audit-only requests, use:

```markdown
## Verdict
[one-line assessment]

## Biggest issues
- [issue + why it matters]

## Recommended fixes
1. [highest leverage fix]
2. [next]
3. [next]

## Optional polish
- [nice-to-have]
```

## Quick preflight checklist

Before finalizing frontend work, verify:
- [ ] No placeholder comments, TODOs, fake links, or lorem ipsum remain unless intentionally part of demo data
- [ ] Loading, empty, error, focus, hover, disabled states are handled where relevant
- [ ] Mobile layout has no horizontal overflow
- [ ] Color contrast is readable
- [ ] Components use the existing stack and dependencies correctly
- [ ] Motion uses transform/opacity and respects reduced-motion where practical
- [ ] The result fits the product context, not a generic flashy template

## Reference files

Load these only when needed:
- `references/ui-audit-checklist.md` for deeper redesign audits
- `references/patterns.md` for recommended layout patterns by product type
