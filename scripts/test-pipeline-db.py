#!/usr/bin/env python3
"""
test-pipeline-db.py - Tests for pipeline_db.py (the most depended-on module).

Uses in-memory SQLite for speed and isolation.
Target: 25+ assertions covering every write function.
"""

import sys
import os
import tempfile
import sqlite3
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch DB_PATH to use temp file before importing
_tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmpfile.close()
TEST_DB_PATH = _tmpfile.name

# We need to patch before import
import pipeline_db as pdb
from pathlib import Path
pdb.DB_PATH = Path(TEST_DB_PATH)
pdb.init_db()

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} — {detail}")


def run_tests():
    global passed, failed

    print("\n" + "=" * 60)
    print("TEST SUITE: pipeline_db.py")
    print("=" * 60)

    # ── 1. url_hash determinism ──────────────────────────────────────────
    print("\n[1/9] url_hash")
    h1 = pdb.url_hash("https://linkedin.com/jobs/view/12345")
    h2 = pdb.url_hash("https://linkedin.com/jobs/view/12345")
    h3 = pdb.url_hash("https://linkedin.com/jobs/view/99999")
    test("Same URL = same hash", h1 == h2)
    test("Different URL = different hash", h1 != h3)
    test("Hash length is 12", len(h1) == 12)
    test("Hash is hex chars only", all(c in "0123456789abcdef" for c in h1))

    # ── 2. register_job + get_job round-trip ─────────────────────────────
    print("\n[2/9] register_job + get_job")
    job_id = pdb.register_job(
        source="linkedin",
        job_id="test-001",
        company="Acme Corp",
        title="Senior PM",
        location="Dubai, UAE",
        url="https://linkedin.com/jobs/view/test001",
    )
    test("register_job returns job_id", job_id == "test-001")
    job = pdb.get_job("test-001")
    test("get_job returns dict", job is not None and isinstance(job, dict))
    test("Company round-trip", job["company"] == "Acme Corp")
    test("Title round-trip", job["title"] == "Senior PM")
    test("Location round-trip", job["location"] == "Dubai, UAE")
    test("URL round-trip", job["job_url"] == "https://linkedin.com/jobs/view/test001")
    test("Default status is discovered", job["status"] == "discovered")

    # ── 3. register_job duplicate handling (INSERT OR IGNORE) ────────────
    print("\n[3/9] Duplicate handling")
    job_id2 = pdb.register_job(
        source="linkedin",
        job_id="test-001",
        company="Acme Corp",
        title="Senior PM",
        location="Dubai, UAE",
        url="https://linkedin.com/jobs/view/test001",
        jd_text="This is the job description.",
    )
    test("Duplicate returns same job_id", job_id2 == "test-001")
    job_after = pdb.get_job("test-001")
    test("JD enriched on duplicate", job_after.get("jd_text") == "This is the job description.")

    # ── 4. _generate_job_id determinism ──────────────────────────────────
    print("\n[4/9] _generate_job_id")
    id_a = pdb._generate_job_id("linkedin", "acme", "pm", "https://example.com/job1")
    id_b = pdb._generate_job_id("linkedin", "acme", "pm", "https://example.com/job1")
    id_c = pdb._generate_job_id("linkedin", "acme", "pm", "https://example.com/job2")
    test("Same inputs = same ID", id_a == id_b)
    test("Different URL = different ID", id_a != id_c)
    # With URL, should use url_hash
    test("URL-based ID matches url_hash", id_a == pdb.url_hash("https://example.com/job1"))
    # Without URL, falls back to gen- prefix
    id_no_url = pdb._generate_job_id("linkedin", "acme", "pm", "")
    test("No-URL ID has gen- prefix", id_no_url.startswith("gen-"))

    # ── 5. update_status ─────────────────────────────────────────────────
    print("\n[5/9] update_status")
    result = pdb.update_status("test-001", "applied")
    test("update_status returns True", result is True)
    job_updated = pdb.get_job("test-001")
    test("Status actually changed to applied", job_updated["status"] == "applied")

    # ── 6. mark_applied ──────────────────────────────────────────────────
    print("\n[6/9] mark_applied")
    pdb.register_job(source="indeed", job_id="test-002", company="Beta Inc",
                     title="Director", url="https://indeed.com/j/test002")
    result = pdb.mark_applied("test-002", applied_date="2026-03-24")
    test("mark_applied returns True", result is True)
    job_applied = pdb.get_job("test-002")
    test("Status changed to applied", job_applied["status"] == "applied")
    test("Applied date set", job_applied["applied_date"] == "2026-03-24")

    # ── 7. update_score ──────────────────────────────────────────────────
    print("\n[7/9] update_score")
    result = pdb.update_score("test-001", ats_score=85, fit_score=7, verdict="SUBMIT")
    test("update_score returns True", result is True)
    job_scored = pdb.get_job("test-001")
    test("ATS score persisted", job_scored["ats_score"] == 85)
    test("Fit score persisted", job_scored["fit_score"] == 7)
    test("Verdict persisted", job_scored["verdict"] == "SUBMIT")

    # ── 8. upsert_job (scanner path) ────────────────────────────────────
    print("\n[8/9] upsert_job (scanner)")
    r1 = pdb.upsert_job({
        "url": "https://linkedin.com/jobs/view/scanner-001",
        "title": "PMO Lead",
        "company": "Gamma LLC",
        "location": "Riyadh",
        "source": "exa",
        "status": "discovered",
    })
    test("New job inserted", r1 == "inserted")

    r2 = pdb.upsert_job({
        "url": "https://linkedin.com/jobs/view/scanner-001",
        "title": "PMO Lead",
        "company": "Gamma LLC",
        "ats_score": 78,
        "verdict": "APPLY",
        "status": "scored",
    })
    test("Existing job updated", r2 == "updated")

    # Verify enrichment persisted
    h = pdb.url_hash("https://linkedin.com/jobs/view/scanner-001")
    conn = pdb._get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE url_hash = ?", (h,)).fetchone()
    conn.close()
    test("ATS score from upsert persisted", dict(row)["ats_score"] == 78)

    # upsert should NOT overwrite applied status
    pdb.register_job(source="manual", job_id="protected-001", company="Delta Co",
                     title="VP Ops", url="https://linkedin.com/jobs/view/protected-001")
    pdb.update_status("protected-001", "applied")
    r3 = pdb.upsert_job({
        "url": "https://linkedin.com/jobs/view/protected-001",
        "status": "discovered",
        "ats_score": 90,
    })
    job_protected = pdb.get_job("protected-001")
    test("Applied status NOT overwritten by upsert", job_protected["status"] == "applied")
    test("Score still enriched on protected job", job_protected["ats_score"] == 90)

    # ── 9. get_stale + get_funnel + count_by_status consistency ──────────
    print("\n[9/9] Aggregates")
    stale = pdb.get_stale(days=0)  # days=0 means everything is stale
    test("get_stale returns list", isinstance(stale, list))

    funnel = pdb.get_funnel()
    test("get_funnel returns dict", isinstance(funnel, dict))

    counts = pdb.count_by_status()
    test("count_by_status returns dict", isinstance(counts, dict))

    # Funnel and count should agree on total (exclude _total key from sum)
    funnel_total = funnel.get("_total", 0)
    count_total = sum(v for k, v in counts.items() if k != "_total")
    test("Funnel total matches count_by_status total", funnel_total == count_total,
         f"funnel={funnel_total}, count={count_total}")

    scanner_stats = pdb.get_scanner_funnel_stats()
    test("get_scanner_funnel_stats returns dict", isinstance(scanner_stats, dict))

    # is_duplicate
    test("is_duplicate finds existing URL", pdb.is_duplicate("https://linkedin.com/jobs/view/scanner-001"))
    test("is_duplicate rejects unknown URL", not pdb.is_duplicate("https://example.com/nope"))

    # is_company_tracked
    test("is_company_tracked finds applied company", pdb.is_company_tracked("Delta Co"))
    test("is_company_tracked rejects unknown", not pdb.is_company_tracked("Nonexistent Corp"))

    # export_csv
    csv_path = os.path.join(tempfile.gettempdir(), "test-pipeline-export.csv")
    n = pdb.export_csv(csv_path)
    test("export_csv returns row count > 0", n > 0)
    test("CSV file created", os.path.exists(csv_path))
    if os.path.exists(csv_path):
        os.remove(csv_path)

    # ── 10. Status history (D7) ──────────────────────────────────────────
    print("\n[10/12] Status history (D7)")
    # update_status should record transition
    pdb.register_job(source="test", job_id="hist-001", company="HistCo", title="PM",
                     url="https://example.com/hist001")
    pdb.update_status("hist-001", "scored")
    pdb.update_status("hist-001", "applied")
    pdb.update_status("hist-001", "interview")
    history = pdb.get_status_history("hist-001")
    test("Status history has 3 transitions", len(history) == 3,
         f"got {len(history)}")
    test("First transition: discovered->scored", 
         history[0]["from_status"] == "discovered" and history[0]["to_status"] == "scored" if history else False)
    test("Last transition: applied->interview",
         history[-1]["from_status"] == "applied" and history[-1]["to_status"] == "interview" if history else False)

    # get_recent_transitions
    recent = pdb.get_recent_transitions(days=1, to_status="interview")
    test("Recent interview transitions found", len(recent) >= 1)

    # get_stage_velocity
    velocity = pdb.get_stage_velocity()
    test("Stage velocity returns dict", isinstance(velocity, dict))

    # ── 11. Recruiters (D9) ──────────────────────────────────────────────
    print("\n[11/12] Recruiters (D9)")
    rid1 = pdb.add_recruiter(name="Sarah HR", email="sarah@acme.com", company="Acme Corp")
    test("add_recruiter returns positive ID", rid1 > 0)

    # Dedup by email
    rid2 = pdb.add_recruiter(name="Sarah Updated", email="sarah@acme.com", phone="+971555")
    test("Same email returns same recruiter ID", rid1 == rid2)

    # Link to job
    linked = pdb.link_recruiter_to_job("test-001", rid1)
    test("link_recruiter_to_job succeeds", linked is True)

    # Duplicate link should not error
    linked2 = pdb.link_recruiter_to_job("test-001", rid1)
    test("Duplicate link doesn't error", linked2 is True)

    # Get job's recruiters
    job_recs = pdb.get_job_recruiters("test-001")
    test("get_job_recruiters returns recruiter", len(job_recs) >= 1)
    test("Recruiter has correct name", any(r["name"] == "Sarah Updated" for r in job_recs))

    # Get recruiter's jobs
    rec_jobs = pdb.get_recruiter_jobs(rid1)
    test("get_recruiter_jobs returns job", len(rec_jobs) >= 1)

    # Update contacted
    contacted = pdb.update_recruiter_contacted(rid1)
    test("update_recruiter_contacted succeeds", contacted is True)

    # ── 12. No-op on same status ─────────────────────────────────────────
    print("\n[12/12] Edge cases")
    pdb.update_status("hist-001", "interview")  # same status again
    history2 = pdb.get_status_history("hist-001")
    test("Same-status update doesn't add history row", len(history2) == 3,
         f"got {len(history2)}")

    # upsert_job with empty URL
    r_empty = pdb.upsert_job({"url": "", "title": "Nothing"})
    test("upsert_job with empty URL returns skipped", r_empty == "skipped")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    try:
        success = run_tests()
    finally:
        # Cleanup temp DB
        try:
            os.remove(TEST_DB_PATH)
        except:
            pass
    sys.exit(0 if success else 1)
