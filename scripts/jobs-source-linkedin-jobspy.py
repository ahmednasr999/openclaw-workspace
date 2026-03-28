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
RESULTS_PER_SEARCH = 20
HOURS_OLD = 168  # 7 days
RATE_LIMIT_DELAY = 2.0  # seconds between searches (be respectful)

# Priority: top titles × all 6 GCC countries
PRIORITY_TITLES = [
    "Chief Digital Officer",
    "VP Digital Transformation",
    "Director Digital Transformation",
    "Head of Digital Transformation",
    "Chief Technology Officer",
    "Chief Information Officer",
    "Head of Technology",
    "PMO Director",
    "Head of PMO",
    "Head of Transformation",
    "VP Technology",
    "Chief Operating Officer",
    "Chief Strategy Officer",
    "Director of Innovation",
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


def scrape_linkedin_jobspy(title: str, location: str, dry_run: bool = False) -> list[dict]:
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
                id=f"li-{job_id}" if job_id and not job_id.startswith("li-") else job_id,
                title=str(row.get("title", "")),
                company=str(row.get("company", "")),
                location=str(row.get("location", "")),
                url=url,
                source="linkedin_jobspy",
                snippet=description[:300] if description else "",
                jd_text=description,
                posted=str(row.get("date_posted", "")) if row.get("date_posted") else "",
                salary=salary_raw,
            )
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
        (title, loc_str)
        for title in PRIORITY_TITLES
        for loc_str in LOCATION_MAP.values()
    ]

    print(f"LinkedIn JobSpy: {len(search_pairs)} searches ({len(PRIORITY_TITLES)} titles × {len(LOCATION_MAP)} countries)")
    print(f"linkedin_fetch_description=True — full JDs via public API")

    if dry_run:
        print(f"\nDRY RUN: Would run {len(search_pairs)} JobSpy searches")
        for title, loc in search_pairs[:5]:
            print(f"  → '{title}' @ {loc}")
        print(f"  ... and {len(search_pairs)-5} more")
        result.set_data([])
        result.set_kpi({"searches_planned": len(search_pairs), "dry_run": True})
        return

    for i, (title, location) in enumerate(search_pairs, 1):
        print(f"  [{i}/{len(search_pairs)}] '{title}' @ {location}...", end=" ", flush=True)
        jobs = scrape_linkedin_jobspy(title, location)

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
        "source": "linkedin_jobspy",
        "total": len(jobs_list),
        "jobs": jobs_list,
        "meta": {
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
    agent_main(AGENT_NAME, run_linkedin_jobspy)
