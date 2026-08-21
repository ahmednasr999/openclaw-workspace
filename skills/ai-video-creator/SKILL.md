---
name: ai-video-creator
description: Turn creative briefs, campaign concepts, product references, scripts, or existing AI-video prompts into coherent production-ready video packages. Use for commercials, social videos, cinematic reveals, sports or fashion films, product launches, storyboards, shot lists, image-to-video prompts, reference bibles, continuity control, edit and sound plans, rights/disclosure checks, shot manifests, QA, and repair plans. Also use when auditing or restructuring oversized multi-scene video prompts into controllable per-shot generation instructions.
---

# AI Video Creator

Build a film as a controlled system: story, references, shots, generation, edit, and verification. Preserve the user's creative intent while making every generated clip testable and repairable.

## Choose the delivery mode

Select the smallest mode that completes the request.

- **Fast mode:** Deliver a premise, assumptions, narrative arc, essential reference locks, concise shot list, one prompt per shot, and edit/audio notes. Use for ideation, early approval, or short social content.
- **Production mode:** Add a reference bible, time-coded script, complete shot manifest, storyboard directions, acceptance criteria, rights/disclosure record, post-production plan, QA log, and repair strategy. Use for approved concepts, paid work, complex continuity, real people, or exact products.
- **Audit mode:** Diagnose an existing brief or prompt. Separate creative strengths from production risks, identify rights or claims issues, and provide a prioritized rewrite plan. Do not silently replace the user's concept.

State the selected mode and assumptions. Ask only when a missing answer materially changes rights, budget, platform, or the central story. Otherwise infer reasonable defaults and proceed.

## Run the workflow

### 1. Normalize the brief

Capture or infer:

- goal and CTA;
- audience and viewing context;
- duration, aspect ratio, platform, language, and deliverable variants;
- product, brand, people, locations, mandatory copy, and claims;
- supplied references and which one wins if references conflict;
- realism, tone, pacing, audio, deadline, tool constraints, and approval status.

Do not default every request to 30 seconds or 16:9. Derive duration and format from the platform and purpose. For a short social ad with no format stated, propose 9:16 and a duration range instead of pretending the choice is settled.

### 2. Clear the rights and truth gate

Read [references/rights-and-disclosure.md](references/rights-and-disclosure.md) whenever the work includes a real person, trademark, logo, copyrighted design, recognizable property, product claim, political context, or fictional announcement.

Record the status as `owned`, `approved`, `licensed`, `public-domain`, `not-required`, `pending`, or `unknown`. Do not present `pending` or `unknown` as cleared. For speculative public-facing work, add an unambiguous disclosure and avoid official-looking claims.

### 3. Build the reference bible

Assign stable IDs only to references that matter:

- `CHAR-##` character or likeness;
- `WARD-##` wardrobe;
- `PROD-##` product or packaging;
- `ENV-##` environment;
- `STYLE-##` visual treatment;
- `CAM-##` camera language;
- `LIGHT-##` lighting;
- `GRADE-##` color grade;
- `AUDIO-##` music, voice, or sound reference.

For every critical reference, define:

1. what must remain locked;
2. what may vary naturally;
3. what must never appear;
4. the primary asset when references conflict.

Do not promise exact logos, packaging text, jersey names, or small typography from generative video alone. Plan reference-controlled stills, clean plates, tracking, compositing, or post typography when exact readability matters.

### 4. Design the story before the shots

Write a one-sentence premise, viewer insight, emotional promise, and narrative arc. Give each beat one job:

`hook -> curiosity/tension -> escalation -> reveal -> payoff -> CTA`

Delay the highest-value reveal only when suspense supports the objective. For direct-response work, make the product and benefit legible early enough to sell.

### 5. Convert beats into controllable shots

Create one row per generated clip. Each shot must contain:

- one primary subject;
- one primary action;
- one motivated camera move or a locked camera;
- a clear opening state and ending state;
- reference IDs;
- duration and story purpose;
- transition handles;
- audio cue;
- objective acceptance criteria.

