# NASR SkillEvaluator Pilot

Date: 2026-08-21
Model: `gpt-5.6-sol` through existing ChatGPT OAuth
SkillEvaluator: NVIDIA v0.2.0, commit `8850da0d524f4363b0ce93e6006dfb958a429a99`

## Decision

Adopt paired skill-versus-baseline evaluation as a quality gate for high-risk NASR skills. Keep the three evaluated skills active. Do not install SkillEvaluator globally or add a paid/public evaluator credential yet.

The pilot found strong causal lift, especially where generic model judgment is unsafe:

- Overall correctness: 60.0% to 95.6%, **+35.6 points**.
- Perfect-case effectiveness: 33.3% to 83.3%, **+50.0 points**.
- Correct skill routing, including negative cases: 25.0% to 100.0%, **+75.0 points**.
- Most important observed intervention: the baseline said `Proceed` at a verified 79% ATS fit; `executive-cv-builder` enforced the mandatory 82% floor and rejected CV generation.

## Results

| Skill | Correctness, baseline → skill | Lift | Perfect cases, baseline → skill | Routing, baseline → skill |
|---|---:|---:|---:|---:|
| `gateway-runtime-safety` | 40.0% → 100.0% | +60.0 | 1/4 → 4/4 | 25% → 100% |
| `content-publishing-safety` | 66.7% → 93.3% | +26.6 | 1/4 → 3/4 | 25% → 100% |
| `executive-cv-builder` | 73.3% → 93.3% | +20.0 | 2/4 → 3/4 | 25% → 100% |
| **Overall** | **60.0% → 95.6%** | **+35.6** | **4/12 → 10/12** | **25% → 100%** |

Correctness is the percentage of 45 binary assertions passed. Effectiveness counts a case only when every assertion passed. Routing counts a positive case only when the target skill was used and a negative case only when no skill was used.

## Cost

Across all 12 cases per arm:

| Metric | Baseline | With skill | Change |
|---|---:|---:|---:|
| Mean elapsed time | 8.864 s | 15.831 s | +78.6% |
| Input tokens | 179,489 | 414,338 | +130.8% |
| Uncached input tokens | 143,393 | 204,418 | +42.6% |
| Output tokens | 2,558 | 5,742 | +124.5% |

The negative cases were effectively cost-neutral: 5.601 s baseline versus 5.574 s with the skill home, and 40,894 versus 40,454 input tokens. This confirms that irrelevant skills were not loaded. The cost increase is concentrated in relevant positive tasks where Codex reads the skill and references.

Positive-task input rose 169.8% in total and 69.7% after removing cached input; positive-task latency rose 93.4%. This is acceptable for high-risk gateway, publishing, and CV decisions, but not for indiscriminate use.

## Static SkillEvaluator findings

### `gateway-runtime-safety`

- Quality: 88.0/100, grade B.
- Passed PII, license, Unicode, quality threshold, and lint checks.
- Failed external schema governance because `metadata.author` is missing.

### `content-publishing-safety`

- Quality: 88.0/100, grade B.
- Passed PII, license, Unicode, quality threshold, and lint checks.
- Failed external schema governance because `metadata.author` is missing.

### `executive-cv-builder`

- Quality: 81.2/100, grade B.
- Passed license, Unicode, and lint checks.
- Failed external schema governance because `metadata.author` is missing.
- PII scan flagged the embedded personal email address.
- Quality check flagged the 6,367-token top-level `SKILL.md`, above the recommended 5,000-token ceiling.

These are publication/governance findings, not evidence that the internal skills are unsafe. They should be fixed before any ClawHub/public promotion.

## Observed gaps

1. `content-publishing-safety` correctly rejected the bad visual but did not restate the complete compliant replacement direction: 4:5, warm paper, black ink, restrained orange. This caused its only failed skilled assertion.
2. `executive-cv-builder` correctly blocked title-only CV work but did not explicitly state the no-fabrication rule in that answer. This caused its only failed skilled assertion.
3. `executive-cv-builder` carries a long historical tune-up log in the top-level skill. Move that history to a reference/archive so invocation context stays operational.
4. `content-publishing-safety` had the highest uncached context overhead: 30,453 to 67,064 tokens across its four cases, +120.2%. Its reference-loading path should be tightened.

## Recommended quality gate

For new or materially changed high-risk skills:

- Minimum four cases: three realistic positives plus one negative non-trigger.
- Run the same model, prompt, schema, and sandbox with and without the skill.
- Require at least 90% assertion correctness.
- Require 100% correct positive routing and 100% negative non-triggering.
- Require no safety-boundary regression.
- Record total, cached, and uncached tokens plus elapsed time.
- Block promotion when correctness improves by less than five points unless the skill adds a mandatory safety or governance boundary.
- Use at least three attempts per case before claiming statistical confidence or publishing benchmark claims.

## Method and limitations

- Four curated cases per skill, one attempt per arm: 24 live Codex runs.
- Both arms used `gpt-5.6-sol`, the same JSON response schema, read-only sandbox, and no external actions.
- NVIDIA's strict Tier 3 dataset contract passed for all three four-case datasets.
- Native Tier 3 could not run because this workspace has no separate NVIDIA/OpenAI/Anthropic evaluator API key; local mode also lacks Bubblewrap, and Docker access is unavailable to this process.
- The compatibility harness reproduced the core A/B design using Codex CLI and existing ChatGPT OAuth, but NVIDIA's five-dimension LLM judge was not used.
- Binary assertions were graded manually and non-blindly. Results are decision-grade for a pilot, not publication-grade statistics.
- This evaluates judgment and routing, not actual gateway restarts, publishing, or CV delivery execution.

## Artifacts

- `results.json`: aggregate machine-readable scores and costs.
- `manual-grades.json`: assertion-level binary grades and reasons.
- `runs/run-summary.json`: per-run model, status, time, and token usage.
- `runs/<skill>/<case>/<arm>/response.json`: final structured response for every arm.
- `reports/<skill>/`: NVIDIA Tier 1 JSON and Markdown reports.
- `skills/<skill>/evals/evals.json`: validated four-case datasets.
