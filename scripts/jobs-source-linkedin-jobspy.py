#!/usr/bin/env python3
"""
jobs-source-linkedin-jobspy.py — LinkedIn source via JobSpy (public API, no auth needed).

*** NON-NEGOTIABLE: This is the ONLY approved LinkedIn scraping method. ***
Uses JobSpy with linkedin_fetch_description=True which hits LinkedIn's public
/jobs/view/ endpoint — works from any VPS without login, cookies, or proxies.

DO NOT replace or bypass this with:
- requests + BeautifulSoup scraping of linkedin.com/jobs/search/
- Selenium / Playwright LinkedIn automation
- Composio LinkedIn tools for job search
- Any method requiring authentication or cookies

Why this works: JobSpy calls LinkedIn's public job API (/jobs/view/) that returns
HTML for non-authenticated users. No login needed. Full JDs included.
Reference: https://github.com/DaKheera47/job-ops

Output: data/jobs-raw/linkedin.json  (same file as old linkedin source)
"""

import sys
import os
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ["PYTHONUNBUFFERED"] = "1"

try:
    sys.path.insert(0, os.path.dirname(__file__))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

from _imports import agent_common, jobs_source_common

AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
JOBS_RAW_DIR = agent_common.JOBS_RAW_DIR

ALL_TITLES = jobs_source_common.ALL_TITLES
GCC_COUNTRIES = jobs_source_common.GCC_COUNTRIES
standard_job_dict = jobs_source_common.standard_job_dict

AGENT_NAME = "jobs-source-linkedin-jobspy"
OUTPUT_FILE = JOBS_RAW_DIR / "linkedin.json"

# JobSpy settings
RESULTS_PER_SEARCH = 50
HOURS_OLD = 720  # 30 days (still accepting apps, just age-rank lower)
RATE_LIMIT_DELAY = 2.0  # seconds between searches (be respectful)

# Priority: top titles × all 6 GCC countries
PRIORITY_TITLES = [
    # Core targets
    "PMO Director",
    "Head of PMO",
    "Senior PMO Manager",
    "Head of Business Excellence",
    # Digital transformation
    "Chief Digital Officer",
    "VP Digital Transformation",
    "Director Digital Transformation",
    "Head of Digital Transformation",
    "Transformation Director",
    # Technology leadership
    "Chief Technology Officer",
    "Chief Information Officer",
    "Head of Technology",
    # Operations & strategy
    "Chief Operating Officer",
    "Chief Strategy Officer",
    "VP Operations",
    "VP Technology",
    "Director of Strategy",
    "Director of Program Management",
    "Program Director",
    # Innovation
    "Director of Innovation",
    "Head of Transformation",
    # Added 2026-04-05 — critical missing roles
    "Delivery Director",
    "Programme Manager",
    "Project Director",
    "Head of Delivery",
    "Portfolio Director",
    "EPMO Director",
]

# Cross-functional keyword searches — catches non-standard titles
# (e.g. "Programme Delivery Director", "Associate Director - Transformation")
KEYWORD_SEARCHES = [
    "PMO",                          # all PMO roles regardless of title
    "Digital Transformation",        # all DT roles regardless of title
    "Portfolio Director OR PMO",     # combo for LinkedIn search
    "Transformation Director",       # variant of transformation roles
    "Head of Strategy",              # strategic leadership
    "Operations Director",           # broad ops leadership
]

# Location map: country → search location string for JobSpy
LOCATION_MAP = {
    "United Arab Emirates": "Dubai, UAE",
    "Saudi Arabia": "Riyadh, Saudi Arabia",
    "Qatar": "Doha, Qatar",
    "Bahrain": "Manama, Bahrain",
    "Kuwait": "Kuwait City, Kuwait",
    "Oman": "Muscat, Oman",
}


