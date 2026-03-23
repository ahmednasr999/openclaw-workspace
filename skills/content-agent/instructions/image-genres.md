# LinkedIn Image Genres

All images: 1080x1080px, HTML/CSS + Chromium headless screenshot. No AI image generation.

## Brand Tokens (Canonical)

```
Background:  #0D1421
Card BG:     #1A2332
Text Primary: #FFFFFF
Text Secondary: #8B95A5
Footer Border: #1E293B
Font: Inter (primary), Poppins (accent)
Footer: "Ahmed Nasr / Digital Transformation Executive / PMP CSM CSPO"
```

## Accent Colors (One per post, match to theme)

| Color | Hex | Use for |
|-------|-----|---------|
| Blue | #3B82F6 | PMO, governance, frameworks |
| Teal | #14B8A6 | Digital transformation, technology |
| Red | #EF4444 | Bold claims, warnings, contrarian takes |
| Yellow | #F59E0B | Data, metrics, achievements |
| Purple | #8B5CF6 | AI, innovation, future-facing |

## Genre Definitions

### 1. Stat Card (for Data posts)

One dominant number. One supporting line. That's it.

```
Layout:
- Top-left: small category badge (13px, 4px radius, accent border)
- Center: the number (64px, weight 800, accent color)
- Below number: one-line context (20px, #8B95A5)
- Footer at bottom

Example:
Badge: "GCC Healthcare"
Number: "83%"
Context: "of regulated transformations fail in the first 18 months"
```

### 2. Framework Diagram (for Expertise posts)

Named concept with 3-5 components. Clean, structured.

```
Layout:
- Top: framework name (36px, weight 700, white)
- Middle: 3-5 items in cards (#1A2332 bg, 4px left accent border)
  - Each card: icon/number + title (18px bold) + one-line description (14px, #8B95A5)
- Footer at bottom

Example:
Title: "The 3-Country Governance Model"
Cards:
1. Local Autonomy — Each country owns daily operations
2. Regional Standards — Shared KPIs and reporting cadence  
3. Central Oversight — Monthly executive steering committee
```

### 3. Statement Card (for Opinion posts)

One bold line. Maximum visual impact.

```
Layout:
- Top-left: small document icon or badge
- Center: the statement (40px, weight 700, white, max 2 lines)
- Optional: one supporting line below (16px, #8B95A5)
- Footer at bottom

Example:
Statement: "Your PMO is measuring the wrong things."
Support: "And it's costing you millions."
```

### 4. Quote Card (for Story posts)

A key quote or moment from the story.

```
Layout:
- Large opening quotation mark (accent color, decorative)
- Quote text (32px, weight 600, white, max 3 lines)
- Attribution: "— Ahmed Nasr" (16px, #8B95A5)
- Footer at bottom

Example:
Quote: "The meeting that saved a $50M program lasted seven minutes."
```

### 5. Minimal Card (for Behind-the-Scenes posts)

Almost empty. One line. Understated.

```
Layout:
- Top section: mostly empty space
- Single line of text (24px, weight 500, #8B95A5)
- Subtle accent element (thin line, small shape)
- Footer at bottom

Example:
Text: "Sometimes the hardest decision is the one you don't make."
```

## Genre-to-Post-Type Mapping

| Post Type | Primary Genre | Alternate |
|-----------|--------------|-----------|
| Story | Quote Card | Statement Card |
| Expertise | Framework Diagram | Stat Card |
| Opinion | Statement Card | Quote Card |
| Data | Stat Card | Framework Diagram |
| BTS | Minimal Card | Quote Card |

## Technical Rules

- `overflow: hidden` on html/body (no scrollbars)
- Content in upper 60% of canvas
- All text left-aligned
- Author credentials in footer use #EF4444 (red), not teal
- Footer: author name 20px/600, title 14px/400
- Footer positioned ~100px from bottom with #1E293B top border
- Category badge: 13px font, 4px border-radius, accent-colored left border

## No-Image Posts

Some posts perform better without images. If the content is pure text and the engagement experiment indicates text-only wins, skip image generation. Log `"has_image": false` in performance data.
