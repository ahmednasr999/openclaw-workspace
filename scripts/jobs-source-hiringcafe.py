#!/usr/bin/env python3
"""
jobs-source-hiringcafe.py - HiringCafe job source adapter.

Uses tls_client to bypass bot detection and scrape hiring.cafe search results.
HiringCafe is a job aggregator with good startup/mid-market coverage.

Output: data/jobs-raw/hiringcafe.json
"""

import time
import sys
import os
import json
import re
from pathlib import Path

os.environ["PYTHONUNBUFFERED"] = "1"
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
build_source_output = jobs_source_common.build_source_output

AGENT_NAME = "jobs-source-hiringcafe"
OUTPUT_FILE = JOBS_RAW_DIR / "hiringcafe.json"
RATE_LIMIT_DELAY = 1.2
MAX_RESULTS_PER_SEARCH = 50

# HiringCafe location mapping for GCC
HIRINGCAFE_LOCATIONS = {
    "United Arab Emirates": ["Dubai, UAE", "Abu Dhabi, UAE"],
    "Saudi Arabia": ["Riyadh, Saudi Arabia", "Jeddah, Saudi Arabia"],
    "Qatar": ["Doha, Qatar"],
    "Bahrain": ["Manama, Bahrain"],
    "Kuwait": ["Kuwait City, Kuwait"],
    "Oman": ["Muscat, Oman"],
}

# Subset of titles to search (avoid overwhelming the source)
SEARCH_TITLES = [
    "Digital Transformation Director",
    "Chief Technology Officer",
    "Chief Operating Officer",
    "PMO Director",
    "Head of Transformation",
    "VP Technology",
    "Director of Engineering",
    "Head of IT",
    "Chief Information Officer",
    "Program Director",
    "IT Director",
    "Head of Strategy",
]


def fetch_hiringcafe_jobs(query, location, session):
    """Fetch jobs from HiringCafe search page using tls_client."""
    jobs = []

    try:
        # HiringCafe search URL pattern
        params = {
            "q": query,
            "l": location,
            "sort": "date",
        }
        search_url = "https://hiring.cafe/jobs"

        resp = session.get(
            search_url,
            params=params,
            timeout_seconds=15,
        )

        if resp.status_code != 200:
            print(f"  [hiringcafe] HTTP {resp.status_code} for {query} in {location}")
            return jobs

        html = resp.text

        # Try to extract job data from embedded JSON (common SPA pattern)
        # Look for __NEXT_DATA__ or similar embedded state
        next_data_match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL
        )
        if next_data_match:
            try:
                next_data = json.loads(next_data_match.group(1))
                # Navigate the Next.js data structure to find jobs
                page_props = next_data.get("props", {}).get("pageProps", {})
                job_listings = page_props.get("jobs", page_props.get("results", []))

                if isinstance(job_listings, list):
                    for item in job_listings[:MAX_RESULTS_PER_SEARCH]:
                        job = _parse_job_from_json(item)
                        if job:
                            jobs.append(job)
                    return jobs
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # Fallback: extract from Algolia-style API if embedded in page
        algolia_match = re.search(
            r'"hits"\s*:\s*(\[.*?\])\s*[,}]', html, re.DOTALL
        )
        if algolia_match:
            try:
                hits = json.loads(algolia_match.group(1))
                for item in hits[:MAX_RESULTS_PER_SEARCH]:
                    job = _parse_job_from_algolia(item)
                    if job:
                        jobs.append(job)
                return jobs
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: basic HTML extraction
        job_cards = re.findall(
            r'<a[^>]+href="(/jobs/[^"]+)"[^>]*>.*?</a>', html, re.DOTALL
        )
        # Extract structured data from job card patterns
        card_pattern = re.compile(
            r'href="(/jobs/[^"]+)".*?'
            r'class="[^"]*job-title[^"]*"[^>]*>([^<]+)<.*?'
            r'class="[^"]*company[^"]*"[^>]*>([^<]+)<.*?'
            r'class="[^"]*location[^"]*"[^>]*>([^<]+)<',
            re.DOTALL | re.IGNORECASE,
        )
        for match in card_pattern.finditer(html):
            url_path, title, company, loc = match.groups()
            jobs.append({
                "title": title.strip(),
                "company": company.strip(),
                "location": loc.strip(),
                "url": f"https://hiring.cafe{url_path}",
                "source_id": url_path.split("/")[-1] if "/" in url_path else url_path,
            })

    except Exception as e:
        print(f"  [hiringcafe] Error fetching {query} in {location}: {e}")

    return jobs


