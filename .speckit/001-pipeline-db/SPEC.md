# SPEC: Pipeline Intelligence Database

## Problem Statement

The Nasr Command Center has 213+ job applications tracked across 6+ disconnected data sources:
- `jobs-bank/applied-job-ids.txt` (flat text, inconsistent format)
- `coordination/pipeline.json` (6 records, stale since Mar 19)
- `cvs/*.pdf` (165 files, no link to which job)
- `data/jd-cache/*.json` (~60 JDs, no link to applications)
- `data/jobs-merged.json` (daily refresh, no historical state)
- `data/jobs-summary.json` (scores, no persistence)

**Result:** When a recruiter contacts Ahmed, we cannot find which CV they have. 29 CVs built in one session are lost to /tmp/. No funnel analytics. No keyword intelligence. No CV clustering capability.

## Solution

A single SQLite database (`data/nasr-pipeline.db`) accessed through one shared Python module (`scripts/pipeline_db.py`). Every agent reads from and writes to this database. No direct JSON file manipulation for application lifecycle data.

## Design Principles

1. **One module, one throat to choke.** All DB access goes through `pipeline_db.py`. No script touches SQLite directly.
2. **Additive schema.** New fields are added with `ALTER TABLE ADD COLUMN`. Nothing breaks when we evolve.
3. **Backward compatible rollout.** Scripts continue writing JSON files during transition. DB writes are added alongside, not instead of. Once verified, JSON writes are removed.
4. **WAL mode.** SQLite Write-Ahead Logging for concurrent read access from multiple agents.
5. **Migration before modification.** All existing data is imported before any script is changed.
6. **Zero new crons.** No new scheduled jobs. Existing scripts gain DB awareness.

## Database Schema

### Table: `jobs`
Primary record for every opportunity from discovery to final state.

```sql
CREATE TABLE jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT UNIQUE,          -- LinkedIn/Indeed/Google ID (e.g., "4366706927", "indeed-in-xxx")
    source          TEXT,                 -- linkedin, indeed, google, bayt, manual, recruiter
    company         TEXT NOT NULL,
    title           TEXT NOT NULL,
    location        TEXT,
    country         TEXT,                 -- UAE, Saudi, Qatar, etc.
    job_url         TEXT,
    
    -- JD
    jd_text         TEXT,                 -- Full job description
    jd_path         TEXT,                 -- Path to cached JD JSON
    jd_fetched_at   TEXT,                 -- ISO timestamp
    
    -- Scoring
    ats_score       INTEGER,              -- 0-100
    fit_score       INTEGER,              -- 0-10
    verdict         TEXT,                 -- SUBMIT, REVIEW, SKIP
    score_notes     TEXT,                 -- LLM reasoning
    
    -- CV
    cv_path         TEXT,                 -- Path to PDF in cvs/
    cv_html_path    TEXT,                 -- Path to HTML source
    cv_cluster      TEXT,                 -- PMO, Digital Transformation, Data/AI, Strategy, CTO
    cv_built_at     TEXT,                 -- ISO timestamp
    
    -- Application
    status          TEXT DEFAULT 'discovered',  
    -- Lifecycle: discovered → scored → cv_built → applied → response → screening → interview → offer → accepted → rejected → withdrawn → stale
    applied_date    TEXT,                 -- ISO date
    applied_via     TEXT,                 -- linkedin, indeed, email, recruiter_direct
    
    -- Recruiter
    recruiter_name  TEXT,
    recruiter_email TEXT,
    recruiter_company TEXT,              -- The agency (e.g., "Le Chene Recruitment")
    recruiter_phone TEXT,
    
    -- Follow-up
    follow_up_date  TEXT,
    next_action     TEXT,
    
    -- Salary
    salary_range    TEXT,
    salary_currency TEXT,
    
    -- Notion sync
    notion_page_id  TEXT,
    notion_synced   INTEGER DEFAULT 0,
    
    -- Meta
    tags            TEXT,                 -- JSON array: ["saudi", "fintech", "visa_2030"]
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_verdict ON jobs(verdict);
CREATE INDEX idx_jobs_source ON jobs(source);
```

### Table: `interactions`
Every touchpoint with an opportunity.

```sql
CREATE TABLE interactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT REFERENCES jobs(job_id),
    type            TEXT NOT NULL,        -- email_inbound, email_outbound, call, whatsapp, linkedin_message, interview
    date            TEXT NOT NULL,        -- ISO timestamp
    summary         TEXT,
    from_name       TEXT,
    from_email      TEXT,
    channel         TEXT,                 -- gmail, whatsapp, linkedin, phone
    next_action     TEXT,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_interactions_job_id ON interactions(job_id);
```

### Table: `keywords`
Aggregated keyword intelligence from JDs.

```sql
CREATE TABLE keywords (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword         TEXT UNIQUE NOT NULL,
    frequency       INTEGER DEFAULT 1,    -- How many JDs contain it
    in_master_cv    INTEGER DEFAULT 0,    -- Boolean: is it in Ahmed's master CV?
    category        TEXT,                 -- technical, leadership, domain, certification
    last_seen       TEXT                  -- ISO date of most recent JD containing it
);

CREATE INDEX idx_keywords_frequency ON keywords(frequency DESC);
```

### Table: `cv_templates`
Track CV cluster templates for reuse.

```sql
CREATE TABLE cv_templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_name    TEXT UNIQUE NOT NULL,  -- e.g., "PMO", "Digital Transformation", "Data/AI"
    template_path   TEXT,                 -- Path to base HTML template
    target_keywords TEXT,                 -- JSON array of keywords this template optimizes for
    jobs_covered    INTEGER DEFAULT 0,    -- How many jobs this template served
    avg_ats_score   REAL,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
```

