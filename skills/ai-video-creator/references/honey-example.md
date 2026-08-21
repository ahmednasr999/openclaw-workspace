# Standardized Example: Ten-Second Honey Product Film

This example converts the imported ultra-fast honey mega-prompt into a controllable 9:16 production package. Reuse the method, not the product claims or exact creative.

## 1. Normalized brief

- **Goal:** Premium product awareness in a ten-second social ad.
- **Format:** 9:16, 10.0 seconds, sound-on and sound-off safe.
- **Core promise:** Golden richness and crafted quality.
- **CTA:** Brand-approved end-card copy, added in post.
- **Reference:** The uploaded bottle is `PROD-01` and is the primary packaging reference.
- **Claims gate:** “Pure,” “natural,” origin, nutrition, and health claims remain pending until brand evidence is supplied.
- **Production decision:** Generate clean product and liquid plates; composite the approved bottle label and exact logo in post.

The original request for roughly twenty half-second moments is reduced to eight shots. This preserves energy while giving product geometry, liquid physics, and editing room to survive.

## 2. Reference bible

| ID | Lock | May vary | Never allow |
|---|---|---|---|
| `PROD-01` | Bottle silhouette, cap geometry, fill level, material, label placement, palette, proportions | Reflections and viewing angle | Redesigned bottle, invented text, missing cap |
| `STYLE-01` | Premium macro food photography, warm gold/amber palette, clean luxury surfaces | Background depth and bokeh | Plastic CGI look, dirty food styling |
| `LIGHT-01` | Warm backlight, narrow rim, controlled highlights | Intensity by shot | Blown label area, flat muddy amber |
| `AUDIO-01` | Rising pulse, viscous liquid details, restrained impact | Exact instrumentation | Cartoon splats, busy stock stingers |

## 3. Story and edit map

`formation -> recognition -> ingredient energy -> pour -> appetite -> detail -> momentum -> hero/CTA`

| Shot | Time | Dur. | Generated clip job | Post job | Acceptance focus |
|---|---:|---:|---|---|---|
| `S001` | 0.0 | 1.0 | Honey stream converges into a bottle-shaped silhouette | Cut before exact label is required | Clean recognizable silhouette; plausible gravity |
| `S002` | 1.0 | 1.0 | Approved bottle hero rotates slightly against warm rim light | Composite exact pack and label | Geometry and cap remain stable |
| `S003` | 2.0 | 1.1 | Honeycomb enters foreground around a locked hero bottle | Add two or three clean particle layers | Product remains unobstructed |
| `S004` | 3.1 | 1.2 | Macro honey stream lands on a wooden dipper | Sound bridge into appetite shot | Continuous contact; no clipping |
| `S005` | 4.3 | 1.2 | Honey ribbons across one breakfast food surface | Match cut using amber curve | One food hero; no object duplication |
| `S006` | 5.5 | 1.0 | Macro bottle material and honey texture | Insert approved label close-up | Stable texture; no generated text |
| `S007` | 6.5 | 1.3 | Product rises through one elegant honey ring | Add beat-synced speed change | One camera orbit; clean end hold |
| `S008` | 7.8 | 2.2 | Centered bottle on reflective surface with slow push-in | Composite exact product, CTA, disclosure, logo | 24+ clean final frames and safe text area |

Do not ask a single video model to perform every row. Render each shot separately, preserving handles before and after the intended cut.

## 4. Example hero shot prompt

```text
SHOT S008 — FINAL PRODUCT HERO
DURATION: 2.2 seconds | FORMAT: vertical 9:16 | PURPOSE: recognition and CTA hold

REFERENCE CONTROL
Use PROD-01 as the primary bottle reference. Preserve the bottle silhouette, cap geometry, fill level, transparent material, label placement, palette, and proportions. The approved pack-shot asset wins if any visual reference conflicts.

OPENING STATE
The bottle stands centered on a clean dark-gold reflective surface. A low ring of honey rests around the base. The upper-right area remains quiet for post typography.

PRIMARY ACTION
The honey at the base moves in one slow viscous wave while a few small droplets drift through the backlight.

CAMERA
Eye-level product camera, subtle 85 mm commercial lens character, one slow 8% push-in, no orbit, no handheld motion.

ENVIRONMENT AND LIGHT
Warm golden backlight, narrow rim on both bottle edges, controlled specular highlights, soft volumetric haze, deep clean background.

ENDING STATE
End on a centered hero composition with at least 24 frames of stable hold and unobstructed label and CTA zones.

CONTINUITY HANDOFF
Maintain the clockwise honey curve established in S007.

NEGATIVE CONSTRAINTS
No bottle redesign, cap deformation, label mutation, invented text, duplicate bottle, liquid clipping, excessive particles, focus pumping, flicker, or camera shake.
```

## 5. Audio and copy

- Use one rising rhythmic bed rather than a new sound every half second.
- Anchor four sound moments: formation pull, dipper contact, ring sweep, final low impact.
- Add exact logo, claim, CTA, and legal line in post.
- Produce a sound-off version whose visual story remains legible.

## 6. Repair priorities

1. If the bottle drifts, replace it with the approved pack shot and track reflections around it.
2. If honey physics fail, shorten the action and cut to a macro insert.
3. If the label is unreadable, remove it from generation and composite the approved label.
4. If the ten-second cut feels chaotic, lengthen `S002` and `S008` before adding more shots.
5. Do not use “8K” as a quality instruction; verify actual render and delivery resolution separately.