def _parse_job_from_json(item):
    """Parse a job from Next.js JSON data."""
    if not isinstance(item, dict):
        return None
    title = item.get("title") or item.get("jobTitle") or ""
    company = item.get("company") or item.get("companyName") or item.get("employer") or ""
    location = item.get("location") or item.get("city") or ""
    url = item.get("url") or item.get("jobUrl") or item.get("applyUrl") or ""
    job_id = item.get("id") or item.get("objectID") or ""
    description = item.get("description") or item.get("snippet") or ""
    posted = item.get("datePosted") or item.get("postedAt") or item.get("created") or ""

    if not title or not (company or url):
        return None

    if url and not url.startswith("http"):
        url = f"https://hiring.cafe{url}" if url.startswith("/") else f"https://hiring.cafe/jobs/{url}"

    return {
        "title": title.strip(),
        "company": (company if isinstance(company, str) else str(company)).strip(),
        "location": (location if isinstance(location, str) else str(location)).strip(),
        "url": url,
        "source_id": str(job_id),
        "description": description[:500] if description else "",
        "posted": posted,
    }


def _parse_job_from_algolia(item):
    """Parse a job from Algolia hits format."""
    if not isinstance(item, dict):
        return None
    return _parse_job_from_json(item)


def run(result):
    """Main run function."""
    try:
        import tls_client
    except ImportError:
        print("[hiringcafe] tls_client not installed, attempting pip install...")
        os.system(f"{sys.executable} -m pip install -q tls_client")
        import tls_client

    session = tls_client.Session(
        client_identifier="chrome_120",
        random_tls_extension_order=True,
    )
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://hiring.cafe/",
    }

    all_jobs = []
    seen_ids = set()
    searches_run = 0
    jobs_found_raw = 0

    # Priority countries only for speed
    search_countries = PRIORITY_COUNTRIES

    for country in search_countries:
        locations = HIRINGCAFE_LOCATIONS.get(country, [country])
        for location in locations[:2]:  # Max 2 locations per country
            for title in SEARCH_TITLES[:8]:  # Top 8 titles
                print(f"  [hiringcafe] Searching: '{title}' in {location}")
                searches_run += 1

                raw_jobs = fetch_hiringcafe_jobs(title, location, session)
                jobs_found_raw += len(raw_jobs)

                for job in raw_jobs:
                    job_id = job.get("source_id") or f"{job['title']}-{job['company']}"
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    std_job = standard_job_dict(
                        job_id=job_id,
                        source="hiringcafe",
                        title=job["title"],
                        company=job.get("company", "Unknown"),
                        location=job.get("location", location),
                        url=job.get("url", ""),
                        posted=job.get("posted", ""),
                        raw_snippet=job.get("description", ""),
                    )
                    all_jobs.append(std_job)

                time.sleep(RATE_LIMIT_DELAY)

    # Filter relevant jobs
    relevant_jobs = [j for j in all_jobs if j.get("relevant", False)]

    output = build_source_output(
        agent_name=AGENT_NAME,
        source="hiringcafe",
        jobs=relevant_jobs,
        searches_run=searches_run,
        jobs_found_raw=jobs_found_raw,
    )

    result.set_data(output)
    result.set_kpi({
        "searches_run": searches_run,
        "jobs_found_raw": jobs_found_raw,
        "jobs_relevant": len(relevant_jobs),
        "jobs_total": len(all_jobs),
    })

    print(f"[hiringcafe] Found {len(relevant_jobs)} relevant jobs from {jobs_found_raw} raw ({searches_run} searches)")


if __name__ == "__main__":
    agent_main(AGENT_NAME, run, OUTPUT_FILE, ttl_hours=12)
