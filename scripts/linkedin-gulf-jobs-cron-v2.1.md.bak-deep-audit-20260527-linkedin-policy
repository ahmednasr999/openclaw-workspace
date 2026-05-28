# LinkedIn Gulf Jobs Scanner - Version 2.1 (Production-Ready)
# Runs daily at 6 AM Cairo + manual trigger via Slack/Telegram

## Objective
Automate a comprehensive search for high-level executive and digital transformation roles in the GCC region. Fetch full job descriptions, evaluate each against Ahmed's CV using ATS scoring. Only notify if qualified (82%+). Route notifications to Slack #ai-jobs.

---

## Search Parameters

### Countries (6)
- Saudi Arabia (PRIORITY)
- United Arab Emirates (PRIORITY)
- Qatar
- Bahrain
- Kuwait
- Oman

### Titles (20)
1. Chief Digital Officer
2. Chief Technology Officer
3. Chief Information Officer
4. VP Digital Transformation
5. Director Digital Transformation
6. Head of Digital Transformation
7. Head of IT
8. Head of Technology
9. Director of Technology
10. VP Technology
11. VP IT
12. Director of IT
13. Senior Director Digital Transformation
14. Head of Digital
15. Director of Digital Innovation
16. Head of Digital Innovation
17. Program Director
18. PMO Director
19. Chief Strategy Officer
20. Chief Operating Officer

### Additional Keywords
Include in search: "digital transformation" OR "AI" OR "PMO" OR "fintech" OR "healthtech" OR "e-commerce"

---

## Search Method

### Primary: LinkedIn Public Search
URL format:
```
https://www.linkedin.com/jobs/search/?keywords={title}+OR+{keywords}&location={country}&f_TPR=r172800&f_E=6&f_WT=1
```

Filters:
- f_TPR=r172800: Past 48 hours (overlap window for dedup safety)
- f_E=6: Executive level (Director+)
- f_WT=1: On-site only (excludes remote-only)

### Fallback: JobSpy Library
If LinkedIn blocks (429, login wall, or 0 results across ALL 120 searches):
```python
from jobspy import scrape_jobs
jobs = scrape_jobs(site_name="linkedin", search_term=title, location=country, hours_old=48)
```

### Job Detail Fetching (CRITICAL)
Use the existing JD fetcher engine: `scripts/linkedin-jd-fetcher.py`

For each job found in search results:
1. Extract job ID from search page
2. Call linkedin-jd-fetcher.py with job URL to get full details via Camofox + cookies
3. Extracts: title, company, location, full description, requirements, salary (if shown), easy apply flag, posting age
4. Authenticated via li_at cookie at `config/linkedin-cookies.json`
5. If Camofox unavailable: fallback to raw Playwright
6. If cookies expired: use public page (limited details), log warning

**The ATS scorer MUST score against the actual job description text, NOT the search title.**

### Limits
- Max 5 jobs per search combination (prevents runaway on broad searches)
- Max 600 total JD fetches per run (120 searches x 5 max)
- Maximum runtime: 20 minutes. If exceeded, stop and report partial results.

---

## ATS Scoring (100 points)

Score against the FULL JOB DESCRIPTION text.

### Keyword Match (40 points)

| Keyword | Points |
|---------|--------|
| digital transformation | 5 |
| PMO | 5 |
| project management | 4 |
| program management | 4 |
| portfolio management | 3 |
| AI / artificial intelligence | 3 |
| fintech | 3 |
| healthtech | 3 |
| e-commerce | 3 |
| PMP | 2 |
| CSM | 2 |
| CSPO | 2 |
| Lean Six Sigma | 2 |
| CBAP | 2 |
| 20+ years experience | 3 |
| growth / scale / transformation (metrics) | 3 |

Each keyword found adds its points. **Capped at 40.**

### Experience Alignment (30 points)
- VP/Director/C-level title in JD: +15
- 15+ years experience mentioned: +10
- Key achievement alignment ($50M+, large-scale transformation, multi-country): +5

### Location/Salary Fit (20 points)
- Saudi Arabia or UAE: +10
- Other GCC (Qatar, Bahrain, Kuwait, Oman): +5
- Salary 50,000+ AED/month (or equivalent): +10

### Skills/Other (10 points)
- AI/ML mentioned: +5
- HealthTech/Healthcare/Hospital: +5
- FinTech/Payments: +3
- e-commerce: +3

**Capped at 10.**

### Penalties (subtract from total)
- Non-GCC location detected: -20
- Unrelated industry (beauty, retail, fashion, restaurant, hospitality, real estate agent, construction, facilities): -10
- Sales/HR/Supply Chain role disguised as executive title: -15
- Requires security clearance: -30

**Threshold: 82+ = QUALIFIED**

### Borderline Zone (75-81)
Jobs scoring 75-81 are logged to `qualified-jobs-YYYY-MM-DD.md` under a "Borderline" section for manual review, but NOT sent to Slack.

---

## Process

