---
name: Image
version: 1.0.3
description: Process, optimize, and manage images with web optimization, color management, platform specs, and e-commerce standards.
changelog: "Add scope and security notes for scanner compliance"
---

## Scope

This skill is a **reference guide only**. It provides:
- Format selection guidelines
- Compression settings
- Platform dimension specs
- Command examples for manual use

This skill does NOT:
- Execute commands automatically
- Access or modify files without user request
- Require API credentials (CDN services are optional)
- Store or track any data

---

## Quick Reference

| Task | Load |
|------|------|
| Web optimization, formats, responsive | `web.md` |
| Color profiles, metadata, RAW, print | `photography.md` |
| Social media dimensions by platform | `social.md` |
| E-commerce/marketplace standards | `ecommerce.md` |
| ImageMagick/PIL commands | `commands.md` |

---

## Format Selection

| Content | Format | Reason |
|---------|--------|--------|
| Photos | WebP (JPEG fallback) | 25-35% smaller |
| Icons, logos | SVG | Scalable, tiny |
| Screenshots with text | PNG | Sharp edges |
| Transparency + photo | WebP or PNG-24 | Alpha support |
| Animation | WebP or MP4 | NOT GIF (5-10x larger) |

---

## File Size Budgets

- **Hero images:** MAX 200KB (ideally <150KB)
- **Content images:** MAX 100KB
- **Thumbnails:** MAX 30KB
- **Icons (raster):** MAX 5KB
- **Total page load:** MAX 1.5MB images

---

## Quality Levels

| Format | Hero | General | Thumbnails |
|--------|------|---------|------------|
| JPEG | 80-85% | 70-75% | 60-65% |
| WebP | 80-82% | 72-78% | 60-70% |

---

## Retina/HiDPI

- **2x required** for standard Retina
- **3x only** for iPhone Plus/Max
- 400px displayed needs **800px source**

---

## Before Processing Checklist

- [ ] Target format determined (web vs print)
- [ ] Color profile appropriate (sRGB for web)
- [ ] Dimensions/aspect ratio defined
- [ ] Compression quality set
- [ ] Metadata handling decided

---

## Learned Improvements

### 2026-04-25 - Weekly Skill Tune-Up

**Reviewed lessons:**
- 2026-04-23, visual briefs need semantic background alignment and exact signature/footer rules.
- 2026-04-23, do not keep polishing a visual direction after Ahmed clearly dislikes it.
- 2026-04-23, premium LinkedIn visuals cannot place core text over Ahmed's face or rely on generic AI portrait layouts.

**Improvement recommendation:**
1. **Add a social-visual brief lock before generation.** For LinkedIn or branded social assets, capture the required topic/background metaphor, portrait requirement, asset type, and exact footer/signature before producing or optimizing an image.
2. **Reject non-native social compositions early.** Do not present poster, magazine-cover, or generic AI portrait layouts when Ahmed asked for a feed-native LinkedIn asset. The image should pass a quick feed test: clear hook hierarchy, clean text zone, and no copy over the face or suit.
3. **Stop failed visual directions instead of iterating them.** If Ahmed dislikes the direction, switch to 2-3 materially different concepts or ask one sharp diagnostic question. Do not spend more turns polishing the same weak concept.
4. **Create a future `eval/checklist.md`.** Keep it binary: semantic background matches topic, asset type matches request, text is readable, no text on face, signature is exact, output feels LinkedIn-native.
