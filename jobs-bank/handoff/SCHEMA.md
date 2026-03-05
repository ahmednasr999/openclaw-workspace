# Agent Handoff Schema — Standard Format

*Version: 1.0 | Created: 2026-02-28*
*Purpose: Shared data contract between agents. Every agent reads from and writes to this format.*
*Rule: No agent announces "done" until it has written a valid handoff file.*

---

## File Naming Convention

```
jobs-bank/handoff/<job-id>.json
```

Where `<job-id>` = `YYYY-MM-DD-<company-slug>-<role-slug>`
Example: `2026-02-28-cooper-fitch-exec-director`

---

## Schema (JSON)

```json
{
  "job_id": "YYYY-MM-DD-company-role",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp",
  "status": "new | researched | cv_ready | applied | interview | closed",

  "job": {
    "company": "Company Name",
    "role": "Exact Job Title",
    "location": "City, Country",
    "url": "LinkedIn or direct URL",
    "salary_range": "50-60K AED or null",
    "jd_raw": "Full job description text",
    "jd_keywords": ["keyword1", "keyword2"],
    "ats_score": 91,
    "vision_2030_angle": true,
    "priority": "HIGH | MEDIUM | LOW"
  },

  "research": {
    "company_summary": "2-3 sentence company overview",
    "funding_stage": "Series A / Public / Private / null",
    "headcount": "approx number or null",
    "recent_news": ["headline 1", "headline 2"],
    "hiring_manager": "Name or null",
    "linkedin_connections": 0,
    "notes": "Any other intel"
  },

  "cv": {
    "path": "cvs/Ahmed Nasr - Role - Company.pdf",
    "github_url": "https://github.com/ahmednasr999/openclaw-nasr/blob/master/cvs/...",
    "ats_score": 91,
    "tailoring_notes": "Key adjustments made vs master CV",
    "pending_review": false
  },

  "application": {
    "applied_at": "ISO8601 or null",
    "channel": "LinkedIn | Email | Portal | null",
    "follow_up_due": "YYYY-MM-DD or null",
    "outcome": "pending | interview | rejected | offer | cold"
  },

  "content": {
    "linkedin_post_drafted": false,
    "post_theme": "Theme or null",
    "post_path": "path to draft or null"
  },

  "nasr_review": {
    "approved": false,
    "flags": [],
    "recommendation": "Apply | Hold | Skip"
  }
}
```

---

## Agent Responsibilities

| Agent | Reads | Writes |
|-------|-------|--------|
| Job Hunter | — | `job` section (status: new) |
| Researcher | `job` section | `research` section (status: researched) |
| CV Optimizer | `job` + `research` sections | `cv` section (status: cv_ready) |
| Content Creator | `job` + `cv` sections | `content` section |
| NASR | Full file | `nasr_review` section + presents to Ahmed |

---

## ATS Scoring Protocol (Updated Mar 5, 2026)

- **Scoring model:** MiniMax M2.5 (primary), Opus 4.6 (borderline tie-breaker)
- **Threshold:** 82/100 (SUBMIT), 75-81 (REVIEW), <75 (SKIP)
- **Borderline rule:** If MiniMax scores 82-87, auto-escalate to Opus for second opinion
- **Never use Haiku for ATS scoring** (inflates scores, +4.0 avg drift from Opus)

## Pipeline Status Flow

```
new → researched → cv_ready → applied → interview → closed
```

NASR checks all handoff files with `status: cv_ready` and `nasr_review.approved: false` at each session start.

---

**Links:** [[../../MEMORY.md]] | [[../pipeline.md]] | [[../../memory/active-tasks.md]]