1. Load CV keywords from `memory/master-cv-data.md`
2. Check cookie age: if li_at cookie >30 days old, log warning
3. Generate 120 combinations (20 titles x 6 countries)
4. For each: Search LinkedIn with 48h filter + executive level + on-site
5. If jobs found: **Fetch full JD via linkedin-jd-fetcher.py** (max 5 per search)
6. ATS score each job **against the full JD text**
7. Check duplicates:
   a. vs `notified-jobs.md` (previously notified)
   b. vs `jobs-bank/applications/` (previously applied)
8. If qualified (82+): Send to Slack #ai-jobs (C0AJX895U3E)
9. If 0 qualified: Send summary to Slack (searches count, jobs found, borderline count)
10. If runtime exceeds 20 minutes: stop, report partial results

---

## Error Handling

### Rate Limiting
- 1 second delay between searches
- 2 second delay between JD fetches
- If HTTP 429: wait 30 seconds, retry once
- If persistent 429: stop, alert Ahmed via Slack, log error

### LinkedIn Blocking
- If login wall detected: try public endpoint first
- If still blocked: fallback to JobSpy
- If all methods fail: alert Ahmed via Slack with error count

### Cookie Expiry
- At startup: check if li_at cookie file was modified >30 days ago
- If >30 days: log warning "Cookie may be stale"
- If authenticated fetch fails: fall back to public page
- After 3 consecutive cookie failures: alert Ahmed "Refresh cookies needed"

### Runtime Guard
- Track elapsed time from start
- If 20 minutes exceeded: stop processing, save partial results, send Slack alert:
  "⚠️ Scanner hit 20-min limit. Partial results: X/120 searches completed."

---

## Notification

### Channel: Slack #ai-jobs (C0AJX895U3E)

### Format (when qualified jobs found):
```
🎯 LinkedIn Gulf Jobs Scanner v2.1 - {count} Qualified Job(s)

🔥 {Job Title}
   Company: {company}
   Location: {location} | Score: {score}/100
   Notes: {Hot | Easy Apply | Vision 2030 | Salary}
   Link: {url}

📊 Summary: {total_searched} searches | {total_found} jobs | {qualified} qualified
```

### Notes enrichment:
- 🔥 Hot: Posted <6 hours ago
- ⚡ Easy Apply: LinkedIn Easy Apply available
- 🇸🇦 Vision 2030: Saudi Vision 2030 aligned keywords found
- 💰 Salary: If salary is visible
- ⭐ Priority: Saudi Arabia or UAE

### Sort order: Saudi/UAE first, then by score descending

---

## Deduplication

Check BOTH before notifying:
1. `jobs-bank/scraped/notified-jobs.md` - previously notified job IDs
2. `jobs-bank/applications/` - previously applied (match by company slug or job ID)

After notification: add job to notified-jobs.md

---

## Output Files

| File | Purpose |
|------|---------|
| `jobs-bank/scraped/cron-logs.md` | Execution summary (date, searched, found, scored, qualified, errors) |
| `jobs-bank/scraped/detailed-search-log.md` | Every search: title + country + job count |
| `jobs-bank/scraped/qualified-jobs-YYYY-MM-DD.md` | Qualified jobs (82+) with full details + Borderline (75-81) section |
| `jobs-bank/scraped/notified-jobs.md` | Dedup: all previously notified job IDs |

---

## Triggers

### Automatic: Cron
```
0 6 * * * cd /root/.openclaw/workspace && python3 scripts/linkedin-gulf-jobs.py >> /tmp/linkedin-gulf-jobs.log 2>&1
```

### Manual: Slack or Telegram
When Ahmed sends "run linkedin-gulf-jobs" or "scan jobs" in any channel, execute the scanner immediately.

---

## CV Source
`/root/.openclaw/workspace/memory/master-cv-data.md`

Load CV keywords at startup for ATS scoring reference.

---

## Weekly Summary
Every Sunday at 8 AM Cairo, send to Slack #ai-jobs:
```
📊 Weekly Scanner Summary
- Total searches: {sum}
- Total jobs found: {sum}
- Qualified (82+): {sum}
- Borderline (75-81): {sum}
- Top scoring job this week: {title} at {company} ({score}/100)
```

---

## Changelog from v2.0
- Changed: 24h filter to 48h (r172800) with dedup overlap
- Fixed: f_PP=remote=false to f_WT=1 (correct LinkedIn parameter for on-site)
- Added: Full JD fetching via existing linkedin-jd-fetcher.py + Camofox
- Added: Score against actual JD text, not search title
- Added: Exact point values per keyword in ATS scoring table
- Added: Previously applied jobs filter (jobs-bank/applications/)
- Added: Error handling (rate limits, blocking, cookie expiry, runtime guard)
- Added: Fallback to JobSpy when LinkedIn blocks
- Added: Penalty scoring (non-GCC, unrelated industry, security clearance, disguised roles)
- Added: Manual trigger option (Slack or Telegram)
- Added: Explicit notification channel (Slack #ai-jobs C0AJX895U3E)
- Added: Sort order (Saudi/UAE first, score descending)
- Added: Max 5 jobs per search, 600 total JD fetches, 20-min runtime limit
- Added: Borderline zone (75-81) logged but not notified
- Added: Cookie age check at startup (warn if >30 days)
- Added: Weekly summary every Sunday
- Added: CV keywords loaded at startup from master-cv-data.md
