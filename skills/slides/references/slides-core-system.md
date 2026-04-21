# Slides Core System

This file is the editorial operating system for the `slides` skill.

Use it when:
- creating a new deck from scratch
- raising visual quality beyond normal presentation output
- deciding slide patterns before authoring
- reviewing whether a deck feels designed or merely arranged

Do not load every pattern file by default. Load this file, then load only the specific `pattern-*.md` references required by the current deck.

---

## 1. Philosophy

The deck should read like a designed artifact, not a generic template instance.

Key principles:
- one dominant idea per slide
- one dominant focal element per slide
- fewer stronger elements beats many tidy weak ones
- asymmetry is usually better than safe balance
- hierarchy should be obvious in one glance
- typography should do real visual work, not just hold text
- premium quality usually comes from subtraction plus stronger contrast

If a slide looks neat, balanced, and harmless, it is probably under-designed.

---

## 2. Non-negotiable rules

### One focal element
Each slide needs one element that clearly dominates:
- oversized statement
- hero metric
- dominant visual field
- single decisive comparison
- strong headline block

If the eye does not know where to land first, the slide failed.

### Equal-weight layouts are suspicious
Avoid layouts where all cards, columns, or modules feel equally important unless the slide is a true symmetric comparison.

### Cards are not the default structure
Do not solve every slide with a grid of outlined boxes.

Use cards only when:
- the content is genuinely modular
- comparison requires parallel structure
- the slide needs container logic, not decoration

### Remove one thing before adding one thing
Before adding another icon, label, card, or rule, remove one existing element and see if the slide gets stronger.

### Pattern first, layout second
Every slide must be classified into exactly one pattern before composition begins.

---

## 3. Information density targets

Default density target by slide role:

| Slide role | Density target |
|---|---|
| Cover | 2/10 |
| Section divider | 2/10 |
| Thesis / summary | 3/10 |
| Metric | 3/10 |
| Comparison | 4/10 |
| Agenda | 4/10 |
| Standard explainer | 5/10 |

Rules:
- low density is a feature, not a gap
- density should come from structure and hierarchy, not visual clutter
- if content exceeds the density target, split the slide

---

## 4. Slide rhythm across a deck

Deck rhythm matters as much as individual slide quality.

Rules:
- every 2 to 3 slides, create a hero moment
- avoid repeating the same structural composition on adjacent slides
- alternate dense and sparse moments deliberately
- section dividers should create pause and reset
- closing slides should feel decisive, not administrative

Failure signals:
- 3 slides in a row with the same grid
- every slide looks like a content page
- no visual crescendo in the deck

---

## 5. Pattern selection guidance

Classify each slide into one of these editorial patterns:
- cover
- section-divider
- agenda
- thesis-summary
- metric
- comparison
- process-timeline
- 2-column-explainer
- full-bleed-visual
- closing

In phase 1, only some of these patterns may have dedicated reference files. Use the closest defined pattern and keep the rest under legacy slide-type guidance when necessary.

---

## 6. Composition guidance

### Use asymmetry intentionally
Prefer compositions where one side or region clearly carries more weight.

### Let typography carry weight
Do not rely only on boxes and shapes.

Ways typography should work harder:
- scale contrast
- line-break control
- serif vs sans contrast when appropriate
- strong headline blocks
- restrained metadata systems

### Negative space is structural
Whitespace is not empty area. It is how you create hierarchy, calm, and premium feel.

### One accent color, restrained use
Use accent for:
- focal emphasis
- one highlighted metric
- one recommendation state
- one directional cue

Do not use accent on every important thing.

---

## 7. Editorial quality questions

Ask these while authoring and in QA:
- what is the focal point?
- what pattern is this slide using?
- is one element clearly dominant?
- is this composition editorial or template-like?
- can I remove one element and improve it?
- is the accent restrained enough?
- is there a stronger asymmetric arrangement available?

If the slide feels correct but emotionally flat, strengthen hierarchy before adding decoration.

