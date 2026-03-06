#!/usr/bin/env python3
"""
LinkedIn Job Scout (Camofox Edition)
Searches LinkedIn for executive roles across GCC using camofox anti-detection browser.
Usage: python3 linkedin-scout-camofox.py [--output FILE]
Output: Markdown file with discovered jobs.
"""

import json
import subprocess
import time
import re
import logging
import argparse
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("/root/.openclaw/workspace/memory")
DEFAULT_OUTPUT = OUTPUT_DIR / "linkedin-job-scout.md"
LOG_FILE = Path("/root/.openclaw/workspace/logs/linkedin-scout.log")
COOKIES_FILE = Path("/root/.openclaw/workspace/config/linkedin-cookies.json")

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)

# 10 keywords x 6 GCC countries = 60 searches
KEYWORDS = [
    "PMO Director",
    "VP Digital Transformation",
    "VP Technology",
    "CTO",
    "Head of AI",
    "Director Digital Transformation",
    "Chief Digital Officer",
    "Head of Product",
    "Senior Director Technology",
    "VP HealthTech",
]

LOCATIONS = [
    "United Arab Emirates",
    "Saudi Arabia",
    "Qatar",
    "Bahrain",
    "Kuwait",
    "Oman",
]


def run_camofox(args: list, timeout: int = 30) -> tuple:
    """Run camofox-browser CLI command."""
    cmd = ["camofox-browser", "--format", "json"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 1


def ensure_server():
    """Ensure camofox server is running."""
    out, _, rc = run_camofox(["health"], timeout=5)
    if rc != 0:
        logging.warning("Camofox server not responding, attempting start...")
        subprocess.run(["systemctl", "start", "camofox"], timeout=10)
        time.sleep(3)
        out, _, rc = run_camofox(["health"], timeout=5)
        if rc != 0:
            raise RuntimeError("Cannot start camofox server")
    logging.info("Camofox server healthy")


def search_jobs(keyword: str, location: str, tab_id: str) -> list:
    """Search LinkedIn for jobs and extract results."""
    kw_enc = keyword.replace(" ", "%20")
    loc_enc = location.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?keywords={kw_enc}&location={loc_enc}&f_TPR=r604800&f_E=1"

    # Navigate to search
    out, err, rc = run_camofox(["navigate", url, tab_id], timeout=30)
    if rc != 0:
        logging.error(f"Navigate failed for {keyword}/{location}: {err}")
        return []

    # Wait for results to load
    time.sleep(3)

    # Extract job listings via JavaScript
    extract_js = """
    (() => {
        const jobs = [];
        // Try multiple selector patterns
        const cards = document.querySelectorAll(
            '.job-card-container, .jobs-search-results__list-item, ' +
            '.scaffold-layout__list-item, [data-occludable-job-id]'
        );
        cards.forEach(card => {
            const titleEl = card.querySelector(
                '.job-card-list__title, .job-card-container__link, ' +
                'a[class*="job-card"]'
            );
            const companyEl = card.querySelector(
                '.job-card-container__primary-description, ' +
                '.artdeco-entity-lockup__subtitle, ' +
                '.job-card-container__company-name'
            );
            const locationEl = card.querySelector(
                '.job-card-container__metadata-item, ' +
                '.artdeco-entity-lockup__caption, ' +
                '.job-card-container__metadata-wrapper'
            );
            const linkEl = card.querySelector('a[href*="/jobs/view/"]');

            const title = titleEl ? titleEl.innerText.trim() : null;
            const company = companyEl ? companyEl.innerText.trim() : null;
            const loc = locationEl ? locationEl.innerText.trim() : null;
            const link = linkEl ? linkEl.href : null;
            const jobId = linkEl ? linkEl.href.match(/\\/jobs\\/view\\/(\\d+)/)?.[1] : null;

            if (title && title.length > 3) {
                jobs.push({ title, company, location: loc, link, jobId });
            }
        });
        return JSON.stringify(jobs);
    })()
    """

    out, err, rc = run_camofox(["eval", extract_js, tab_id], timeout=15)

    if rc == 0 and out:
        try:
            eval_result = json.loads(out)
            result_str = eval_result.get("result", out) if isinstance(eval_result, dict) else out
            if isinstance(result_str, str):
                jobs = json.loads(result_str)
            else:
                jobs = result_str
            if isinstance(jobs, list):
                logging.info(f"Found {len(jobs)} jobs for '{keyword}' in '{location}'")
                return jobs[:20]
        except (json.JSONDecodeError, TypeError) as e:
            logging.warning(f"JSON parse error for {keyword}/{location}: {e}")

    # Fallback: use snapshot to get accessible tree
    out, err, rc = run_camofox(["snapshot", tab_id], timeout=15)
    if rc == 0 and out:
        # Extract job titles from snapshot text
        titles = re.findall(r'link "([^"]+)".*?/jobs/view/', out)
        jobs = [{"title": t, "company": None, "location": None, "link": None, "jobId": None} for t in titles[:20]]
        logging.info(f"Snapshot fallback: {len(jobs)} jobs for '{keyword}' in '{location}'")
        return jobs

    logging.warning(f"No results for '{keyword}' in '{location}'")
    return []


def generate_report(all_jobs: dict, stats: dict) -> str:
    """Generate markdown report."""
    lines = [
        f"# LinkedIn Job Scout (Camofox) - {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"> Searched {stats['total_searches']} combinations | "
        f"Found {stats['total_jobs']} unique jobs | "
        f"Completed {stats['completed']}/{stats['total_searches']} | "
        f"Duration: {stats['duration_sec']:.0f}s",
        "",
    ]

    # Deduplicate by jobId
    seen = set()
    unique_jobs = []
    for (kw, loc), jobs in all_jobs.items():
        for j in jobs:
            jid = j.get("jobId") or f"{j['title']}_{j.get('company','')}"
            if jid not in seen:
                seen.add(jid)
                unique_jobs.append({**j, "keyword": kw, "search_location": loc})

    lines.append(f"## Unique Jobs: {len(unique_jobs)}")
    lines.append("")

    # Group by search location
    by_location = {}
    for j in unique_jobs:
        loc = j.get("search_location", "Unknown")
        by_location.setdefault(loc, []).append(j)

    for loc in LOCATIONS:
        jobs = by_location.get(loc, [])
        if not jobs:
            continue
        lines.append(f"### {loc} ({len(jobs)} jobs)")
        lines.append("")
        for j in jobs:
            title = j.get("title", "Unknown")
            company = j.get("company", "")
            job_loc = j.get("location", "")
            link = j.get("link", "")
            company_str = f" at {company}" if company else ""
            loc_str = f" ({job_loc})" if job_loc else ""
            link_str = f" - [View]({link})" if link else ""
            lines.append(f"- **{title}**{company_str}{loc_str}{link_str}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Engine: camofox-browser v2.0.4 | Scanned: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Job Scout (Camofox)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output markdown file")
    args = parser.parse_args()

    logging.info("Starting LinkedIn Job Scout (Camofox Edition)...")
    start_time = time.time()

    ensure_server()

    # Open a tab and import cookies
    out, err, rc = run_camofox(["open", "https://www.linkedin.com/feed/"], timeout=30)
    if rc != 0:
        logging.error(f"Failed to open LinkedIn: {err}")
        sys.exit(1)

    try:
        tab_data = json.loads(out)
        tab_id = tab_data.get("tabId", "")
    except (json.JSONDecodeError, AttributeError):
        tab_id = ""
        for line in out.split("\n"):
            if "tabId" in line:
                tab_id = line.split(":")[-1].strip().strip('"')
                break

    if not tab_id:
        logging.error("No tabId returned")
        sys.exit(1)

    # Import cookies
    if COOKIES_FILE.exists():
        run_camofox(["cookie", "import", str(COOKIES_FILE), tab_id], timeout=10)
        time.sleep(1)
        # Re-navigate to apply cookies
        run_camofox(["navigate", "https://www.linkedin.com/feed/", tab_id], timeout=15)
        time.sleep(2)

    # Accept cookie consent
    run_camofox(["click", "button:has-text('Accept')", tab_id], timeout=5)
    time.sleep(1)

    # Run all searches
    all_jobs = {}
    completed = 0
    total = len(KEYWORDS) * len(LOCATIONS)

    for i, keyword in enumerate(KEYWORDS):
        for j, location in enumerate(LOCATIONS):
            search_num = i * len(LOCATIONS) + j + 1
            logging.info(f"Search {search_num}/{total}: '{keyword}' in '{location}'")

            try:
                jobs = search_jobs(keyword, location, tab_id)
                all_jobs[(keyword, location)] = jobs
                completed += 1
            except Exception as e:
                logging.error(f"Error on search {search_num}: {e}")
                all_jobs[(keyword, location)] = []

            # Small delay between searches to avoid rate limiting
            time.sleep(2)

    # Close tab
    run_camofox(["close", tab_id], timeout=5)

    duration = time.time() - start_time
    total_jobs = sum(len(v) for v in all_jobs.values())

    stats = {
        "total_searches": total,
        "completed": completed,
        "total_jobs": total_jobs,
        "duration_sec": duration,
    }

    # Generate and save report
    report = generate_report(all_jobs, stats)
    output_path = Path(args.output)
    output_path.write_text(report)
    logging.info(f"Report saved to {output_path}")
    logging.info(f"Stats: {completed}/{total} searches, {total_jobs} jobs, {duration:.0f}s")

    # Also output JSON summary for agent consumption
    summary = {
        "status": "complete" if completed == total else "partial",
        "completed": completed,
        "total_searches": total,
        "unique_jobs": total_jobs,
        "duration_seconds": round(duration),
        "output_file": str(output_path),
        "engine": "camofox",
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    import sys
    main()