Split a shot when it asks the generator to change location, reveal multiple identities, perform several complex actions, or execute an edit. Create pacing, typography, speed ramps, freeze frames, and most transitions in post.

Keep total shot duration consistent with the master duration. Vary framing deliberately; do not fill a film with identical push-ins, drone shots, or slow motion.

### 6. Write per-shot prompts

Read [references/prompt-architecture.md](references/prompt-architecture.md) before drafting generation prompts. Write one prompt per clip, repeat critical locks, and specify the start frame, action, camera, environment, lighting, ending frame, continuity handoff, and negative constraints.

Keep prompts model-neutral unless the user names a tool. If the workflow depends on a current model feature, price, duration limit, reference count, or resolution, verify it from a current reliable source before asserting it.

Use image generation for reference sheets, keyframes, hero stills, and composition targets. Use image-to-video for continuity-critical shots when a locked start frame is available. Use text-to-video mainly for low-risk atmosphere or exploratory footage. Route compositing, typography, retiming, sound, and final delivery to post-production.

### 7. Design edit and sound

Specify:

- cut rhythm and transition logic;
- music arc and beat landmarks;
- sound effects tied to actions;
- voiceover or dialogue timing;
- on-screen copy, CTA, disclaimer, and safe-area placement;
- master and cutdown exports.

Treat audio as part of the story, not a final decoration. Keep exact copy out of generated frames and add it in post unless the chosen tool has been tested on that exact requirement.

### 8. Define acceptance and repair

Set objective criteria per shot, including the relevant subset of:

- identity, product, wardrobe, or environment match;
- anatomy and physical plausibility;
- readable silhouette and composition;
- camera path and ending frame;
- stable background and no morphing or flicker;
- brand-safe text and marks;
- clean handles for the next edit;
- correct duration and export specification.

When a shot fails, diagnose the smallest failing dimension. Repair in this order:

1. replace or improve the input reference;
2. simplify the action;
3. lock the camera or reduce movement;
4. split the shot;
5. regenerate only the failed clip;
6. patch with compositing, cleanup, retiming, or a cutaway;
7. redesign the beat only when the core action remains unreliable.

Never regenerate an entire film to fix one defective shot.

## Package the output

For Fast mode, deliver:

1. premise, assumptions, and format;
2. reference locks;
3. time-coded shot list;
4. one prompt per shot;
5. edit, sound, CTA, and main risks.

For Production mode, deliver:

1. normalized brief and approval gates;
2. creative treatment and time-coded script;
3. reference bible;
4. storyboard directions and shot list;
5. still/keyframe and video prompts;
6. manifest and folder naming plan;
7. edit, audio, typography, and export plan;
8. rights/disclosure register;
9. QA checklist, revision log, and repair priorities.

Copy [assets/shot-manifest-template.json](assets/shot-manifest-template.json) when a machine-readable manifest is useful. Validate it with:

```bash
python3 scripts/validate-shot-manifest.py path/to/shot-manifest.json
```

Use `--strict` before handoff to fail on unresolved warnings.

## Load the relevant examples only

- Read [references/honey-example.md](references/honey-example.md) for product packaging, liquid simulation, macro food photography, or ultra-short social ads.
- Read [references/salah-case-study.md](references/salah-case-study.md) for sports reveals, real-person likeness, fan/city impact stories, or fictional announcement concepts.

Treat examples as patterns, not copy blocks. Replace their assumptions, rights status, references, and claims with the current project's facts.

## Enforce the quality bar

- Prefer a coherent film over a list of spectacle shots.
- Preserve continuity through references, not adjectives alone.
- Make every shot earn its duration.
- Separate generation instructions from edit instructions.
- Use exact, observable acceptance criteria.
- State unresolved rights, claims, asset, or capability risks plainly.
- Never claim a render, resolution, continuity result, permission, or public approval that has not been verified.
