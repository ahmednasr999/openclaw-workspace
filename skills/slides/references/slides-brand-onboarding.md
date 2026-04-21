# Slides Brand Onboarding

Use this when the user wants a deck to match a company, product, or publication style rather than the default slide tokens.

This is a proposal workflow, not an automatic truth workflow.

Runnable helper:

```bash
python3 scripts/slides_brand_onboarding.py extracted-brand-signals.json --output planning/brand-token-proposal.md
```

Live website scan:

```bash
python3 scripts/slides_brand_onboarding.py --url https://example.com --output planning/brand-token-proposal.md
```

Browser-assisted extraction mode:

```bash
python3 scripts/slides_brand_onboarding.py --url https://example.com --browser --output planning/brand-token-proposal.md
```

Apply after approval:

```bash
python3 scripts/slides_brand_onboarding.py extracted-brand-signals.json --apply --output planning/brand-token-proposal.md
```

Sandbox showcase application:

```bash
python3 scripts/slides_apply_brand_example.py planning/brand-token-proposal.md --name "Brand Name" --output examples/brand-name-branded-showcase
```

One-shot brand demo workflow:

```bash
python3 scripts/slides_brand_demo.py --url https://example.com --name "Brand Name"
```

One-shot browser-assisted workflow:

```bash
python3 scripts/slides_brand_demo.py --url https://example.com --browser --name "Brand Name"
```

One-shot workflow with delivery-ready media copy:

```bash
python3 scripts/slides_brand_demo.py --url https://example.com --name "Brand Name" --copy-to-media
```

The workflow prints a `SUMMARY_JSON:` line at the end with:
- proposal path
- sandbox deck path
- pptx path
- montage path
- media path when `--copy-to-media` is used
- a `sendHint` object for OpenClaw-native delivery

---

## 1. First-run style gate

Before generating the first branded deck in a new task or project:

1. inspect `slides-style-guide.md`
2. if it still reflects the default neutral system, ask the user to choose one of:
   - use default style for now
   - infer a proposed style from a website or brand source
   - provide tokens manually

Do not silently ship default styling into a branded project if the user expects a matched look.

---

## 2. Inputs you can use

Preferred sources, in order:
- live website
- approved brand guide
- existing presentation or PDF
- company/product screenshots
- manually supplied palette and font notes

If the brand source is noisy, use it to propose tokens, not to claim certainty.

---

## 3. Output of onboarding

Produce a proposed mapping into semantic tokens:
- `bg`
- `surface`
- `surface-2`
- `text-primary`
- `text-secondary`
- `text-soft`
- `rule`
- `rule-strong`
- `accent`
- `accent-soft`

And optionally typography roles:
- `display`
- `title`
- `body`
- `meta`
- `data`
- `eyebrow`

Show the proposed diff before writing it.

---

## 4. Constraint checks

Before applying a proposed style:
- primary text must have strong contrast against the background
- accent must remain more saturated than the neutral system
- supporting text must still be readable at slide sizes
- the system must still allow one clear focal accent per slide

If the extracted brand system is too colorful or too inconsistent:
- reduce it to one accent and a restrained neutral family
- explain the simplification briefly

---

## 5. Important warnings

- brand extraction is approximate
- websites often have inconsistent token usage
- typography on the site may not map cleanly to slide roles
- use preview and approval before writing anything permanent

---

## 6. Write policy

When the user approves:
- write the updated semantic tokens into `slides-style-guide.md`
- do not hardcode the brand values into pattern references
- keep the brand logic localized to the style guide

Validation helper:

```bash
python3 scripts/slides_brand_onboarding_validate.py
python3 scripts/slides_apply_brand_example_validate.py
python3 scripts/slides_brand_demo_validate.py
```
