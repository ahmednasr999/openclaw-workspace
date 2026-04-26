# AI Image Model Benchmark Sheet

Date: 2026-04-23
Owner: Ahmed / NASR
Purpose: Evaluate whether a new image model is actually useful for Ahmed's real workflows.

## How to use
- Run all 12 tests on the same model.
- Score each test from 1 to 5 on the rubric below.
- Total per test: /30
- Production-grade threshold: 20/30 minimum
- Strategic-use threshold: at least 8 of 12 tests must pass, with no failure in identity preservation, typography, or executive-content clarity.

## Scoring rubric
Score each category from 1 to 5:
1. Likeness / consistency
2. Instruction following
3. Typography quality
4. Business usefulness
5. Reusability
6. Production readiness

### Score meaning
- 5 = excellent, immediately usable
- 4 = strong, minor cleanup only
- 3 = workable with noticeable fixes
- 2 = weak, major cleanup needed
- 1 = failed or not usable

---

## Test 1 - Executive headshot upgrade
Goal: Convert a normal Ahmed photo into a premium studio-grade executive headshot.

Prompt shape:
- Transform this portrait into a premium executive studio headshot.
- Keep facial identity accurate.
- Clean lighting, luxury corporate tone, realistic skin, tailored suit, neutral elegant background.
- No beauty-filter look, no exaggerated jawline, no fake teeth, no AI glow.

Pass if:
- Still clearly Ahmed
- Premium and credible
- No face drift or plastic skin

---

## Test 2 - Cinematic LinkedIn statement card
Goal: Generate a high-authority social visual for a strong executive statement.

Prompt shape:
- Create a cinematic editorial LinkedIn visual for the statement: "AI should remove reporting drag, not create more process."
- Premium typography, strong hierarchy, dark elegant palette, operator-grade tone.
- Designed for mobile readability.

Pass if:
- Readable in 2 seconds on mobile
- Feels premium, not templated
- Matches thesis visually

---

## Test 3 - Carousel cover slide
Goal: Create a strong first slide for a LinkedIn carousel.

Prompt shape:
- Design a LinkedIn carousel cover slide titled: "5 PMO workflows AI can accelerate this quarter"
- Clean editorial layout, bold cover hierarchy, premium business design.
- Keep it minimal and high-trust.

Pass if:
- Clear headline hierarchy
- Strong cover energy
- Looks like a real premium carousel cover

---

## Test 4 - PMO framework diagram
Goal: Test whether the model can produce useful executive-process visuals.

Prompt shape:
- Create a clean executive framework diagram showing: Inputs -> Decision Engine -> Prioritization -> Execution Tracking -> Executive Review.
- Board-safe style, simple labels, readable layout, no clutter.

Pass if:
- Logic is understandable immediately
- Diagram is readable and board-safe
- No confusing visual noise

---

## Test 5 - Transformation roadmap visual
Goal: See if the model can create a credible roadmap graphic for a deck.

Prompt shape:
- Create a 3-phase transformation roadmap visual: Stabilize, Scale, Optimize.
- Executive presentation style, minimal color palette, clean milestone structure.

Pass if:
- Timeline logic is clear
- Suitable for a PPTX deck
- Not overdesigned or childish

---

## Test 6 - Dashboard mockup
Goal: Test business UI quality.

Prompt shape:
- Design an executive dashboard for a transformation office.
- Show delivery health, risks, milestone status, financial variance, and top decisions needed.
- Make it realistic, modern, and presentation-ready.

Pass if:
- Realistic hierarchy
- Good information density
- Could actually support a business discussion

---

## Test 7 - Controlled background swap
Goal: Test edit precision.

Prompt shape:
- Keep the person exactly the same.
- Only change the background to a refined executive office setting.
- Do not alter clothing, pose, face, or framing.

Pass if:
- Only the requested change happens
- Identity and pose remain stable
- No hidden collateral edits

---

## Test 8 - Controlled lighting fix
Goal: Test local edit quality without composition damage.

Prompt shape:
- Improve lighting only.
- Preserve face, background, outfit, camera angle, and crop exactly.
- Make the image cleaner and more professional without changing identity.

Pass if:
- Lighting improves
- Everything else stays intact
- No fake smoothing or identity drift

---

## Test 9 - Identity consistency across 3 variations
Goal: Test whether the model can keep Ahmed consistent across outputs.

Prompt shape:
- Generate 3 variations of the same executive portrait concept.
- Keep the same facial identity, age, expression family, build, and overall look.
- Vary only pose and framing slightly.

Pass if:
- All 3 still look like the same person
- No age/race/face drift
- Consistent styling quality

---

## Test 10 - Typography and print cleanliness
Goal: Stress-test text rendering.

Prompt shape:
- Design a premium poster with the heading: "Execution wins when visibility is real"
- Include subheading and 3 short bullets.
- Typography must be clean enough for print.

Pass if:
- Text is actually readable
- No broken letters or spacing artifacts
- Layout looks intentional

---

## Test 11 - Ad variation generation
Goal: Test scalable creative generation.

Prompt shape:
- Create 4 premium ad variations for an AI-powered PMO advisory offer.
- Same core concept, different visual hooks.
- Executive audience, high trust, clean typography.

Pass if:
- Variations are genuinely distinct
- Messaging remains coherent
- Quality holds across all outputs

---

## Test 12 - Slide hero visual
Goal: Test whether the model can create a deck-worthy hero image.

Prompt shape:
- Create a premium presentation hero visual for a deck titled: "AI for Executive Execution"
- Sophisticated, modern, understated, boardroom-credible.
- Avoid sci-fi clichés, robots, holograms, and blue-glow nonsense.

Pass if:
- Feels board-grade
- Supports a serious executive deck
- Not generic AI stock-art sludge

---

## Decision rules

### Strong model
- Passes at least 8/12 tests
- No critical failure in Tests 1, 7, 9, or 10
- Produces at least 3 assets that are usable with minimal edits

### Limited but useful model
- Passes 5 to 7 tests
- Good for selected lanes only, such as concepts, ads, or backgrounds
- Not reliable enough for premium brand work

### Not worth operationalizing
- Fails identity consistency
- Fails controlled edits
- Fails typography
- Produces outputs that need too much cleanup to be worth the speed

---

## What matters most for Ahmed
Priority order:
1. Identity preservation
2. LinkedIn authority visuals
3. PMO / executive execution diagrams
4. Slide / deck visuals
5. Controlled edits
6. Growth / ad creative

## Notes template
Model tested:
Date:
Strengths:
Weaknesses:
Best use cases:
Do not use for:
Final verdict:
