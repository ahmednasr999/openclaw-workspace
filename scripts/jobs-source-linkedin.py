#!/usr/bin/env python3
"""
jobs-source-linkedin.py — LinkedIn job source adapter using public job search.

Uses LinkedIn's public job search page (no API, no login required).
Much more reliable than JobSpy's LinkedIn scraper from VPS IPs.

Output: data/jobs-raw/linkedin.json
"""

import time
import sys
import os
import requests
from pathlib import Path

# Ensure unbuffered output for cron
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

AGENT_NAME = "jobs-source-linkedin"
OUTPUT_FILE = JOBS_RAW_DIR / "linkedin.json"
RESULTS_PER_SEARCH = 25
RATE_LIMIT_DELAY = 1.5  # Seconds between requests

# Location terms for LinkedIn's public search
LINKEDIN_LOCATIONS = {
    "Saudi Arabia": ["Saudi Arabia", "Riyadh", "Jeddah"],
    "United Arab Emirates": ["Dubai", "Abu Dhabi"],
    "Qatar": ["Qatar"],
    "Bahrain": ["Bahrain"],
    "Kuwait": ["Kuwait"],
    "Oman": ["Oman"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def search_linkedin_public(title: str, location: str) -> list[dict]:
    """Search LinkedIn public job listings. Returns list of job dicts."""
    try:
        from bs4 import BeautifulSoup
        
        url = "https://www.linkedin.com/jobs/search/"
        params = {
            "keywords": title,
            "location": location,
            "position": 1,
            "pageNum": 0,
            "f_TPR": "r604800",  # Last 7 days only
        }
        
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        
        if r.status_code != 200:
            return []
        
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("div", class_="base-card")
        
        if not cards:
            return []
        
        jobs = []
        for card in cards:
            title_el = card.find("h3", class_="base-search-card__title")
            company_el = card.find("h4", class_="base-search-card__subtitle")
            location_el = card.find("span", class_="job-search-card__location")
            link_el = card.find("a", class_="base-card__full-link")
            time_el = card.find("time")
            
            job_title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else "Confidential"
            loc = location_el.get_text(strip=True) if location_el else location
            job_url = link_el["href"].split("?")[0] if link_el and link_el.get("href") else ""
            posted = time_el.get("datetime", "")[:10] if time_el else ""
            
            if not job_url or not job_title:
                continue
            
            # Extract job ID from URL
            job_id = job_url.rstrip("/").split("-")[-1] if job_url else ""
            
            job = standard_job_dict(
                job_id=f"li-{job_id}" if job_id else f"li-{abs(hash(job_url))}",
                source="linkedin",
                title=job_title,
                company=company,
                location=loc,
                url=job_url,
                posted=posted,
                raw_snippet="",
            )
            jobs.append(job)
        
        return jobs
    
    except Exception as e:
        print(f"  Search error ({location}): {e}")
        return []


def run_linkedin_scanner(result: AgentResult):
    """Main scanner logic using public LinkedIn search."""
    
    if is_dry_run():
        result.set_data([])
        return
    
    # Build search plan: top titles x locations
    TOP_TITLES = ALL_TITLES  # All 27 titles
    
    searches = []
    for country in PRIORITY_COUNTRIES:
        locations = LINKEDIN_LOCATIONS.get(country, [country])
        for loc in locations:
            for title in TOP_TITLES:
                searches.append((title, loc, country))
    
    print(f"Search plan: {len(searches)} queries (LinkedIn public)")
    
    all_jobs = []
    seen_urls = set()
    searches_run = 0
    jobs_raw = 0
    errors = 0
    consecutive_errors = 0
    blocked = False
    
    for title, location, country in searches:
        if blocked:
            break
        
        searches_run += 1
        
        jobs = search_linkedin_public(title, location)
        
        if not jobs:
            errors += 1
            consecutive_errors += 1
            if consecutive_errors >= 20 and jobs_raw == 0:
                blocked = True
                print("  LinkedIn appears fully blocked after 20 consecutive empty results")
        else:
            consecutive_errors = 0
            jobs_raw += len(jobs)
        
        for j in jobs:
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_jobs.append(j)
        
        if searches_run % 15 == 0:
            print(f"  Progress: {searches_run}/{len(searches)} | raw {jobs_raw} | unique {len(all_jobs)}")
        
        time.sleep(RATE_LIMIT_DELAY)
    
    print(f"\nCompleted: {searches_run} searches, {jobs_raw} raw, {len(all_jobs)} unique")
    
    result.set_data(all_jobs)
    result.set_kpi({
        "searches_run": searches_run,
        "results_per_search": round(jobs_raw / max(1, searches_run), 2),
        "unique_jobs": len(all_jobs),
        "errors": errors,
        "blocked": blocked,
        "method": "public-html-scrape",
    })


if __name__ == "__main__":
    JOBS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(AGENT_NAME, run_linkedin_scanner, OUTPUT_FILE)