def scrape_linkedin_jobspy(title: str, location: str, country: str = "", dry_run: bool = False) -> list[dict]:
    """Scrape LinkedIn via JobSpy for a single title+location combo."""
    try:
        from jobspy import scrape_jobs
        import pandas as pd

        if dry_run:
            return []

        jobs_df = scrape_jobs(
            site_name=["linkedin"],
            search_term=title,
            location=location,
            results_wanted=RESULTS_PER_SEARCH,
            hours_old=HOURS_OLD,
            linkedin_fetch_description=True,
            description_format="markdown",
            verbose=0,
        )

        if jobs_df is None or jobs_df.empty:
            return []

        results = []
        for _, row in jobs_df.iterrows():
            job_id = str(row.get("id", "")) or str(row.get("job_url", ""))
            url = str(row.get("job_url", "")) or str(row.get("job_url_direct", ""))
            description = str(row.get("description", "")) or ""
            salary_raw = ""
            if row.get("min_amount") and row.get("max_amount"):
                currency = row.get("currency", "")
                interval = row.get("interval", "")
                salary_raw = f"{currency} {row['min_amount']}-{row['max_amount']} {interval}".strip()

            job = standard_job_dict(
                job_id=f"li-{job_id}" if job_id and not job_id.startswith("li-") else job_id,
                title=str(row.get("title", "")),
                company=str(row.get("company", "")),
                location=str(row.get("location", "")),
                url=url,
                source="linkedin_jobspy",
                raw_snippet=description[:300] if description else "",
                posted=str(row.get("date_posted", "")) if pd.notna(row.get("date_posted")) else "",
            )
            # Attach extra fields that merge step can use
            job["search_country"] = country  # critical for country extraction in merge step
            if description:
                job["jd_text"] = description
            if salary_raw:
                job["salary"] = salary_raw
            results.append(job)

        return results

    except ImportError:
        print("  ERROR: jobspy not installed — run: pip install jobspy")
        return []
    except Exception as e:
        print(f"  Error scraping '{title}' @ {location}: {e}")
        return []


def run_linkedin_jobspy(result: AgentResult):
    """Main scraping logic."""
    dry_run = is_dry_run()
    all_jobs = {}
    total_searches = 0
    failed_searches = 0

    search_pairs = [
        (title, loc_str, country_name, "title")
        for country_name, loc_str in LOCATION_MAP.items()
        for title in PRIORITY_TITLES
    ]

    # Add keyword searches (broader net — catches non-standard titles)
    KEYWORD_PAIRS = [
        (kw, loc_str, country_name, "keyword")
        for country_name, loc_str in LOCATION_MAP.items()
        for kw in KEYWORD_SEARCHES
    ]

    all_searches = search_pairs + KEYWORD_PAIRS

    print(f"LinkedIn JobSpy: {len(all_searches)} searches ({len(search_pairs)} title + {len(KEYWORD_PAIRS)} keyword across {len(LOCATION_MAP)} countries)")
    print(f"linkedin_fetch_description=True — full JDs via public API")

    if dry_run:
        print(f"\nDRY RUN: Would run {len(all_searches)} searches")
        for title, loc, ctry, kind in all_searches[:5]:
            print(f"  → [{kind}] '{title}' @ {loc} [{ctry}]")
        print(f"  ... and {len(all_searches)-5} more")
        result.set_data([])
        result.set_kpi({"searches_planned": len(search_pairs), "dry_run": True})
        return

    for i, (title, location, country_name, kind) in enumerate(all_searches, 1):
        print(f"  [{i}/{len(all_searches)}] [{kind}] '{title}' @ {location}...", end=" ", flush=True)
        jobs = scrape_linkedin_jobspy(title, location, country_name)

        new_count = 0
        for job in jobs:
            jid = job.get("id", "") or job.get("url", "")
            if jid and jid not in all_jobs:
                all_jobs[jid] = job
                new_count += 1

        print(f"{len(jobs)} found, {new_count} new (total: {len(all_jobs)})")
        total_searches += 1

        if i < len(search_pairs):
            time.sleep(RATE_LIMIT_DELAY)

    jobs_list = list(all_jobs.values())
    print(f"\nTotal unique LinkedIn jobs: {len(jobs_list)} from {total_searches} searches")

    # Write output
    JOBS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "jobs": jobs_list,
        "meta": {
            "source": "linkedin",
            "searches": total_searches,
            "failed": failed_searches,
            "titles": len(PRIORITY_TITLES),
            "countries": len(LOCATION_MAP),
        }
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    result.set_data(jobs_list)
    result.set_kpi({
        "total_jobs": len(jobs_list),
        "searches": total_searches,
        "failed": failed_searches,
        "output_file": str(OUTPUT_FILE),
    })


if __name__ == "__main__":
    agent_main(AGENT_NAME, run_linkedin_jobspy, OUTPUT_FILE)
