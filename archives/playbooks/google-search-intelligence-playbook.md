# Google Search Intelligence Playbook

Purpose: improve search quality and speed for Job Hunter and Researcher with a repeatable method.

## 1) Source reliability ladder
- Tier 1: Official sources (company career pages, official docs, regulator sites)
- Tier 2: Reputable secondary sources (major media, strong domain niche sources)
- Tier 3: Aggregators/community lists (discovery only, never final evidence)

Rule: no recommendation is final without Tier 1 verification.

## 2) Four-pass workflow

### Pass A: Discovery
Goal: find candidate URLs fast.

Use broad queries:
- `site:linkedin.com/jobs ("VP" OR "Head") "Digital Transformation"`
- `("company" OR "hiring") "AI" "Dubai"`
- `site:company.com ("careers" OR "jobs")`

### Pass B: Precision
Goal: reduce noise.

Tactics:
- Add intent filters: `intitle:`, `inurl:`, exact quotes
- Exclude noise with minus operator: `-intern -junior -blog`
- Tune language/region when needed via URL params and settings

### Pass C: Verification
Goal: validate freshness and legitimacy.

Checklist:
1. Is source Tier 1 or confirmed against Tier 1?
2. Is posting still open/active now?
3. Is role seniority and scope aligned (VP/Head/Director-level as requested)?
4. Is location and compensation band compatible with Ahmed targets?

### Pass D: Decision packaging
Goal: deliver decision-ready output.

Output format:
- Opportunity: [company | role | location]
- Why it matters: [1-2 lines]
- Evidence: [links]
- Confidence: High / Medium / Low
- Recommended action: Apply / Monitor / Reject

## 3) Operator library (core)
- `site:` domain restriction
- `intitle:` title-only match
- `inurl:` url pattern match
- `"..."` exact phrase
- `-keyword` exclusion
- `OR` alternatives
- `before:` / `after:` date constraints where supported

## 4) Guardrails
- Do not depend on undocumented query params as hard requirements.
- Treat large parameter catalogs as exploratory only.
- If data conflicts, official source wins.
- Prefer fewer high-quality links over many unverified links.

## 5) Agent-specific usage

### Job Hunter
- Optimize for opportunity detection and action speed.
- Deliver shortlists with clear apply/monitor/reject recommendation.

### Researcher
- Optimize for depth and context quality.
- Add company, market, and role intelligence around each validated opening.

## 6) Definition of done
A search task is done only when:
- At least one Tier 1 validated finding is delivered, or
- A clear “no valid opportunities found” result is returned with evidence and next search pivot.

## 7) Quick execution template

Use this template per run:

1. Objective: [what we are trying to find]
2. Discovery queries used: [list]
3. Precision filters used: [list]
4. Verified opportunities: [table]
5. Rejected opportunities and why: [table]
6. Recommendation: [what to do next and why]

No em dashes anywhere in output. Use commas, periods, or colons.
