#!/usr/bin/env python3
"""
Job Radar v3: GCC Executive Job Search using JobSpy
Searches LinkedIn, Indeed, Bayt, and Google Jobs for VP/C-Suite roles.
Output: memory/job-radar.md
"""

import sys
import json
from datetime import datetime
from jobspy import scrape_jobs

DATE = datetime.now().strftime("%Y-%m-%d")
OUTPUT = "/root/.openclaw/workspace/memory/job-radar.md"

# Ahmed's target searches
SEARCHES = [
    {
        "label": "Digital Transformation Executive (UAE)",
        "search_term": "Digital Transformation VP Director Head",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "Digital Transformation Executive (Saudi)",
        "search_term": "Digital Transformation VP Director Head",
        "location": "Riyadh",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "Digital Transformation Executive (Qatar)",
        "search_term": "Digital Transformation VP Director Head",
        "location": "Doha",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "CTO / Head of Technology (UAE)",
        "search_term": "CTO Chief Technology Officer Head Technology",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "PMO / Program Director (GCC)",
        "search_term": "Head PMO Program Director Transformation",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "HealthTech / AI Executive (GCC)",
        "search_term": "Head AI HealthTech Digital Health VP",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "FinTech Executive (GCC)",
        "search_term": "VP FinTech Head Payments Digital Banking",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
]

def run_search(search_config):
    """Run a single search and return results."""
    try:
        sites = search_config.get("sites", ["indeed", "google"])
        kwargs = {
            "site_name": sites,
            "search_term": search_config["search_term"],
            "location": search_config.get("location", "Dubai"),
            "results_wanted": 10,
            "hours_old": 168,  # 7 days
            "verbose": 0,
        }
        if "country_indeed" in search_config:
            kwargs["country_indeed"] = search_config["country_indeed"]

        jobs = scrape_jobs(**kwargs)
        return jobs
    except Exception as e:
        return f"ERROR: {e}"


def format_jobs(df, label):
    """Format job results as markdown."""
    lines = [f"### {label}\n"]

    if isinstance(df, str):
        lines.append(f"⚠️ {df}\n")
        return "\n".join(lines)

    if df is None or len(df) == 0:
        lines.append("No results found.\n")
        return "\n".join(lines)

    count = 0
    for _, row in df.iterrows():
        title = row.get("title", "N/A")
        company = row.get("company", "N/A")
        location_val = row.get("location", "N/A")
        url = row.get("job_url", "")
        date_posted = row.get("date_posted", "")
        job_type = row.get("job_type", "")
        salary_min = row.get("min_amount", "")
        salary_max = row.get("max_amount", "")
        salary_str = ""
        if salary_min and salary_max:
            salary_str = f" | 💰 {salary_min}-{salary_max}"
        elif salary_min:
            salary_str = f" | 💰 {salary_min}+"

        lines.append(f"- **{title}** at {company}")
        lines.append(f"  📍 {location_val} | 📅 {date_posted}{salary_str}")
        if url:
            lines.append(f"  🔗 {url}")
        lines.append("")
        count += 1

    lines.append(f"*{count} results*\n")
    return "\n".join(lines)


def main():
    print(f"🔍 Job Radar v3 running: {DATE}")
    
    all_results = []
    all_results.append(f"# Job Radar: {DATE}\n")
    all_results.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*\n")
    all_results.append(f"*Engine: JobSpy (LinkedIn, Indeed, Google Jobs, Bayt)*\n")
    all_results.append("---\n")

    seen_urls = set()

    for search in SEARCHES:
        print(f"  Searching: {search['label']}...")
        df = run_search(search)
        
        # Deduplicate across searches
        if not isinstance(df, str) and df is not None and len(df) > 0:
            mask = ~df["job_url"].isin(seen_urls)
            new_urls = set(df["job_url"].dropna().tolist())
            seen_urls.update(new_urls)
            df = df[mask]
        
        formatted = format_jobs(df, search["label"])
        all_results.append(formatted)

    all_results.append("---\n")
    all_results.append(f"*Total unique URLs found: {len(seen_urls)}*\n")

    # Write output
    with open(OUTPUT, "w") as f:
        f.write("\n".join(all_results))

    print(f"✅ Results written to {OUTPUT}")
    print(f"   Total unique jobs: {len(seen_urls)}")


if __name__ == "__main__":
    main()
