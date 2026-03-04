#!/usr/bin/env python3
"""
Job Radar v2 - JobSpy Edition
Replaces Tavily-based job-radar.sh with structured LinkedIn/Indeed scraping.
Runs daily via OpenClaw cron at 7 AM Cairo (5 AM UTC).

Output: memory/job-radar.md (overwritten daily)
Pipeline: jobs-bank/pipeline.md (new roles added to Radar section)
"""

import os
import re
import sys
from datetime import datetime, timezone

# Add venv to path
VENV_PATH = "/root/.openclaw/workspace/tools/jobspy-venv/lib/python3.13/site-packages"
sys.path.insert(0, VENV_PATH)

from jobspy import scrape_jobs
import pandas as pd

WORKSPACE = "/root/.openclaw/workspace"
RADAR_OUTPUT = f"{WORKSPACE}/memory/job-radar.md"
PIPELINE_FILE = f"{WORKSPACE}/jobs-bank/pipeline.md"
SCAN_ARCHIVE = f"{WORKSPACE}/jobs-bank/scans"

# Search configuration
SEARCHES = [
    # UAE
    ("VP Digital Transformation", "united arab emirates", "Dubai"),
    ("Director AI", "united arab emirates", "Dubai"),
    ("Head of Technology", "united arab emirates", "Dubai"),
    ("CTO", "united arab emirates", "Dubai"),
    # Saudi Arabia
    ("VP Digital Transformation", "saudi arabia", "Riyadh"),
    ("Director AI", "saudi arabia", "Riyadh"),
    # Qatar
    ("Director Technology", "qatar", "Doha"),
    # Bahrain
    ("Head of Technology", "bahrain", "Manama"),
]

# Executive title keywords
EXECUTIVE_KEYWORDS = [
    "VP", "Vice President", "Director", "Head of", "Chief",
    "CTO", "COO", "CFO", "CEO", "SVP", "Senior Director",
    "Executive Director", "Principal", "Managing Director"
]

# Relevance keywords (for scoring)
RELEVANCE_KEYWORDS = [
    "AI", "Digital", "Transformation", "Technology", "PMO",
    "Project", "Data", "Strategy", "Innovation", "Engineering",
    "HealthTech", "FinTech", "Operations"
]

# Roles to exclude (clearly not matching Ahmed's profile)
EXCLUDE_PATTERNS = [
    r"sales rep", r"insurance", r"sustainability", r"compliance",
    r"legal", r"travel", r"logistics coordinator", r"office manager",
    r"copywriter", r"editor", r"marketing manager", r"account manager",
    r"recruitment", r"hr ", r"human resources", r"finance consultant",
    r"security officer", r"ciso", r"investor club", r"real estate",
    r"brokerage", r"web3", r"crypto", r"blockchain", r"receptionist",
    r"art director", r"creative director", r"design director",
    r"architectural", r"building safety", r"envelope", r"procurement",
    r"vendor management", r"gallery", r"interior", r"landscape",
    r"nursing", r"medical director", r"clinical", r"dental",
    r"chef", r"food", r"beverage", r"hospitality director",
    r"product design", r"ux director", r"store manager",
]


def is_executive(title):
    """Check if title is executive-level."""
    if pd.isna(title):
        return False
    return any(kw.lower() in title.lower() for kw in EXECUTIVE_KEYWORDS)


def is_excluded(title):
    """Check if title matches exclusion patterns."""
    if pd.isna(title):
        return True
    title_lower = title.lower()
    return any(re.search(pat, title_lower) for pat in EXCLUDE_PATTERNS)


def relevance_score(title):
    """Score relevance 0-13 based on keyword matches."""
    if pd.isna(title):
        return 0
    return sum(1 for kw in RELEVANCE_KEYWORDS if kw.lower() in title.lower())


def get_pipeline_companies():
    """Extract company names from existing pipeline to avoid duplicates."""
    companies = set()
    try:
        with open(PIPELINE_FILE, "r") as f:
            for line in f:
                # Match active pipeline rows
                match = re.search(r'\|\s*(?:☑️|~~)?\s*([A-Za-z][A-Za-z0-9\s&\(\)\.]+?)\s*(?:~~)?\s*\|', line)
                if match:
                    company = match.group(1).strip().lower()
                    if company and company not in ("company", "none"):
                        companies.add(company)
                # Also match radar rows
                match2 = re.search(r'^\|\s*([A-Za-z][A-Za-z0-9\s&\(\)\.]+?)\s*\|.*\|.*\|.*Priority', line)
                if match2:
                    companies.add(match2.group(1).strip().lower())
    except FileNotFoundError:
        pass
    return companies


def run_scan():
    """Run all searches and return deduplicated results."""
    all_jobs = []
    errors = []

    for term, country, location in SEARCHES:
        try:
            jobs = scrape_jobs(
                site_name=["indeed", "linkedin"],
                search_term=term,
                location=location,
                results_wanted=10,
                hours_old=72,  # Last 3 days
                country_indeed=country
            )
            if len(jobs) > 0:
                jobs["search_term"] = term
                jobs["search_country"] = country
                all_jobs.append(jobs)
                print(f"  ✅ {term} / {location}: {len(jobs)} results")
            else:
                print(f"  ⚪ {term} / {location}: 0 results")
        except Exception as e:
            errors.append(f"{term} / {location}: {e}")
            print(f"  ❌ {term} / {location}: ERROR - {e}")

    if not all_jobs:
        return pd.DataFrame(), errors

    df = pd.concat(all_jobs, ignore_index=True)
    df = df.drop_duplicates(subset=["job_url"], keep="first")
    return df, errors


def filter_and_score(df):
    """Filter for executive roles and score relevance."""
    # Filter executive-level
    df = df[df["title"].apply(is_executive)].copy()

    # Remove excluded roles
    df = df[~df["title"].apply(is_excluded)].copy()

    # Score relevance
    df["relevance"] = df["title"].apply(relevance_score)

    # Sort by relevance descending
    df = df.sort_values("relevance", ascending=False)

    return df


def deduplicate_against_pipeline(df):
    """Remove jobs where company is already in pipeline."""
    pipeline_companies = get_pipeline_companies()

    def is_new(row):
        if pd.isna(row["company"]):
            return False
        company = str(row["company"]).lower()
        for pc in pipeline_companies:
            if pc in company or company in pc:
                return False
        return True

    return df[df.apply(is_new, axis=1)].copy()


def prioritize(title):
    """Assign priority based on title."""
    title_lower = title.lower() if not pd.isna(title) else ""
    high = ["vp ", "vice president", "chief", "cto", "coo", "ceo", "head of ai", "head of digital", "head of pmo"]
    if any(kw in title_lower for kw in high):
        return "🔴 High"
    return "🟡 Medium"


def write_radar_output(df, errors, date_str):
    """Write clean markdown output to memory/job-radar.md."""
    lines = [
        f"# Job Radar Report - {date_str}",
        "",
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        f"*Source: JobSpy (LinkedIn + Indeed) | Last 72 hours*",
        "",
        "---",
        "",
        f"## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Searches run | {len(SEARCHES)} |",
        f"| New executive roles found | {len(df)} |",
        f"| Search errors | {len(errors)} |",
        "",
    ]

    if len(df) > 0:
        lines.extend([
            "## New Roles (Not in Pipeline)",
            "",
            "| Priority | Role | Company | Location | URL |",
            "|----------|------|---------|----------|-----|",
        ])
        for _, j in df.iterrows():
            title = j.get("title", "?")
            company = j.get("company", "?")
            location = str(j.get("location", "?")).replace("nan", "?")
            url = j.get("job_url", "")
            priority = prioritize(title)
            lines.append(f"| {priority} | {title} | {company} | {location} | [Link]({url}) |")

        lines.append("")
    else:
        lines.extend(["## No New Roles Found", "", "All executive-level results are already in pipeline.", ""])

    if errors:
        lines.extend(["## Search Errors", ""])
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    lines.extend(["---", "", "**Links:** [[../jobs-bank/pipeline.md]] | [[../MEMORY.md]]", ""])

    with open(RADAR_OUTPUT, "w") as f:
        f.write("\n".join(lines))

    print(f"\n📝 Radar output written to {RADAR_OUTPUT}")


def main():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"🔍 Job Radar v2 - {date_str}")
    print(f"   Searching {len(SEARCHES)} terms across GCC...\n")

    # Run scan
    df, errors = run_scan()

    if df.empty:
        print("\n⚠️ No results from any search")
        write_radar_output(pd.DataFrame(), errors, date_str)
        return

    print(f"\n📊 Total raw results: {len(df)}")

    # Filter and score
    df = filter_and_score(df)
    print(f"📊 Executive-level (filtered): {len(df)}")

    # Deduplicate against pipeline
    df = deduplicate_against_pipeline(df)
    print(f"📊 New (not in pipeline): {len(df)}")

    # Write output
    write_radar_output(df, errors, date_str)

    # Archive scan
    os.makedirs(SCAN_ARCHIVE, exist_ok=True)
    if len(df) > 0:
        df.to_csv(f"{SCAN_ARCHIVE}/scan-{date_str}.csv", index=False)
        print(f"📁 Scan archived to {SCAN_ARCHIVE}/scan-{date_str}.csv")

    print(f"\n✅ Job Radar complete. {len(df)} new roles found.")


if __name__ == "__main__":
    main()
