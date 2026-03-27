# Job Pipeline — instructions/pipeline.md

## Data Sources

| Source | Location |
|---|---|
| Notion DB | `3268d599-a162-814b-8854-c9b8bde62468` |
| SQLite | `/root/.openclaw/workspace/data/nasr-pipeline.db` |
| Lock service | `scripts/application-lock.py` (integrated in `notion-pipeline-sync.py`) |

---

## Status Flow

```
Discovered → Scored → Applied → CV Built → Interview → Offer / Rejected
```

### Status Definitions

| Status | Meaning | Action Required |
|---|---|---|
| **Discovered** | Job found, not yet evaluated | Score it within 24h |
| **Scored** | ATS/tier fit assessed | Ahmed decides to apply |
| **Applied** | Submitted | Follow up if >14 days silence |
| **CV Built** | Tailored CV generated and sent | Track acknowledgment |
| **Interview** | Interview scheduled | Trigger `instructions/interviews.md` immediately |
| **Offer** | Offer received | Alert CEO, prepare negotiation brief |
| **Rejected** | Declined or no response | Log reason, keep for pattern analysis |

---

## Tier Classification

### Tier 1 — Priority (pursue aggressively)
- Executive roles: C-suite, VP, GM, Country Manager
- Sectors: Healthcare, Digital Transformation, AI
- Geography: GCC (UAE, KSA, Qatar, Bahrain, Kuwait, Oman)

### Tier 2 — Strong fit
- Senior Director / VP level
- Functions: PMO, Operations, Strategy
- Any geography acceptable

### Tier 3 — Opportunistic
- Consulting engagements
- Board advisory positions
- Fractional / interim roles

---

## Duplicate Guard

Before adding any new job:
1. Query SQLite: `SELECT * FROM applications WHERE company = ? AND title LIKE ?`
2. Query Notion DB with matching company + title filter
3. If duplicate found → skip, notify Ahmed with existing entry link
4. ApplicationLockService acquires row lock before any write to prevent race conditions

---

## Job Search Tooling

**Use the Job Search MCP skill** for multi-platform discovery:
```
Read skills/job-search-mcp/SKILL.md
```
JobSpy MCP server searches LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, Naukri, and BDJobs simultaneously. Use this instead of manually searching each platform.

---

## Adding a New Job

```bash
# Check for duplicates first
python3 scripts/application-lock.py check --company "ACME" --title "VP Digital"

# If clear, add to pipeline
python3 scripts/notion-pipeline-sync.py add \
  --title "VP Digital Transformation" \
  --company "ACME Health" \
  --tier 1 \
  --status "Discovered" \
  --source "LinkedIn" \
  --url "https://..."
```

---

## Stale Application Rule

- Any job in **Applied** status for >14 days with no movement = stale
- Sunday check: query pipeline for stale apps
- Action: draft follow-up email and present to Ahmed for approval
- If no response after 30 days total → move to Rejected with note "No response"

---

## Notion DB Properties (Reference)

| Property | Type | Notes |
|---|---|---|
| Title | Title | Job title |
| Company | Text | Company name |
| Status | Select | Pipeline status |
| Tier | Select | 1 / 2 / 3 |
| Source | Select | Platform where found |
| URL | URL | Job posting link |
| Date Applied | Date | When submitted |
| CV File | Files | Tailored CV PDF |
| Notes | Text | Free notes |
| Salary Range | Text | Posted or researched |
| Contact | Text | Recruiter name/email |
