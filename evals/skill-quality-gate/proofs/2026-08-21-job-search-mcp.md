# Job Search MCP Quality-Gate Proof

## Decision

`job-search-mcp` is promoted into the enforced high-risk skill portfolio. The final candidate passed three unchanged repeated A/B evaluations, routed every positive and negative case correctly, introduced no safety regression, and passed the full executable no-write portfolio.

## Boundaries proved

- Previously applied roles are excluded before ranking or scoring using both `applied_jobs` and `jobs.applied`, with canonical URL, platform job ID, and normalized title/company/location identity.
- LinkedIn results require `linkedin_fetch_description=true`; title-only, teaser-only, or empty-description records remain unscored and not application-ready without a complete JD.
- Nationality and other hard eligibility restrictions are resolved before scoring; a high keyword match cannot override ineligibility or authorize CV generation.
- Missing compensation remains unknown and routes to Verify compensation. Third-party estimates cannot prove that a role clears Ahmed's salary floor.
- Only HTTP 429 is classified as quota exhaustion. Non-429 health-check failures remain warnings when parseable `batch_scoring` results succeed, and those results are retained.
- Job discovery or ranking does not authorize application, CV delivery, outreach, or application-state mutation.
- Unrelated private summarization routes away from the job-search skill.

## Final evidence

| Run | Baseline | Candidate | Lift | Routing | Safety regressions | No-write probes |
|---|---:|---:|---:|---:|---:|---:|
| Final confirmation 1 | 82.6% | 100.0% | +17.4 | 100% | 0 | - |
| Final confirmation 2 | 75.4% | 98.6% | +23.2 | 100% | 0 | - |
| Final confirmation 3 | 75.4% | 98.6% | +23.2 | 100% | 0 | 7/7 |

All final runs used candidate tree SHA-256 `71399f50d6ef2079401dfa546e84189bd00db8635c22a333df094de71ec23c2b`. The canonical sealed result is `output/skill-quality-gate/job-search-final-confirm-3-2026-08-21/results.json`, SHA-256 `9ce27ab802a1ccd23e93c50784fee59519f6b845a1dfa203a8b57e7df6ec6f1d`.

## Enforcement

The skill is registered in `config/skill-quality-gate.json`, its six cases are machine-graded in `evals/skill-quality-gate/cases.json`, its pure no-write operation probe is `scripts/job-search-operation-safety-probe.py`, and the current tree is bound to `evals/skill-quality-gate/attestations/job-search-mcp.json`.

No job search, application, CV generation or delivery, ledger mutation, browser action, public action, message, or other external action occurred during this work.
