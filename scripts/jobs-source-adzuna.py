#!/usr/bin/env python3
"""
jobs-source-adzuna.py — Adzuna job source adapter using official REST API.

Adzuna provides a free API (https://api.adzuna.com/v1/api) with GCC coverage:
  - ae: United Arab Emirates ✅
  - gb: United Kingdom (used as fallback; no direct SA/QA country)

Supported GCC-adjacent countries in Adzuna:
  ae (UAE), gb (fallback for other GCC via broad search)

API credentials: /root/.openclaw/workspace/config/adzuna.json
  {"app_id": "<your_app_id>", "app_key": "<your_app_key>"}

Output: data/jobs-raw/adzuna.json
"""

import time
import sys
import os
import json
import requests
from pathlib import Path
from urllib.parse import urlencode

# Ensure unbuffered output for cron
os.environ["PYTHONUNBUFFERED"] = "1"

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
load_json = agent_common.load_json
JOBS_RAW_DIR = agent_common.JOBS_RAW_DIR
WORKSPACE = agent_common.WORKSPACE

ALL_TITLES = jobs_source_common.ALL_TITLES
PRIORITY_COUNTRIES = jobs_source_common.PRIORITY_COUNTRIES
COUNTRY_SEARCH_TERMS = jobs_source_common.COUNTRY_SEARCH_TERMS
standard_job_dict = jobs_source_common.standard_job_dict

AGENT_NAME = "jobs-source-adzuna"
OUTPUT_FILE = JOBS_RAW_DIR / "adzuna.json"
CONFIG_FILE = WORKSPACE / "config" / "adzuna.json"

RESULTS_PER_PAGE = 50
RATE_LIMIT_DELAY = 1.0  # 1 req/sec (Adzuna free tier)
MAX_PAGES = 2            # Max pages per query (50 * 2 = 100 results max)

# Adzuna country codes that overlap with GCC region
# ae = UAE (direct support)
# gb = UK (used as broader "remote/international" fallback)
ADZUNA_COUNTRY_MAP = {
    "United Arab Emirates": {
        "country_code": "ae",
        "locations": ["Dubai", "Abu Dhabi", "UAE"],
    },
    # Saudi Arabia not directly supported — search via keyword in ae
    "Saudi Arabia": {
        "country_code": "ae",        # nearest supported country
        "locations": ["Saudi Arabia", "Riyadh", "Jeddah"],
    },
    "Qatar": {
        "country_code": "ae",        # nearest supported country
        "locations": ["Qatar", "Doha"],
    },
}

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


def load_adzuna_config() -> tuple[str, str]:
    """Load Adzuna API credentials from config file."""
    config = load_json(CONFIG_FILE, default={})
    app_id = config.get("app_id", "")
    app_key = config.get("app_key", "")
    return app_id, app_key


def search_adzuna(
    app_id: str,
    app_key: str,
    country_code: str,
    title: str,
    location: str,
    page: int = 1,
) -> list[dict]:
    """
    Call Adzuna jobs search API.
    Returns list of raw job result dicts.
    """
    url = f"{BASE_URL}/{country_code}/search/{page}"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": RESULTS_PER_PAGE,
        "what": title,
        "where": location,
        "content-type": "application/json",
        "max_days_old": 14,   # Last 14 days
        "sort_by": "date",
    }

    try:
        r = requests.get(url, params=params, timeout=15)

        if r.status_code == 401:
            print(f"  ERROR: Adzuna authentication failed. Check config/adzuna.json credentials.")
            return []
        if r.status_code == 429:
            print(f"  Rate limited — sleeping 5s")
            time.sleep(5)
            return []
        if r.status_code != 200:
            print(f"  HTTP {r.status_code} for {title} / {location}")
            return []

        data = r.json()
        return data.get("results", [])

    except requests.exceptions.Timeout:
        print(f"  Timeout: {title} / {location}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"  Request error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"  JSON decode error: {e}")
        return []


