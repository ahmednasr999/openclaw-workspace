# Job Search Policy — Effective 2026-03-07

*Approved by Ahmed Nasr on Mar 7, 2026*

---

## Target Titles

### Priority 1 (always process)
- VP Digital Transformation
- VP Technology Strategy
- VP Enterprise Transformation
- Director Transformation Office
- Head of Enterprise PMO
- Chief Transformation Officer
- Chief Digital Officer
- Group PMO Director

### Priority 2 (process if strong match)
- Programme Director
- Head of Strategy and Transformation
- Head of PMO
- Director Strategic Initiatives

### Exclude / Deprioritize
- Project Manager (unless clearly senior enterprise scope)
- IT Manager
- Analyst, Coordinator, Specialist, Associate
- Mid-level roles without Head/Director/VP/C-level seniority
- Intern, Graduate, Trainee, Cadet

---

## Country Weighting

| Priority | Countries |
|----------|-----------|
| High | UAE, Saudi Arabia, Qatar |
| Medium | Bahrain, Kuwait, Oman |
| Low | UK/Europe (only if GCC mandate or exceptional package) |

---

## Gates

- **Seniority gate:** Head, Director, VP, C-level only
- **Work mode gate:** GCC on-site/hybrid preferred
- **Compensation signal gate:** Prioritize roles at/above 50K AED equivalent when visible
- **Sector gate:** HealthTech, FinTech, Digital Transformation, AI, PMO, e-commerce preferred

---

## Processing Rules

1. JD fetch -> ATS score -> verdict (SUBMIT 82+ / REVIEW 75-81 / SKIP <75)
2. SUBMIT only enters CV queue
3. CV tailoring: Opus 4.6 only, zero exceptions
4. Duplicate skip: check pipeline before processing
5. Unique-link validation: no duplicate LinkedIn IDs in same batch

---

## Output Contract v2

### Mandatory output lines (no tables, no narrative-first)
1. `TEST_START | run_id | start_time_utc | roles_count | eta`
2. `HEARTBEAT | run_id | progress_percent | eta | blocker_or_none`
3. `TEST_RESULT | run_id | pass_count/18 | failed_rules_or_none | evidence_ref`
4. `TASK_COMPLETE | run_id | processed | submitted | reviewed | skipped`

### Pre-send validation gate (must pass before CV/job-link delivery)
- A) Required fields per role: company, role, unique job_link, jd_status, ats_score, verdict, confidence
- B) Unique job-link check across batch (no duplicate LinkedIn ID)
- C) Role-to-link consistency (company/role must match link metadata)
- D) Verdict gate: only SUBMIT roles enter CV queue
- E) CV model gate: Opus 4.6 only
- F) If validation fails: `BLOCKED | run_id | validation_failure | fix_action`

### Daily reliability scorecard
`SCORECARD | date | total_runs | success_rate | median_cycle_time | stalled_runs | missed_heartbeats | top_failure_reason`

### Policy impact reporting
`POLICY_IMPACT | run_id | total_found | executive_kept | noise_dropped | top3_quality_notes`
