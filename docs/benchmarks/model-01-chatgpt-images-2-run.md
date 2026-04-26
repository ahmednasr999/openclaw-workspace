# Model 01 Benchmark Run - ChatGPT Images 2.0

Date: 2026-04-23
Model label: ChatGPT Images 2.0
Runtime model id: openai/gpt-image-2
Benchmark source: `docs/benchmarks/ai-image-model-benchmark-sheet.md`

## Current availability in this environment
- `openai/gpt-image-2` is discoverable by the image tool
- Current status: NOT configured in this environment
- Execution blocker: OpenAI image auth is not currently configured here

## Decision
Model 01 is defined as ChatGPT Images 2.0 (`openai/gpt-image-2`).
This is the correct first benchmark target based on the X post that triggered the evaluation.

## Execution status
- Benchmark design: READY
- Benchmark execution in this environment: BLOCKED until OpenAI image auth is configured

## Required reference assets
1. Ahmed portrait source photo
2. Optional second Ahmed portrait for identity consistency checks
3. One baseline low-light photo for lighting-fix test
4. One baseline office/background photo for controlled-edit comparison

## Evidence to save for each test
- Prompt used
- Output image path(s)
- Short assessment notes
- Score out of 30
- Pass / fail

## Test order
Run in this order so identity/control risks surface early:
1. Executive headshot upgrade
2. Controlled background swap
3. Controlled lighting fix
4. Identity consistency across 3 variations
5. Cinematic LinkedIn statement card
6. Carousel cover slide
7. PMO framework diagram
8. Transformation roadmap visual
9. Dashboard mockup
10. Typography and print cleanliness
11. Ad variation generation
12. Slide hero visual

## Model 01 prompt pack

### Test 1 - Executive headshot upgrade
Transform this portrait into a premium executive studio headshot. Keep facial identity accurate. Clean lighting, luxury corporate tone, realistic skin, tailored suit, neutral elegant background. No beauty-filter look, no exaggerated jawline, no fake teeth, no AI glow.

### Test 2 - Controlled background swap
Keep the person exactly the same. Only change the background to a refined executive office setting. Do not alter clothing, pose, face, or framing.

### Test 3 - Controlled lighting fix
Improve lighting only. Preserve face, background, outfit, camera angle, and crop exactly. Make the image cleaner and more professional without changing identity.

### Test 4 - Identity consistency across 3 variations
Generate 3 variations of the same executive portrait concept. Keep the same facial identity, age, expression family, build, and overall look. Vary only pose and framing slightly.

### Test 5 - Cinematic LinkedIn statement card
Create a cinematic editorial LinkedIn visual for the statement: "AI should remove reporting drag, not create more process." Premium typography, strong hierarchy, dark elegant palette, operator-grade tone. Designed for mobile readability.

### Test 6 - Carousel cover slide
Design a LinkedIn carousel cover slide titled: "5 PMO workflows AI can accelerate this quarter". Clean editorial layout, bold cover hierarchy, premium business design. Keep it minimal and high-trust.

### Test 7 - PMO framework diagram
Create a clean executive framework diagram showing: Inputs -> Decision Engine -> Prioritization -> Execution Tracking -> Executive Review. Board-safe style, simple labels, readable layout, no clutter.

### Test 8 - Transformation roadmap visual
Create a 3-phase transformation roadmap visual: Stabilize, Scale, Optimize. Executive presentation style, minimal color palette, clean milestone structure.

### Test 9 - Dashboard mockup
Design an executive dashboard for a transformation office. Show delivery health, risks, milestone status, financial variance, and top decisions needed. Make it realistic, modern, and presentation-ready.

### Test 10 - Typography and print cleanliness
Design a premium poster with the heading: "Execution wins when visibility is real". Include a subheading and 3 short bullets. Typography must be clean enough for print.

### Test 11 - Ad variation generation
Create 4 premium ad variations for an AI-powered PMO advisory offer. Same core concept, different visual hooks. Executive audience, high trust, clean typography.

### Test 12 - Slide hero visual
Create a premium presentation hero visual for a deck titled: "AI for Executive Execution". Sophisticated, modern, understated, boardroom-credible. Avoid sci-fi clichés, robots, holograms, and blue-glow nonsense.

## Fillable scorecard
| Test | Score /30 | Pass? | Notes |
|---|---:|---|---|
| 1. Executive headshot upgrade |  |  |  |
| 2. Controlled background swap |  |  |  |
| 3. Controlled lighting fix |  |  |  |
| 4. Identity consistency across 3 variations |  |  |  |
| 5. Cinematic LinkedIn statement card |  |  |  |
| 6. Carousel cover slide |  |  |  |
| 7. PMO framework diagram |  |  |  |
| 8. Transformation roadmap visual |  |  |  |
| 9. Dashboard mockup |  |  |  |
| 10. Typography and print cleanliness |  |  |  |
| 11. Ad variation generation |  |  |  |
| 12. Slide hero visual |  |  |  |

## Final verdict template
- Strengths:
- Weaknesses:
- Best use cases:
- Not safe for:
- Passed tests count:
- Final verdict:
