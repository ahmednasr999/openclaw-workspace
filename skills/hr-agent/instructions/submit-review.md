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
ORDER BY career_fit_score DESC
```

### Step 2 — HR Quality Checks (per job)

For each SUBMIT job, validate:

| Check | Action if Failed |
|-------|------------------|
| **Duplicate?** | Run `application-lock.py check`. If already in pipeline → SKIP, don't show Ahmed |
| **Company reputation?** | `web_search` (Exa): "{company} layoffs OR fraud OR reviews {year}". Glassdoor <3.0 → SKIP with note |
| **Role still open?** | `web_fetch` the posting URL. If 404/expired → SKIP |
| **Tier match?** | Cross-reference against `memory/career-strategy.md` Tier 1-3 criteria. Off-target → SKIP |
| **Salary floor?** | `web_search`: "{title} salary {country} {year}". If below market → FLAG. If no data → note "salary unverified" |
| **Geographic fit?** | Must be GCC (UAE, KSA, Qatar, Bahrain, Kuwait, Oman) or remote-eligible → SKIP if not |

### Step 3 — Curate Shortlist

From validated SUBMIT jobs, select the top 3-5 (maximum 7) based on:
1. ATS score (highest first)
2. Tier 1 > Tier 2 > Tier 3
3. Company brand strength (known brand > unknown)
4. Role freshness (posted <7 days > older)

### Step 4 — Present to Ahmed (Topic 9)

Format:
```
💼 New Opportunities — HR Reviewed

1. [Title] — [Company] ([City, Country])
   ATS: [score]/100 | Tier [1/2/3] | Posted [date]
   Why: [1-line reason this is worth Ahmed's time]
   ⚠️ [any flags — salary concern, short posting, etc.]

2. ...

Filtered out: [N] jobs (duplicates: X, off-target: Y, expired: Z)

Say "build CV for #N" to start, or "details #N" for full JD.
```

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
