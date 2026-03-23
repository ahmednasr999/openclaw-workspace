# PLAN: Pipeline Intelligence Database

## Implementation Order

The build follows a strict dependency chain. Each phase must complete before the next starts.

---

### Phase A: Foundation (no script changes)
**Goal:** Create the DB module and populate it with all existing data. Nothing breaks because nothing uses it yet.

**A1. Create `scripts/pipeline_db.py`**
- SQLite schema creation (4 tables)
- WAL mode enabled
- All write functions (register_job, update_score, attach_cv, mark_applied, log_interaction, update_status, update_field)
- All read functions (get_job, get_by_company, search, get_stale, get_funnel, get_recent, count_by_status)
- Intelligence functions (analyze_keywords, keyword_gaps, suggest_clusters)
- Utility functions (export_csv, backup)
- DB path: `data/nasr-pipeline.db`
- Logging to stderr for debugging
- Thread-safe connection handling (each call opens/closes, or use thread-local)
- `ENABLED` flag for kill switch

**A2. Create `scripts/migrate_to_db.py`**
- Import from `cvs/*.pdf` (parse filenames → company + role + date from mtime)
- Import from `jobs-bank/applied-job-ids.txt` (parse structured lines)
- Import from `coordination/pipeline.json` (6 detailed records)
- Import from `data/jd-cache/*.json` (match job_id from filename)
- Import from `data/jobs-merged.json` (current batch)
- Import from `data/jobs-summary.json` (scores + verdicts)
- Cross-reference: match CVs to jobs by company+title fuzzy match
- Report: print import stats (imported, skipped, matched, orphaned)
- Idempotent: can run multiple times without duplicating

**A3. Run migration**
- Execute migrate_to_db.py
- Verify record counts
- Spot-check 5 records manually
- Test: `get_by_company("FAB")` returns data
- Test: `get_funnel()` returns sensible numbers

**A4. Import tonight's 29 CVs**
- Use session memory to map each CV to its job
- Call attach_cv() for each
- Verify all 29 are linked

---

### Phase B: Writer Integration (scripts that CREATE data)
**Goal:** Scripts start writing to DB alongside existing JSON files. Dual-write pattern.

**B1. Job source scripts** (parallel changes, independent)
- `jobs-source-linkedin.py`: After saving JSON, call `register_job()` for each job
- `jobs-source-indeed.py`: Same pattern
- `jobs-source-google.py`: Same pattern

**B2. Merge script**
- `jobs-merge.py`: After merge, call `register_job()` with UPSERT logic for each merged record

**B3. Enrichment script**
- `jobs-enrich-jd.py`: After fetching JD, call `update_field(job_id, jd_text=..., jd_path=...)`

**B4. Review scripts**
- `jobs-review.py`: After LLM scoring, call `update_score()` for each reviewed job
- `job-scorer.py`: After ATS scoring, call `update_score()`

**B5. Notion sync scripts**
- `push-submit-to-notion.py`: After push, call `update_field(notion_synced=1, notion_page_id=...)`
- `sync-applied-from-notion.py`: After sync, call `mark_applied()` for each applied job

**B6. Manual add script**
- `add-to-pipeline.py`: Add `register_job()` call

**B7. Email agent**
- `email-agent.py`: When recruiter reply detected, call `log_interaction()` + `update_status()`

**B8. Outreach agent**
- `outreach-agent.py`: When outreach sent, call `log_interaction()`

---

### Phase C: Reader Integration (scripts that CONSUME data)
**Goal:** Scripts start reading from DB. Keep JSON fallback initially.

**C1. Pipeline agent**
- `pipeline-agent.py`: Add DB query path. If DB has data, use it. Else fall back to file counting.

**C2. Briefing consumers**
- `briefing-agent.py`: Add DB-sourced sections (stale apps, funnel, upcoming follow-ups)
- `pam-telegram.py`: Add DB-sourced summary line

**C3. Health check**
- `nasr-doctor.py`: Add `check_pipeline_db()` — verify DB exists, has recent data, no corruption

**C4. Audit + research**
- `weekly-pipeline-audit.py`: Rewrite to query DB for weekly metrics
- `company-dossier.py`: Add DB lookup for "do we have history with this company?"
- `auto-cv-builder.py`: Add DB query for unbuilt CVs

---

### Phase D: Verification
**Goal:** Confirm everything works before the 5 AM briefing.

**D1. Manual pipeline run**
- Run `bash scripts/run-briefing-pipeline.sh --all` manually
- Check all phases complete
- Verify DB was populated by each phase

**D2. Data integrity check**
- Compare DB record count vs file-based count
- Verify no duplicate job_ids
- Check that stale detection works
- Check that funnel numbers make sense

**D3. Rollback test**
- Set `ENABLED = False` in pipeline_db.py
- Verify pipeline still runs on JSON files
- Set back to True

---

### Phase E: Cleanup (after 48h of stable operation)
**Goal:** Remove dual-write. DB is single source of truth.

- Remove JSON write paths from modified scripts
- Archive `jobs-bank/applied-job-ids.txt` (no longer updated)
- Archive `coordination/pipeline.json` (no longer updated)
- Add daily DB backup to nasr-doctor.py
- Update MEMORY.md and TOOLS.md with new architecture

---

## Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| DB file corruption | WAL mode + daily backup + git-tracked copy |
| Script breaks mid-pipeline | Dual-write: JSON still works as fallback |
| Concurrent write conflict | WAL mode + short transactions + retry on SQLITE_BUSY |
| Migration data loss | Idempotent migration, run multiple times |
| 5 AM briefing fails | git checkout to revert all modified scripts in <60s |
| Schema needs new fields | ALTER TABLE ADD COLUMN — zero downtime |

## Time Estimate

| Phase | Estimated |
|-------|-----------|
| A: Foundation | 30-40 min |
| B: Writers | 20-30 min |
| C: Readers | 15-20 min |
| D: Verification | 10-15 min |
| **Total** | **~90 min** |
