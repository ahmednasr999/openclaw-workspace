#!/usr/bin/env python3
"""Shadow-only GCC executive discovery through LinkedIn's public guest endpoint.

This lane measures incremental coverage against JobZoom's raw LinkedIn output.
It does not write to JobZoom, score jobs, generate CVs, or change application state.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup


SEARCH_ENDPOINT = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/124 Safari/537.36"
)
LOCATIONS = [
    "United Arab Emirates",
    "Saudi Arabia",
    "Qatar",
    "Oman",
    "Bahrain",
    "Kuwait",
]
QUERIES = [
    "digital transformation",
    "PMO transformation",
    "vice president operations",
    "head of operations",
    "chief operating officer",
    "strategy transformation",
    "director program management",
    "payments fintech",
    "healthcare transformation",
    "ecommerce logistics director",
]
SENIOR_RE = re.compile(
    r"\b(chief|ceo|coo|vice president|vp|head|director|general manager|"
    r"country manager|portfolio lead|transformation lead|program(?:me)? lead|"
    r"pmo lead|operational planning)\b",
    re.I,
)
EXCLUDE_RE = re.compile(
    r"\b(assistant|associate|intern|specialist|engineer|developer|analyst|"
    r"coordinator|sales director|account director|art director|medical director|"
    r"nursing director|finance director|hr director|human resources|legal director|"
    r"marketing director|real estate|construction director|project director|"
    r"design director)\b",
    re.I,
)
JOB_ID_RE = re.compile(r"(?:jobPosting:|/jobs/view/(?:[^/?#]*-)?)(\d{8,12})")
JOBZOOM_TARGET_TITLES = [
    "Chief Digital Officer",
    "VP Digital Transformation",
    "Head of Digital Transformation",
    "Director Digital Transformation",
    "SVP Digital Strategy",
    "Chief Operating Officer",
    "VP Operations",
    "Head of Operations",
    "Director Operations Excellence",
    "VP Revenue Operations",
    "Head of PMO",
    "VP PMO",
    "Director PMO",
    "Head of Program Management",
    "Director Portfolio Management",
    "VP HealthTech",
    "Head of Healthcare IT",
    "VP FinTech Operations",
    "Director E-Commerce",
    "Head of Product & Technology",
    "Senior Program Manager",
    "Senior Project Manager",
    "PMO Manager",
    "Program Director",
    "Transformation Manager",
]
JOBZOOM_PMO_KEYWORDS = [
    "program manager",
    "project manager",
    "pmo",
    "program director",
    "transformation manager",
    "operations manager",
    "strategy manager",
    "delivery manager",
    "implementation manager",
    "product manager",
    "portfolio manager",
    "chief of staff",
    "business manager",
    "digital transformation",
    "change manager",
    "engagement manager",
]
JOBZOOM_APPROVED_PASS1_PATTERNS = [
    "corporate program management",
    "operations excellence",
    "customer experience transformation",
    "plm transformation",
    "transformation & development",
    "service delivery director",
    "chief technology officer",
    "chief product & technology officer",
    "cpto",
]
EXECUTIVE_TITLE_RE = re.compile(
    r"\b(chief|ceo|coo|vice president|vp|svp|evp|head|director|general manager|"
    r"country manager)\b",
    re.I,
)
EXECUTIVE_DOMAIN_TITLE_RE = re.compile(
    r"\b(ai|artificial intelligence|innovation|technology|digital|transformation|"
    r"strategy|operations?|operational|performance|program(?:me)?|portfolio|pmo|"
    r"enablement|excellence)\b",
    re.I,
)
EXECUTIVE_RESCUE_EXCLUDE_RE = re.compile(
    r"\b(finance|financial institutions|sales|marketing|revenue|commercial officer|"
    r"legal|human resources|hr|medical|nursing|construction|housekeeping|front services|"
    r"supply chain|m&a|quality control|project control|design unit|planning and scheduling)\b",
    re.I,
)


class StartRateLimiter:
    """Keep request starts spaced across all workers."""

    def __init__(self, minimum_interval: float) -> None:
        self.minimum_interval = max(0.0, minimum_interval)
        self._lock = threading.Lock()
        self._next_start = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = max(0.0, self._next_start - now)
            self._next_start = max(now, self._next_start) + self.minimum_interval
        if delay:
            time.sleep(delay)


def extract_job_id(value: object) -> str:
    text = str(value or "")
    match = re.search(r"(?:li-)?(\d{8,12})(?:\D|$)", text)
    return match.group(1) if match else ""


def parse_cards(html: str, query: str, fallback_location: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict] = []
    for card in soup.select("li"):
        entity = card.select_one('[data-entity-urn*="jobPosting:"]')
        match = (
            re.search(r"jobPosting:(\d+)", entity.get("data-entity-urn", ""))
            if entity
            else None
        )
        if not match:
            continue
        job_id = match.group(1)
        title = card.select_one("h3")
        company = card.select_one("h4")
        location = card.select_one(".job-search-card__location")
        posted = card.select_one("time")
        link = card.select_one('a[href*="/jobs/view/"]')
        jobs.append(
            {
                "id": job_id,
                "title": title.get_text(" ", strip=True) if title else "",
                "company": company.get_text(" ", strip=True) if company else "",
                "location": (
                    location.get_text(" ", strip=True) if location else fallback_location
                ),
                "posted": posted.get("datetime", "") if posted else "",
                "link": (
                    link.get("href", "").split("?")[0]
                    if link
                    else f"https://www.linkedin.com/jobs/view/{job_id}"
                ),
                "matched_queries": [query],
            }
        )
    return jobs


def fetch_search(
    query: str,
    location: str,
    start: int,
    hours: int,
    timeout: int,
    retries: int,
    limiter: StartRateLimiter,
) -> tuple[list[dict], dict]:
    params = {
        "keywords": query,
        "location": location,
        "f_TPR": f"r{hours * 3600}",
        "start": str(start),
    }
    url = SEARCH_ENDPOINT + "?" + urllib.parse.urlencode(params)
    last_error = ""
    for attempt in range(retries + 1):
        limiter.wait()
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                html = response.read().decode("utf-8", "replace")
            jobs = parse_cards(html, query, location)
            return jobs, {
                "query": query,
                "location": location,
                "start": start,
                "status": 200,
                "cards": len(jobs),
                "attempts": attempt + 1,
                "error": None,
            }
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason}"
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            if exc.code != 429 or attempt >= retries:
                break
            try:
                wait_seconds = float(retry_after) if retry_after else 0.0
            except (TypeError, ValueError):
                wait_seconds = 0.0
            time.sleep(max(wait_seconds, (2**attempt) * 2 + random.random()))
        except (OSError, TimeoutError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt >= retries:
                break
            time.sleep((2**attempt) * 2 + random.random())
    return [], {
        "query": query,
        "location": location,
        "start": start,
        "status": None,
        "cards": 0,
        "attempts": retries + 1,
        "error": last_error or "unknown error",
    }


def dedupe_jobs(jobs: Iterable[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for job in jobs:
        job_id = extract_job_id(job.get("id") or job.get("link"))
        if not job_id:
            continue
        if job_id not in by_id:
            normalized = dict(job)
            normalized["id"] = job_id
            normalized["matched_queries"] = list(job.get("matched_queries") or [])
            by_id[job_id] = normalized
            continue
        existing = by_id[job_id]
        for query in job.get("matched_queries") or []:
            if query not in existing["matched_queries"]:
                existing["matched_queries"].append(query)
    return list(by_id.values())


def load_jobzoom_jobs(path: Path | None) -> dict[str, dict]:
    if not path or not path.exists():
        return {}
    payload = json.loads(path.read_text(errors="replace"))
    rows = payload.get("jobs", []) if isinstance(payload, dict) else payload
    jobs: dict[str, dict] = {}
    for row in rows if isinstance(rows, list) else []:
        for key in ("linkedin_id", "id", "job_id", "url", "job_url"):
            job_id = extract_job_id(row.get(key)) if isinstance(row, dict) else ""
            if job_id:
                jobs.setdefault(job_id, row)
                break
    return jobs


def load_offline_jobs(path: Path) -> list[dict]:
    payload = json.loads(path.read_text())
    rows = list(payload.get("fresh", [])) + list(payload.get("known_reappeared", []))
    jobs = []
    for row in rows:
        item = dict(row)
        item["matched_queries"] = [row.get("query", "offline-artifact")]
        jobs.append(item)
    return jobs


def jobzoom_pass1_title_match(title: str) -> bool:
    """Mirror the title portion of JobZoom's current Pass 1 gate."""
    normalized = (title or "").lower()
    return (
        any(keyword in normalized for keyword in JOBZOOM_PMO_KEYWORDS)
        or any(
            target.lower() in normalized or normalized in target.lower()
            for target in JOBZOOM_TARGET_TITLES
        )
        or any(
            re.search(r"\b" + re.escape(pattern) + r"\b", normalized)
            for pattern in JOBZOOM_APPROVED_PASS1_PATTERNS
        )
    )