def parse_adzuna_job(raw: dict, source_country: str, source: str = "adzuna") -> dict:
    """Convert Adzuna API result dict to standardized job dict."""
    job_id = str(raw.get("id", ""))
    title = raw.get("title", "").strip()
    description = raw.get("description", "").strip()[:500]
    url = raw.get("redirect_url", "").strip()
    created = raw.get("created", "")[:10] if raw.get("created") else ""

    # Company
    company_obj = raw.get("company", {})
    company = company_obj.get("display_name", "Confidential").strip() if company_obj else "Confidential"

    # Location
    location_obj = raw.get("location", {})
    location = location_obj.get("display_name", source_country).strip() if location_obj else source_country

    # Salary (optional enrichment)
    salary_min = raw.get("salary_min")
    salary_max = raw.get("salary_max")

    job = standard_job_dict(
        job_id=job_id if job_id else str(abs(hash(url)))[:10],
        source=source,
        title=title,
        company=company,
        location=location,
        url=url,
        posted=created,
        raw_snippet=description,
    )

    # Enrich with salary if available
    if salary_min or salary_max:
        job["salary_min"] = salary_min
        job["salary_max"] = salary_max

    return job


def run_adzuna_scanner(result: AgentResult):
    """Main scanner logic for Adzuna source."""

    app_id, app_key = load_adzuna_config()

    if not app_id or not app_key:
        msg = (
            f"Adzuna credentials not configured. "
            f"Edit {CONFIG_FILE} and add your app_id and app_key from "
            f"https://developer.adzuna.com/admin/applications"
        )
        print(f"  WARNING: {msg}")
        result.set_error(msg)
        result.set_data([])
        result.set_kpi({"searches_run": 0, "unique_jobs": 0, "error": "no_credentials"})
        return

    if is_dry_run():
        total = sum(
            len(cfg["locations"]) * len(ALL_TITLES) * MAX_PAGES
            for cfg in ADZUNA_COUNTRY_MAP.values()
        )
        print(f"\n=== DRY RUN: Adzuna Search Plan ===")
        for country, cfg in ADZUNA_COUNTRY_MAP.items():
            print(f"  {country} [{cfg['country_code']}]: {len(cfg['locations'])} locations × {len(ALL_TITLES)} titles × {MAX_PAGES} pages")
        print(f"  Total requests planned: {total}")
        result.set_data([])
        result.set_kpi({"searches_planned": total})
        return

    # Build search plan
    searches = []
    for country, cfg in ADZUNA_COUNTRY_MAP.items():
        country_code = cfg["country_code"]
        for location in cfg["locations"]:
            for title in ALL_TITLES:
                for page in range(1, MAX_PAGES + 1):
                    searches.append((country_code, title, location, country, page))

    print(f"Search plan: {len(searches)} queries (Adzuna API)")

    all_jobs = []
    seen_urls = set()
    searches_run = 0
    jobs_raw = 0
    errors = 0

    for country_code, title, location, country, page in searches:
        searches_run += 1

        raw_jobs = search_adzuna(app_id, app_key, country_code, title, location, page)

        if not raw_jobs:
            errors += 1
        else:
            jobs_raw += len(raw_jobs)

        for raw in raw_jobs:
            job = parse_adzuna_job(raw, source_country=country)
            if not job["url"] or job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])
            all_jobs.append(job)

        if searches_run % 20 == 0:
            print(
                f"  Progress: {searches_run}/{len(searches)} "
                f"| raw {jobs_raw} | unique {len(all_jobs)}"
            )

        time.sleep(RATE_LIMIT_DELAY)

    print(f"\nCompleted: {searches_run} searches, {jobs_raw} raw, {len(all_jobs)} unique")

    # DB write (dual-write, non-blocking)
    if _pdb:
        try:
            db_count = 0
            for j in all_jobs:
                _pdb.register_job(
                    source="adzuna",
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

    result.set_data(all_jobs)
    result.set_kpi({
        "searches_run": searches_run,
        "results_per_search": round(jobs_raw / max(1, searches_run), 2),
        "unique_jobs": len(all_jobs),
        "errors": errors,
        "countries_searched": list(ADZUNA_COUNTRY_MAP.keys()),
        "api_version": "v1",
    })


if __name__ == "__main__":
    JOBS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(AGENT_NAME, run_adzuna_scanner, OUTPUT_FILE)
