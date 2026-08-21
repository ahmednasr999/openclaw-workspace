# Prompt Architecture and Production Controls

Use this reference when writing image, keyframe, or video prompts and when converting a multi-scene prompt into a shot-based production package.

## Contents

1. Prompt stack
2. Still and keyframe prompts
3. Video shot prompts
4. Negative constraints
5. Acceptance criteria
6. Tool routing
7. Repair patterns

## 1. Prompt stack

Keep four layers separate:

1. **Project constants:** approved references, visual rules, disclosure, aspect ratio, and grade.
2. **Shot intent:** story purpose, emotion, and information the viewer must receive.
3. **Generation prompt:** what the model must render in one clip.
4. **Post instructions:** cuts, text, transitions, speed changes, sound, and compositing.

Do not bury post-production edits inside a generation prompt.

## 2. Still and keyframe prompt

```text
PURPOSE
[Approval frame, character sheet, product hero, environment keyframe, or transition target.]

REFERENCE CONTROL
Use [reference IDs]. Preserve [locked traits]. [Primary asset] wins if references conflict.

SUBJECT AND STATE
[One subject in one clear pose or material state.]

COMPOSITION
[Aspect ratio, framing, placement, foreground/background, negative space, safe area.]

CAMERA AND OPTICS
[Camera position, lens character, depth of field, perspective.]

LIGHT AND MATERIAL RESPONSE
[Sources, direction, contrast, reflections, translucency, atmosphere.]

STYLE
[Photographic or graphic treatment stated descriptively.]

NEGATIVE CONSTRAINTS
[Identity drift, redesigned product, invented text, anatomy errors, duplicate objects, etc.]
```

For character or product sheets, request a neutral reference view before dramatic angles. Generate typography and logos as clean post assets when exact spelling is mandatory.

## 3. Video shot prompt

```text
SHOT [ID] — [SHORT NAME]
DURATION: [seconds] | FORMAT: [aspect ratio] | PURPOSE: [story job]

REFERENCE CONTROL
Use [reference IDs]. Preserve [locked identity, geometry, wardrobe, materials, palette].

OPENING STATE
[Exact first-frame composition and subject state.]

PRIMARY ACTION
[One subject performs one action with realistic physical behavior.]

CAMERA
[Position, framing, movement, speed, lens character, screen direction.]

ENVIRONMENT AND LIGHT
[Location, depth layers, practical sources, atmosphere, reflections.]

ENDING STATE
[Composition and motion state required for the next cut.]

CONTINUITY HANDOFF
[Match direction, object position, eyeline, motion, color, or shape for the adjacent shot.]

NEGATIVE CONSTRAINTS
[Only the failures relevant to this shot.]
```

Write the motion in chronological order. Use concrete physical verbs. Avoid incompatible directions such as “locked tripod” and “aggressive orbit” in the same shot.

## 4. Negative constraints

Prioritize likely failures instead of pasting a universal negative list. Common categories:

- identity drift, age shift, face substitution;
- altered product geometry, cap, label placement, color, material, or proportions;
- invented or misspelled text, logos, numbers, or sponsor marks;
- extra limbs, duplicate objects, unstable hands, broken contact physics;
- liquid clipping, impossible viscosity, gravity errors, object penetration;
- flicker, morphing, texture crawl, unstable background;
- unmotivated camera motion, focus pumping, abrupt speed changes;
- stereotypes, demeaning behavior, or false official framing.

## 5. Acceptance criteria

Make criteria binary or inspectable. Weak: “looks cinematic.” Strong:

- `PROD-01` bottle silhouette and cap geometry match the approved hero still throughout.
- The honey stream contacts the dipper continuously without clipping.
- The camera ends on a centered medium close-up with at least 12 frames of clean hold.
- No generated text appears; the label area remains unobstructed for compositing.
- The face matches `CHAR-01` in the final 24 frames without visible morphing.

Use subjective criteria only for intentional human review: performance authenticity, emotional tone, taste level, and rhythm.

## 6. Tool routing

Route by risk and evidence:

| Need | Preferred production approach |
|---|---|
| Stable character/product | Reference sheet or approved still, then image-to-video |
| Exact label, jersey name, UI, or CTA | Track and composite in post |
| Complex liquid or cloth | Short action, controlled camera, multiple tests, fallback insert |
| Atmospheric establishing shot | Text-to-video may be sufficient |
| Complex reveal | Several clips joined in the edit |
| Fast iteration | Low-cost draft passes before hero renders |
| Final polish | NLE, compositing, sound mix, grade, and QC |

Use the user's selected stack when viable. Verify current features and limits before recommending a named model as a dependency.

## 7. Repair patterns

| Failure | First repair | Fallback |
|---|---|---|
| Product redesign | Stronger hero still and tighter crop | Composite approved pack shot |
| Face drift | Shorter clip, reduced head rotation | Cut before drift or use profile insert |
| Unreadable text | Remove text request | Add tracked typography in post |
| Broken liquid | Reduce simultaneous action | Generate liquid insert separately |
| Chaotic crowd | Lock camera and reduce foreground motion | Layer crowd plates in post |
| Transition failure | Generate clean ending hold | Use a cut, sound bridge, or graphic match |
| Timing mismatch | Retiming within safe range | Re-render only that clip |
