# SUBMIT Queue Review — instructions/submit-review.md

## Purpose

**HR Agent is the quality gate between cron scoring and Ahmed.**

`jobs-review.py` scores 300 jobs automatically → marks SUBMIT/REVIEW/SKIP.
Before Ahmed sees ANY job, HR Agent reviews the SUBMIT queue and curates a shortlist.

Ahmed should never see raw SUBMIT dumps. He sees HR's curated recommendation.

---

## Trigger

This workflow runs when:
1. HEARTBEAT detects new SUBMIT jobs (checked every heartbeat cycle)
2. CEO Morning Briefing reports SUBMIT queue > 0
3. Ahmed asks "what's new" or "show me jobs" in topic 9

---

## Review Workflow

### Step 1 — Pull SUBMIT Queue

```sql
SELECT * FROM jobs WHERE verdict = 'SUBMIT' AND status = 'discovered'
ORDER BY fit_score DESC, ats_score DESC
```

### Step 2 — HR Quality Checks (per job)

For each SUBMIT job, validate:

| Check | Action if Failed |
|-------|------------------|
| **Duplicate?** | Run `application-lock.py check`. If already in pipeline → SKIP, don't show Ahmed |
| **Company reputation?** | `web_search` (Exa): "{company} layoffs OR fraud OR reviews {year}". Glassdoor <3.0 → SKIP with note |
| **Role still open?** | `web_fetch` the posting URL. If 404/expired → SKIP |
| **Tier match?** | Cross-reference against `memory/career-strategy.md` Tier 1-3 criteria. Off-target → SKIP |
| **Role-family match?** | Must be real transformation / PMO / portfolio / delivery / business excellence / IT-technology leadership. Senior-but-wrong roles (sales, risk, demand planning, chief of staff, product, staffing, beauty/cosmetics, cyber) → SKIP |
| **Salary floor?** | `web_search`: "{title} salary {country} {year}". If below market → FLAG. If no data → note "salary unverified" |
| **Geographic fit?** | Must be GCC (UAE, KSA, Qatar, Bahrain, Kuwait, Oman) or remote-eligible → SKIP if not |

### Step 3 — Rank and Present ALL Validated Jobs

Show Ahmed ALL jobs that pass quality checks. Don't cap or filter out valid opportunities — that's Ahmed's decision, not HR's.

Rank by:
1. ATS score (highest first)
2. Fit score (highest first)
3. Tier 1 > Tier 2 > Tier 3
4. Company brand strength (known brand > unknown)
5. Role freshness (posted <7 days > older)

### Step 4 — Present to Ahmed (Topic 9)

Format:
```
💼 New Opportunities — HR Reviewed ([N] validated, [M] filtered out)

🏆 Tier 1
1. [Title] — [Company] ([City, Country])
   ATS: [score]/100 | Posted [date]
   Why: [1-line fit reason]
   ⚠️ [any flags — salary concern, short posting, etc.]

📌 Tier 2
2. ...

Filtered out: [M] jobs (duplicates: X, expired: Y, geo mismatch: Z)

Say "build CV for #N" or "details #N" for full JD.
```

**Rule: HR filters noise. Ahmed filters opportunity. Show everything that's real.**

### Step 5 — Loop in CEO

```
[HR Agent] Curated shortlist posted to HR Desk.
[N] SUBMIT → [M] recommended to Ahmed (filtered: duplicates, expired, off-target).
Top match: [Title] @ [Company] (ATS [score]).
```

---

## REVIEW Verdict Jobs (Score 5-6)

These are borderline. HR Agent:
1. Does NOT show these to Ahmed automatically
2. Holds them in a "REVIEW" backlog
3. Once per week (Sunday), scans REVIEW backlog for any that improved (reposted, company news, etc.)
4. Promotes to SUBMIT if warranted, otherwise archives after 30 days

---

## What NOT to Do

- Never show Ahmed raw SUBMIT dumps without quality checks
- Never show expired job postings
- Never show duplicates of jobs already in pipeline
- Never recommend a job HR hasn't validated
- Never skip the duplicate check — application-lock exists for a reason
