# Slides Style Guide

Single source of truth for visual tokens used by editorial slide patterns.

Use semantic roles, not raw visual instructions, when designing or reviewing slides.

---

## 1. Color tokens

| Token | Purpose | Default |
|---|---|---|
| `bg` | Main slide background | `F5F1EA` |
| `surface` | Primary module/card fill | `FFFDFC` |
| `surface-2` | Secondary surface / quiet blocks | `ECE6DE` |
| `text-primary` | Headline / primary text | `171411` |
| `text-secondary` | Body copy / supporting text | `4B443D` |
| `text-soft` | Meta / captions / quiet labels | `7A6F66` |
| `rule` | Hairline rules / subtle borders | `D8CEC2` |
| `rule-strong` | Stronger separators / key outlines | `B9AB9B` |
| `accent` | Focal color, 1 main accent | `C86432` |
| `accent-soft` | Accent-tinted fill | `F3E1D8` |
| `warning` | Caution / risk callout | `B85C38` |
| `success` | Positive signal / progress | `4B7A5A` |
| `data-link` | Data / API / timeline connector color | `2E6FD0` |

Rules:
- one accent dominates, not multiple competing accents
- avoid pure black and pure white by default
- keep neutral system warm unless the project requires a colder system

---

## 2. Typography roles

| Token | Purpose | Default guidance |
|---|---|---|
| `display` | Hero cover statement | 38-58 pt |
| `title` | Slide title | 24-34 pt |
| `section` | Divider / section headline | 30-42 pt |
| `body` | Main explanatory text | 12-18 pt |
| `caption` | Secondary explanatory text | 10-12 pt |
| `meta` | Date, source, footnote, labels | 8-10 pt |
| `data` | Metric number / tabular emphasis | 18-44 pt |
| `eyebrow` | Small label / kicker / category | 8-11 pt, tracked |

Rules:
- display and title sizes must not drift too close together
- body copy should rarely use bold
- metadata should feel quiet, not decorative
- use mono selectively for data, labels, or technical context, not by default everywhere

---

## 3. Geometry and spacing tokens

| Token | Purpose | Default |
|---|---|---|
| `grid-unit` | Base spacing unit | `4 pt` |
| `page-margin-x` | Horizontal safe margin | `36-52 pt` |
| `page-margin-y` | Vertical safe margin | `24-40 pt` |
| `module-gap` | Gap between major regions | `20-32 pt` |
| `card-radius` | Default rounded treatment | `6-10 pt` |
| `rule-weight` | Standard line weight | `0.75-1.25 pt` |

Rules:
- align to a small spacing vocabulary
- do not mix too many corner radii
- generous spacing is preferred over squeezing more content in

---

## 4. Usage rules

### Accent usage
- 1 dominant accent per slide
- 2 accent moments max on dense comparison slides
- do not color-code everything important

### Surface usage
- surfaces should create structure, not dashboard clutter
- large open fields are allowed and often desirable

### Border usage
- prefer thin rules and selective outlines
- heavy border grids usually make slides feel templated

---

## 5. Brand customization rule

When a project requires branding:
- use `slides-brand-onboarding.md`
- map brand tokens into these semantic roles
- do not rewrite pattern files with raw brand values

All pattern references should consume semantic roles from this file.

