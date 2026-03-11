# LinkedIn Gulf Jobs Scanner - Version 2.0 (Enhanced)
# Runs daily at 6 AM Cairo

## Objective
Automate a comprehensive search for high-level executive and digital transformation roles in the GCC region, filtering for new postings in the last 24 hours. Evaluate each job against Ahmed's CV using ATS scoring. Only notify if qualified (82%+).

## Search Parameters

### Countries (6)
- Saudi Arabia
- United Arab Emirates
- Qatar
- Bahrain
- Kuwait
- Oman

Preferred: Saudi Arabia and UAE (flag for priority)

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

## Search URL Format
https://www.linkedin.com/jobs/search/?keywords={title} {keywords}&location={country}&f_TPR=r86400&f_E=6&f_PP=remote=false

- f_TPR=r86400: Past 24 hours
- f_E=6: Executive level (Director+)
- f_PP=remote=false: Exclude remote-only

## ATS Scoring (100 points)

### Keyword Match (40%)
- Match: digital transformation, PMO, AI, fintech, healthtech, e-commerce
- 20+ years experience
- Growth metrics (233x, 300+ projects)

### Experience Alignment (30%)
- VP/Director level, 15+ years
- Key achievements: $50M transformation (TopMed), 233x growth (Talabat), 300+ projects (Network International)

### Location/Salary Fit (20%)
- +10 Saudi Arabia or UAE
- +10 salary 50K+ AED

### Skills/Other (10%)
- Bonus: AI, HealthTech
- Penalty: Non-GCC, unrelated industries

**Threshold: 82% = QUALIFIED**

## Process

1. Generate 120 combinations (20 titles × 6 countries)
2. For each: Search with 24h filter + executive level
3. If jobs found: Get full details
4. ATS score each job
5. Check duplicates (vs notified-jobs.md)
6. If qualified (82+): Send to Ahmed
7. If 0 qualified: Skip notification

## Output Format

| Job Title | Company | Location | Score | URL | Notes |
|-----------|---------|----------|-------|-----|-------|

Notes:
- Hot: Posted <6 hours ago
- Easy Apply
- Saudi Vision 2030 aligned
- Salary if available
- Priority: Saudi/UAE first

## CV Source
/root/.openclaw/workspace/memory/master-cv-data.md

## Logging
- Log to: /root/.openclaw/workspace/jobs-bank/scraped/cron-logs.md
- Track: Date, scanned, found, qualified, errors
- Dedupe: /root/.openclaw/workspace/jobs-bank/scraped/notified-jobs.md
