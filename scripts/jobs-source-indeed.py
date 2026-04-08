#!/usr/bin/env python3
"""
jobs-source-indeed.py — Indeed job source adapter using python-jobspy.

Uses python-jobspy library to scrape Indeed jobs.
Searches 22 titles x top 3 countries only.
48h lookback window.

Output: data/jobs-raw/indeed.json
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

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from _imports import agent_common, jobs_source_common

# Import from agent_common
AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
JOBS_RAW_DIR = agent_common.JOBS_RAW_DIR

# Import from jobs_source_common
ALL_TITLES = jobs_source_common.ALL_TITLES
PRIORITY_COUNTRIES = jobs_source_common.PRIORITY_COUNTRIES
COUNTRY_SEARCH_TERMS = jobs_source_common.COUNTRY_SEARCH_TERMS
standard_job_dict = jobs_source_common.standard_job_dict

# Configuration
AGENT_NAME = "jobs-source-indeed"
OUTPUT_FILE = JOBS_RAW_DIR / "indeed.json"
RESULTS_PER_SEARCH = 10
HOURS_OLD = 48
RATE_LIMIT_DELAY = 1.5

# Indeed country codes
# JobSpy requires full country names (not 2-letter codes)
INDEED_COUNTRY_CODES = {
    "United Arab Emirates": "united arab emirates",
    "Saudi Arabia": "saudi arabia",
    "Qatar": "qatar",
    "Bahrain": "bahrain",
    "Kuwait": "kuwait",
    "Oman": "oman",
}


def search_indeed_jobs(title: str, country: str) -> list[dict]:
    """Search Indeed using jobspy. Returns list of job dicts."""
    try:
        from jobspy import scrape_jobs
        
        location = COUNTRY_SEARCH_TERMS.get(country, [country])[0]
        country_code = INDEED_COUNTRY_CODES.get(country, "ae")
        
        df = scrape_jobs(
            site_name=["indeed"],
            search_term=title,
            location=location,
            results_wanted=RESULTS_PER_SEARCH,
            hours_old=HOURS_OLD,
            country_indeed=country_code,
        )
        
        if df is None or df.empty:
            return []
        
        jobs = []
        for _, row in df.iterrows():
            job_id = str(row.get("id", "")) or str(abs(hash(str(row.get("job_url", "")))))[:10]
            job_title = str(row.get("title", title))
            company = str(row.get("company", "Confidential"))
            location_str = str(row.get("location", country))
            url = str(row.get("job_url", ""))
            posted = str(row.get("date_posted", ""))[:10] if row.get("date_posted") else ""
            description = str(row.get("description", ""))[:500] if row.get("description") else ""
            
            if not url:
                continue
            
            job = standard_job_dict(
                job_id=job_id,
                source="indeed",
                title=job_title,
                company=company if company != "nan" else "Confidential",
                location=location_str if location_str != "nan" else country,
                url=url,
                posted=posted if posted != "nan" else "",
                raw_snippet=description
            )
            jobs.append(job)
        
        return jobs
        
    except ImportError:
        print("  ERROR: jobspy not installed. Run: pip install python-jobspy")
        return []
    except Exception as e:
        error_str = str(e).lower()
        if "blocked" in error_str or "rate" in error_str or "403" in error_str:
            print(f"  Rate limited/blocked: {e}")
        else:
            print(f"  Search error: {e}")
        return []


def run_indeed_scanner(result: AgentResult):
    """Main scanner logic."""
    
    if is_dry_run():
        print("\n=== DRY RUN: Search Matrix ===")
        total_searches = 0
        
        print("\n--- Priority Countries (all 22 titles) ---")
        for country in PRIORITY_COUNTRIES:
            code = INDEED_COUNTRY_CODES.get(country, "?")
            print(f"\n  {country} ({code}):")
            for title in ALL_TITLES:
                print(f"    - {title}")
                total_searches += 1
        
        print(f"\n--- Total: {total_searches} searches ---")
        print(f"Estimated time: {total_searches * RATE_LIMIT_DELAY / 60:.1f} minutes")
        print(f"Results per search: {RESULTS_PER_SEARCH}")
        print(f"Hours old filter: {HOURS_OLD}h")
        
        result.set_data([])
        result.set_kpi({
            "searches_planned": total_searches,
            "countries": len(PRIORITY_COUNTRIES),
            "titles": len(ALL_TITLES),
        })
        return
    
    # Build search plan
    searches = []
    for country in PRIORITY_COUNTRIES:
        for title in ALL_TITLES:
            searches.append((title, country))
    
    print(f"Search plan: {len(searches)} queries (Indeed)")
    
    # Track stats
    searches_run = 0
    jobs_found_raw = 0
    seen_urls = set()
    all_jobs = []
    errors = 0
    countries_seen = {}
    titles_seen = {}
    
    for title, country in searches:
        searches_run += 1
        
        jobs = search_indeed_jobs(title, country)
        
        if not jobs:
            errors += 1
            time.sleep(0.5)
            continue
        
        jobs_found_raw += len(jobs)
        
        for job in jobs:
            if job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])
            
            if job.get("relevant", False):
                job["search_country"] = country
                job["search_title"] = title
                all_jobs.append(job)
                countries_seen[country] = countries_seen.get(country, 0) + 1
                titles_seen[title] = titles_seen.get(title, 0) + 1
        
        if searches_run % 10 == 0:
            print(f"  Progress: {searches_run}/{len(searches)} | found {jobs_found_raw} | kept {len(all_jobs)}")
        
        time.sleep(RATE_LIMIT_DELAY)
    
    print(f"\nCompleted: {searches_run} searches, {jobs_found_raw} raw, {len(all_jobs)} kept")

    # ── DB write (dual-write, non-blocking) ───────────────────────────────────
    if _pdb:
        try:
            db_count = 0
            for j in all_jobs:
                _pdb.register_job(
                    source="indeed",
                    job_id=j.get("id", ""),
                    company=j.get("company", "Unknown"),
                    title=j.get("title", "Unknown"),
                    location=j.get("location"),
                    url=j.get("url"),
                    jd_text=j.get("raw_snippet") or None,
                    country=j.get("search_country"),
                    search_country=j.get("search_country"),
                    search_title=j.get("search_title"),
                )
                db_count += 1
            print(f"  DB: {db_count} jobs registered")

            import json as _json
            _pdb.log_source_run(
                source="indeed",
                raw_count=jobs_found_raw,
                unique_count=len(all_jobs),
                db_registered=db_count,
                countries_json=_json.dumps(countries_seen),
                titles_json=_json.dumps(dict(sorted(titles_seen.items(), key=lambda x: -x[1])[:10])),
                duration_ms=0,
                errors=errors,
            )
            print(f"  source_runs: logged")
        except Exception as _e:
            print(f"  DB write failed (non-fatal): {_e}")
    # ─────────────────────────────────────────────────────────────────────────

    result.set_data(all_jobs)
    result.set_kpi({
        "searches_run": searches_run,
        "results_per_search": round(jobs_found_raw / max(1, searches_run), 2),
        "unique_jobs": len(all_jobs),
        "errors": errors,
    })


def main():
    """Entry point."""
    JOBS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(
        agent_name=AGENT_NAME,
        run_func=run_indeed_scanner,
        output_path=OUTPUT_FILE,
        ttl_hours=6,
        version="1.0.0"
    )


if __name__ == "__main__":
    main()
