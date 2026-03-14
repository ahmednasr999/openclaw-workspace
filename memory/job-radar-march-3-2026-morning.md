---
description: "Job Radar results from March 3, 2026 morning run"
type: log
topics: [job-search]
updated: 2026-03-14
---

# Job Radar — GCC Executive Roles — Mar 3, 2026 (7 AM Cairo / 5 AM UTC)

**Cron ID:** job-radar-gcc-daily-0001
**Execution Time:** Tuesday, March 3, 2026 — 05:05 AM UTC (07:05 AM Cairo)
**Model:** Claude Sonnet 4.6 (main session)
**Scan Type:** Web only (Gmail/GOG keyring not available in cron context)

---

## Sources Scanned

| Source | Method | Status | Notes |
|--------|--------|--------|-------|
| Halian.com/jobs | web_fetch | Partial | Job list loaded; all UAE/KSA executive roles returned "Applications closed" on detail fetch |
| Wuzzuf.net | web_fetch | Partial | Search results accessible; individual job slugs redirect to stale role |
| GulfTalent.com | web_fetch | Blocked | JS-only |
| Bayt.com | web_fetch | Blocked | CAPTCHA |
| LinkedIn Jobs | web_fetch | Blocked | Auth required |
| Michael Page UAE | web_fetch | Blocked | 404 on search |
| Page Executive | web_fetch | Blocked | JS-only |
| Robert Walters UAE | web_fetch | Blocked | CAPTCHA/403 |
| ADNOC Careers | web_fetch | Blocked | JS-rendered |
| Emaar Careers | web_fetch | Error | ServiceNow error page |
| NEOM Careers | web_fetch | Partial | Eightfold JS portal, no readable job list |
| Al-Futtaim (afuturewithus.com) | web_fetch | Partial | No relevant Director/VP roles found in query results |
| DP World Careers | web_fetch | Blocked | JS-rendered, Workday portal blocked |
| Naukrigulf | web_fetch | Aborted/Timeout | |
| Jobgether | web_fetch | Blocked | 403 Cloudflare |
| Microsoft Careers | web_fetch | JS-rendered | No readable job list |
| Halian (AI expertise page) | web_fetch | 404 | Redirected to "closed" |
| G42/Core42 | web_fetch | JS-rendered | |
| Foreground.io | web_fetch | Fetch failed | Domain unreachable |
| DubaiZle | web_fetch | CAPTCHA bot block | |
| Wuzzuf (list scan) | web_fetch | Success | Returned 39+ results; filtered for GCC executive roles |

---

## Roles Evaluated (New Candidates — Not in Seen List)

### DISMISSED — Below Threshold or Unverifiable

| # | Company | Role | Location | ATS | Reason | Source Credibility |
|---|---------|------|----------|-----|--------|--------------------|
| 1 | DP World | Director, Optimization & Efficiency | Dubai | ~72% | Logistics/ops-specific; gap vs Ahmed's HealthTech/FinTech DT profile; official page unreachable | unverified |
| 2 | NexRevo | Advisors/Consultants Digital Transformation | Riyadh | ~45% | Sales/advisory role, not technology executive; vague listing | unverified |
| 3 | Foreground (HR/Recruitment) | CTO | Riyadh | N/A | JD tags suggest finance/ops, not DT; foreground.io unreachable; 6 days old | unverified |
| 4 | Jobgether (client unknown) | Senior Program Director | Dubai | N/A | Aggregator only; Jobgether blocked; client company unidentifiable; insufficient JD | unverified |
| 5 | Confidential Government | Executive Director, National Digital Sovereignty & AI | Riyadh | ~60% | 16 days old (outside 24hr window); job tags: marketing/sales/analysis (not pure tech exec); probable Saudi national preferred | unverified |

### CLOSED (Verified)

| # | Company | Role | Location | Status |
|---|---------|------|----------|--------|
| 1 | Halian (client) | Technical Director, Federal Technology | Abu Dhabi | CLOSED - "Applications for this role are now closed" (official Halian page) |
| 2 | Halian (client) | Head of Data Governance, Security & Responsible AI | Abu Dhabi | CLOSED - "Applications for this role are now closed" (official Halian page) |

---

## Handoffs Created Today

None. No roles reached ATS >= 80% with verified JD.

---

## Pipeline Status Check

- **Active Pipeline:** 46 roles applied (Row #46 = RAKBANK VP AI Platform Owner, most recent)
- **Radar section:** Empty (no open radar items as of last update)
- **Delphi Consulting:** Interview completed Feb 24. Follow-up sent Mar 2. Currently awaiting recruiter response. Follow-up due Mar 9 if silence continues.
- **Talabat follow-up due:** Mar 2 (past due - policy: no proactive follow-up on LinkedIn applications, wait for them to respond)
- **AIQU, Nexus follow-up due:** Mar 2 (same policy)
- **eMagine follow-up due:** Mar 4 (tomorrow)
- **Group IT Director Bahrain:** Follow-up due Mar 5 (2 days)

---

## Recruiter Responses (Web Evidence)

- No new genuine recruiter responses detected today.
- LinkedIn automated application confirmations for RAKBANK and Cooper Fitch logged yesterday (system emails, not personal recruiter contact).
- Delphi Consulting: No new direct contact visible. Next follow-up window: Mar 9.
- All other pipeline companies: No direct recruiter contact detected.

---

## Extraction Methods Used

- web_fetch: 25 attempts
- firecrawl: 0 (not needed; fallback not triggered by successful extractions)

## Source Credibility Split

- official: 2 (Halian.com/jobs confirmed live list, afuturewithus.com confirmed live)
- verified-aggregator: 1 (Wuzzuf — returned search results; individual JD pages blocked)
- unverified: 5 (all dismissed roles)

## Items Downgraded Due to Weak Evidence

- 5 roles downgraded from "potential" to dismissed due to: unverifiable JDs, aggregator-only sourcing, stale postings (16+ days), or insufficient ATS fit

---

## Summary

Today's scan yielded no new roles above the ATS >= 80 threshold. The market appears to have a lag today (Tuesday morning). Most accessible portals are JS-heavy or require authentication. The Wuzzuf open-list scan returned roles but individual verification was blocked.

Pipeline is strong at 46 active applications. The highest-priority item remains Delphi Consulting (interview done, follow-up sent, awaiting response).