def controlled_rescue_candidates(jobzoom_jobs: dict[str, dict]) -> list[dict]:
    """Return a bounded shadow set that the current Pass 1 title gate rejects."""
    candidates = []
    for job_id, job in jobzoom_jobs.items():
        title = job.get("title", "")
        if jobzoom_pass1_title_match(title):
            continue
        if not EXECUTIVE_TITLE_RE.search(title):
            continue
        if not EXECUTIVE_DOMAIN_TITLE_RE.search(title):
            continue
        if EXECUTIVE_RESCUE_EXCLUDE_RE.search(title):
            continue
        candidates.append(
            {
                "id": job_id,
                "title": title,
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "search_title": job.get("search_title", ""),
                "reason": "controlled_executive_domain_rescue",
            }
        )
    return candidates


def build_report(
    jobs: list[dict], jobzoom_jobs: dict[str, dict], searches: list[dict]
) -> dict:
    unique = dedupe_jobs(jobs)
    senior = [
        job
        for job in unique
        if SENIOR_RE.search(job.get("title", ""))
        and not EXCLUDE_RE.search(job.get("title", ""))
    ]
    novel = [job for job in senior if job["id"] not in jobzoom_jobs]
    pass1_gaps = []
    for job in senior:
        raw_job = jobzoom_jobs.get(job["id"])
        if raw_job and not jobzoom_pass1_title_match(raw_job.get("title", "")):
            rescued = dict(job)
            rescued["jobzoom_search_title"] = raw_job.get("search_title", "")
            rescued["gap_reason"] = "discovered_in_jobzoom_raw_but_rejected_by_title_pass1"
            pass1_gaps.append(rescued)
    rescue = controlled_rescue_candidates(jobzoom_jobs)
    return {
        "meta": {
            "generated_at": datetime.now().astimezone().isoformat(),
            "mode": "shadow-only",
            "writes_to_jobzoom": False,
            "search_endpoint": SEARCH_ENDPOINT,
        },
        "counts": {
            "searches": len(searches),
            "successful_searches": sum(not row.get("error") for row in searches),
            "failed_searches": sum(bool(row.get("error")) for row in searches),
            "unique_jobs": len(unique),
            "senior_jobs": len(senior),
            "jobzoom_reference_ids": len(jobzoom_jobs),
            "novel_vs_jobzoom_raw": len(novel),
            "jobzoom_pass1_gaps": len(pass1_gaps),
            "controlled_rescue_candidates": len(rescue),
        },
        "errors": [row for row in searches if row.get("error")],
        "novel_vs_jobzoom_raw": novel,
        "jobzoom_pass1_gaps": pass1_gaps,
        "controlled_rescue_candidates": rescue,
        "senior_jobs": senior,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--jobzoom-raw",
        type=Path,
        default=Path("/root/.openclaw/workspace-jobzoom/data/jobs-raw/linkedin.json"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--offline-hermes-artifact", type=Path)
    parser.add_argument("--location", action="append", choices=LOCATIONS)
    parser.add_argument("--query", action="append")
    parser.add_argument("--hours", type=int, default=48)
    parser.add_argument("--start", type=int, action="append")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--minimum-request-interval", type=float, default=1.5)
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    jobzoom_jobs = load_jobzoom_jobs(args.jobzoom_raw)
    searches: list[dict] = []
    jobs: list[dict] = []
    if args.offline_hermes_artifact:
        jobs = load_offline_jobs(args.offline_hermes_artifact)
    else:
        locations = args.location or LOCATIONS
        queries = args.query or QUERIES
        starts = args.start or [0]
        plan = [(query, location, start) for location in locations for query in queries for start in starts]
        limiter = StartRateLimiter(args.minimum_request_interval)
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as executor:
            futures = [
                executor.submit(
                    fetch_search,
                    query,
                    location,
                    start,
                    args.hours,
                    args.timeout,
                    args.retries,
                    limiter,
                )
                for query, location, start in plan
            ]
            for future in as_completed(futures):
                found, search = future.result()
                jobs.extend(found)
                searches.append(search)

    report = build_report(jobs, jobzoom_jobs, searches)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")
        print(args.output)
    else:
        print(rendered)
    return 0 if report["counts"]["failed_searches"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
