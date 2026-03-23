# TASKS: Pipeline Intelligence Database

## Phase A: Foundation

- [ ] A1: Create `scripts/pipeline_db.py` — schema, WAL mode, all write/read/intelligence/utility functions, kill switch, thread-safe connections
- [ ] A2: Create `scripts/migrate_to_db.py` — import from 7 sources, cross-reference CVs to jobs, idempotent, print stats
- [ ] A3: Run migration, verify counts, spot-check 5 records, test get_by_company("FAB") and get_funnel()
- [ ] A4: Import tonight's 29 CVs from session memory with full job mapping

## Phase B: Writer Integration (dual-write alongside JSON)

- [ ] B1: `jobs-source-linkedin.py` — add register_job() calls after JSON write
- [ ] B2: `jobs-source-indeed.py` — add register_job() calls after JSON write
- [ ] B3: `jobs-source-google.py` — add register_job() calls after JSON write
- [ ] B4: `jobs-merge.py` — add register_job() UPSERT after merge
- [ ] B5: `jobs-enrich-jd.py` — add update_field() for jd_text and jd_path
- [ ] B6: `jobs-review.py` — add update_score() after LLM scoring
- [ ] B7: `job-scorer.py` — add update_score() after ATS scoring
- [ ] B8: `push-submit-to-notion.py` — add update_field(notion_synced, notion_page_id)
- [ ] B9: `sync-applied-from-notion.py` — add mark_applied() for each synced job
- [ ] B10: `add-to-pipeline.py` — add register_job() call
- [ ] B11: `email-agent.py` — add log_interaction() + update_status() on recruiter reply detection
- [ ] B12: `outreach-agent.py` — add log_interaction() on outreach send

## Phase C: Reader Integration (DB reads with JSON fallback)

- [ ] C1: `pipeline-agent.py` — add DB query path with JSON fallback
- [ ] C2: `briefing-agent.py` — add DB-sourced sections (stale, funnel, follow-ups)
- [ ] C3: `pam-telegram.py` — add DB-sourced summary
- [ ] C4: `nasr-doctor.py` — add check_pipeline_db() health check
- [ ] C5: `weekly-pipeline-audit.py` — rewrite to query DB
- [ ] C6: `company-dossier.py` — add DB lookup for company history
- [ ] C7: `auto-cv-builder.py` — add DB query for unbuilt CVs

## Phase D: Verification

- [ ] D1: Manual full pipeline run (bash scripts/run-briefing-pipeline.sh --all)
- [ ] D2: Data integrity check (counts, no dupes, stale detection, funnel sanity)
- [ ] D3: Rollback test (ENABLED=False → pipeline works → ENABLED=True)

## Phase E: Cleanup (after 48h stable)

- [ ] E1: Remove JSON dual-write from all modified scripts
- [ ] E2: Archive applied-job-ids.txt and coordination/pipeline.json
- [ ] E3: Add daily DB backup to nasr-doctor.py
- [ ] E4: Update MEMORY.md and TOOLS.md with new architecture

---

## Build Strategy

**Phases A-D will be built by a sub-agent (Opus 4.6) in one session.**

The sub-agent receives:
1. This TASKS.md
2. The SPEC.md (full schema + API)
3. The PLAN.md (implementation order)
4. Access to all scripts in /root/.openclaw/workspace/scripts/

Phase E is manual — executed 48 hours after stable operation.