## Module API: `pipeline_db.py`

### Write Functions
```python
register_job(source, job_id, company, title, location=None, url=None, jd_text=None, **extra) → job_id
update_score(job_id, ats_score=None, fit_score=None, verdict=None, notes=None)
attach_cv(job_id, cv_path, cv_html_path=None, cluster=None)
mark_applied(job_id, applied_date=None, applied_via=None)
log_interaction(job_id, type, summary, from_name=None, from_email=None, channel=None)
update_status(job_id, new_status, notes=None)
update_field(job_id, **fields)  # Flexible: update any column
```

### Read Functions
```python
get_job(job_id) → dict or None
get_by_company(company) → list[dict]
search(company=None, title=None, status=None, location=None, verdict=None, source=None) → list[dict]
get_stale(days=7) → list[dict]  # Applied but no response
get_funnel() → dict  # {discovered: N, scored: N, applied: N, ...}
get_recent(days=1) → list[dict]
get_all(status=None) → list[dict]
count_by_status() → dict
```

### Intelligence Functions
```python
analyze_keywords(top_n=50) → list[dict]  # Most frequent JD keywords
keyword_gaps() → list[dict]  # Keywords in JDs but NOT in master CV
suggest_clusters(n=5) → list[dict]  # Group jobs by similarity
get_cv_reuse_candidates(job_id) → list[dict]  # Similar jobs that could share a CV
funnel_conversion() → dict  # Drop-off analysis
```

### Utility Functions
```python
export_csv(filepath) → int  # Export all data
backup() → str  # Copy DB file with timestamp
```

## Scripts to Modify

### Phase 1 — Source scripts (INSERT new jobs)
| Script | Change |
|--------|--------|
| `jobs-source-linkedin.py` | After writing JSON, also call `register_job()` |
| `jobs-source-indeed.py` | Same |
| `jobs-source-google.py` | Same |

### Phase 2 — Merge (UPSERT)
| Script | Change |
|--------|--------|
| `jobs-merge.py` | After merge, call `register_job()` for each merged record |

### Phase 2b — Enrichment (UPDATE)
| Script | Change |
|--------|--------|
| `jobs-enrich-jd.py` | After fetching JD, call `update_field(job_id, jd_text=..., jd_path=...)` |

### Phase 3 — Review (UPDATE)
| Script | Change |
|--------|--------|
| `jobs-review.py` | After scoring, call `update_score()` |
| `job-scorer.py` | Same |

### Phase 4+ — Pipeline (READ/WRITE)
| Script | Change |
|--------|--------|
| `push-submit-to-notion.py` | After push, call `update_field(job_id, notion_synced=1, notion_page_id=...)` |
| `sync-applied-from-notion.py` | After sync, call `mark_applied()` for each |
| `add-to-pipeline.py` | Rewrite to call `register_job()` |
| `pipeline-agent.py` | Rewrite to `SELECT` from DB instead of counting files |

### Data consumers (READ)
| Script | Change |
|--------|--------|
| `briefing-agent.py` | Add DB reads alongside existing JSON reads |
| `pam-telegram.py` | Same |
| `nasr-doctor.py` | Add `check_pipeline_db()` health check |
| `weekly-pipeline-audit.py` | Rewrite to query DB |
| `company-dossier.py` | Add DB lookup for existing application context |
| `auto-cv-builder.py` | Query DB for unbuilt CVs |

### Session-level (ME)
| Action | DB Call |
|--------|---------|
| Ahmed shares job link | `register_job(source='manual', ...)` |
| Ahmed says "applied" | `mark_applied()` |
| Ahmed says "got a response" | `log_interaction()` + `update_status()` |
| Ahmed asks "what do we have on FAB?" | `get_by_company('FAB')` |
| CV agent builds a CV | `attach_cv()` |

## Migration Plan

### Step 1: Create empty database
Run schema creation SQL.

### Step 2: Import existing data (priority order)
1. `cvs/*.pdf` — Parse filenames for company + role, use file timestamps for dates
2. `jobs-bank/applied-job-ids.txt` — Parse the structured lines
3. `coordination/pipeline.json` — 6 detailed records
4. `data/jd-cache/*.json` — Link JDs to job IDs
5. `data/jobs-merged.json` — Current discovered jobs
6. `data/jobs-summary.json` — Scores and verdicts
7. Session memory — Tonight's 29 CVs with full context

### Step 3: Cross-reference and deduplicate
Match CVs to applied IDs by company name + role title similarity.

## Rollback Plan

- Original JSON files are NOT deleted during transition
- `pipeline_db.py` has a `ENABLED = True` flag — set to `False` to disable all DB writes
- Daily backup: `data/backups/nasr-pipeline-YYYY-MM-DD.db`
- If tomorrow's 5 AM briefing breaks, revert modified scripts via `git checkout`

## Success Criteria

1. ✅ All 200+ existing records imported with <5% data loss
2. ✅ `get_by_company("FAB")` returns complete history
3. ✅ Tonight's 29 CVs are linked to their jobs
4. ✅ Tomorrow's 5 AM pipeline runs without errors
5. ✅ `keyword_gaps()` returns actionable insights
6. ✅ Zero new cron jobs
7. ✅ Ahmed can ask natural language questions, I translate to SQL

## Non-Goals (Explicit)

- No web dashboard (I am the interface)
- No REST API
- No real-time sync to Notion (push remains batch)
- No changes to LinkedIn posting or Content Agent
- No changes to cron schedules
