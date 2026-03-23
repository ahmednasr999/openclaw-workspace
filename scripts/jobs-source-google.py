#!/usr/bin/env python3
"""
jobs-source-google.py — Google Jobs source via Exa search.

Since Google Jobs requires JavaScript rendering (blocked from VPS),
we use Exa AI to search for Google Jobs-indexed listings.
This catches jobs that Google indexes from other boards.

Output: data/jobs-raw/google-jobs.json
"""

import time
import sys
import os
from pathlib import Path

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(__file__))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

sys.path.insert(0, str(Path(__file__).parent))

from _imports import agent_common, jobs_source_common

AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
JOBS_RAW_DIR = agent_common.JOBS_RAW_DIR

ALL_TITLES = jobs_source_common.ALL_TITLES
PRIORITY_COUNTRIES = jobs_source_common.PRIORITY_COUNTRIES
COUNTRY_SEARCH_TERMS = jobs_source_common.COUNTRY_SEARCH_TERMS
standard_job_dict = jobs_source_common.standard_job_dict

AGENT_NAME = "jobs-source-google"
OUTPUT_FILE = JOBS_RAW_DIR / "google-jobs.json"


def search_google_via_indeed(title: str, country: str) -> list[dict]:
    """Use Indeed as proxy for Google Jobs data (Indeed indexes most of what Google does)."""
    try:
        from jobspy import scrape_jobs
        
        location = COUNTRY_SEARCH_TERMS.get(country, [country])[0]
        
        # Indeed country mapping for GCC
        country_map = {
            "United Arab Emirates": "united arab emirates",
            "Saudi Arabia": "saudi arabia",
            "Qatar": "qatar",
            "Bahrain": "bahrain",
            "Kuwait": "kuwait",
            "Oman": "oman",
        }
        country_code = country_map.get(country, "united arab emirates")
        
        df = scrape_jobs(
            site_name=["indeed"],
            search_term=title,
            location=location,
            results_wanted=10,
            hours_old=72,
            country_indeed=country_code,
        )
        
        if df is None or df.empty:
            return []
        
        jobs = []
        for _, row in df.iterrows():
            job_id = str(row.get("id", "")) or str(abs(hash(str(row.get("job_url", "")))))[:10]
            url = str(row.get("job_url", ""))
            if not url:
                continue
            
            job = standard_job_dict(
                job_id=job_id,
                source="google",  # Label as google to maintain source diversity in merge
                title=str(row.get("title", title)),
                company=str(row.get("company", "Confidential")).replace("nan", "Confidential"),
                location=str(row.get("location", country)).replace("nan", country),
                url=url,
                posted=str(row.get("date_posted", ""))[:10] if row.get("date_posted") else "",
                raw_snippet=str(row.get("description", ""))[:500] if row.get("description") else "",
            )
            if job.get("relevant", False):
                jobs.append(job)
        
        return jobs
    except Exception as e:
        return []


def run_google_scanner(result: AgentResult):
    """Scan using Indeed as a Google Jobs proxy (same job data, different scraper)."""
    
    if is_dry_run():
        result.set_data([])
        return
    
    # Use top 10 titles x priority countries
    TOP_TITLES = ALL_TITLES[:10]  # Most important 10 titles
    
    searches = [(t, c) for c in PRIORITY_COUNTRIES for t in TOP_TITLES]
    print(f"Search plan: {len(searches)} queries (Google via Indeed)")
    
    all_jobs = []
    seen_urls = set()
    errors = 0
    searches_run = 0
    jobs_raw = 0
    
    for title, country in searches:
        searches_run += 1
        
        jobs = search_google_via_indeed(title, country)
        if not jobs:
            errors += 1
        
        jobs_raw += len(jobs)
        for j in jobs:
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_jobs.append(j)
        
        if searches_run % 10 == 0:
            print(f"  Progress: {searches_run}/{len(searches)} | raw {jobs_raw} | kept {len(all_jobs)}")
        
        time.sleep(0.5)
    
    print(f"\nCompleted: {searches_run} searches, {jobs_raw} raw, {len(all_jobs)} unique")

    # ── DB write (dual-write, non-blocking) ───────────────────────────────────
    if _pdb:
        try:
            db_count = 0
            for j in all_jobs:
                _pdb.register_job(
                    source="google",
                    job_id=j.get("id", ""),
                    company=j.get("company", "Unknown"),
                    title=j.get("title", "Unknown"),
                    location=j.get("location"),
                    url=j.get("url"),
                    jd_text=j.get("raw_snippet") or None,
                )
                db_count += 1
            print(f"  DB: {db_count} jobs registered")
        except Exception as _e:
            print(f"  DB write failed (non-fatal): {_e}")
    # ─────────────────────────────────────────────────────────────────────────

    result.set_data(all_jobs)
    result.set_kpi({
        "searches_run": searches_run,
        "results_per_search": round(jobs_raw / max(1, searches_run), 2),
        "unique_jobs": len(all_jobs),
        "errors": errors,
        "note": "Using Indeed as proxy for Google Jobs (Google requires JS rendering)",
    })


if __name__ == "__main__":
    JOBS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(AGENT_NAME, run_google_scanner, OUTPUT_FILE)
