# SkillEvaluator Remediation

Date: 2026-08-21
Model for focused forward tests: `gpt-5.6-sol`
SkillEvaluator: NVIDIA v0.2.0, commit `8850da0d524f4363b0ce93e6006dfb958a429a99`

## Outcome

All four pilot recommendations were implemented in the active skills. The two previously failed behavioral cases now pass every authored assertion, and all three skills pass the six scoped NVIDIA Tier 1 gates.

| Skill | NVIDIA Tier 1 | Quality | Focused regression |
|---|---:|---:|---:|
| `gateway-runtime-safety` | 6/6 pass | 89.8 | Metadata-only change; native validation pass |
| `content-publishing-safety` | 6/6 pass | 89.8 | 4/4 assertions pass |
| `executive-cv-builder` | 6/6 pass | 85.2 | 4/4 assertions pass |

## Changes

1. Added publication-compatible author metadata to all three skills.
2. Moved the CV skill's historical weekly tune-up log to `references/learned-improvements-history.md`, marked maintenance-only.
3. Reduced the CV top-level file from 302 lines, 3,553 words, and 25,515 bytes to 116 lines, 753 words, and 5,610 bytes.
4. Replaced the hard-coded CV contact email in `eval/post-gen-checks.md` with required `CV_CONTACT_EMAIL`, sourced from the approved master CV data at execution time.
5. Made the CV title-only block explicitly prohibit invented requirements, achievements, metrics, titles, keywords, or evidence.
6. Made publishing visual rejections explicitly restate the complete compliant replacement direction.
7. Changed publishing reference loading to a task-conditional map so unrelated references are not loaded.

## Behavioral evidence

### CV title-only block

Passes all assertions: blocks scoring, requires the complete JD, does not generate a CV, and refuses fabrication.

Evidence: `update-validation/runs/executive-cv-builder/cv-title-only-block/response.json`

### Publishing visual rejection

Passes all assertions: fails closed, flags the dark card/16:9/tiny labels, requires reference comparison and the QA marker, and states the full 4:5 warm-paper, black-ink, restrained-orange handmade direction.

Evidence: `update-validation/runs/content-publishing-safety/publishing-visual-rejection/response.json`

## Validation

- Codex `quick_validate.py`: pass for all three skill folders.
- OpenClaw catalog: all three skills eligible and visible; zero missing requirements.
- NVIDIA scoped checks: schema, PII, license, Unicode, quality, and lint all pass for all three skills.
- The temporary 58 MB evaluator cache and stray first-run reports were removed after validation.

NVIDIA reports are retained under `update-validation/static/<skill>/`.

## Residual advisories

The NVIDIA reports retain non-blocking style advisories such as optional version/tags, conventional section names, and existing non-standard support-folder names. None weaken the evaluated safety boundaries or block Tier 1 validation.
