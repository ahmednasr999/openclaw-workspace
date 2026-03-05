#!/usr/bin/env python3
"""
Job Radar v3: GCC Executive Job Search using JobSpy
Searches LinkedIn, Indeed, and Google Jobs for VP/C-Suite roles.
Auto-deduplicates against pipeline.md and adds good matches.
Output: memory/job-radar.md + jobs-bank/pipeline.md updates
"""

import re
import sys
from datetime import datetime
from jobspy import scrape_jobs

DATE = datetime.now().strftime("%Y-%m-%d")
OUTPUT = "/root/.openclaw/workspace/memory/job-radar.md"
PIPELINE = "/root/.openclaw/workspace/jobs-bank/pipeline.md"

# Seniority keywords that signal executive-level roles
EXEC_KEYWORDS = [
    "vp", "vice president", "director", "head of", "chief",
    "cto", "coo", "ceo", "cio", "cdo", "cpo", "cfo",
    "svp", "evp", "managing director", "general manager",
    "transformation lead", "program director", "senior director",
]

# Keywords that signal wrong domain or too junior
SKIP_KEYWORDS = [
    "intern", "junior", "associate", "coordinator", "analyst",
    "web3", "crypto", "blockchain", "gaming", "game",
    "teacher", "instructor", "professor", "lecturer",
    "nurse", "physician", "dentist", "pharmacist",
    "graphic design", "interior design", "fashion",
    "chef", "cook", "barista", "waiter",
]

# Ahmed's target searches: broad enough to catch opportunities
SEARCHES = [
    {
        "label": "Digital Transformation Executive (UAE)",
        "search_term": "VP Director Head Digital Transformation",
        "location": "United Arab Emirates",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "Digital Transformation Executive (Saudi)",
        "search_term": "VP Director Head Digital Transformation",
        "location": "Saudi Arabia",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "Digital Transformation Executive (Qatar)",
        "search_term": "VP Director Head Digital Transformation",
        "location": "Qatar",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "CTO / Head of Technology (GCC)",
        "search_term": "CTO Chief Technology Officer VP Technology",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "PMO / Program Director (GCC)",
        "search_term": "Director PMO Head PMO Program Director",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "HealthTech / AI Executive (GCC)",
        "search_term": "VP Director Head AI HealthTech Digital Health",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "FinTech / Payments Executive (GCC)",
        "search_term": "VP Director Head FinTech Payments Digital Banking",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
    {
        "label": "IT Director / VP IT (GCC)",
        "search_term": "VP IT Director Information Technology Head IT",
        "location": "Dubai",
        "country_indeed": "worldwide",
        "sites": ["linkedin", "indeed", "google"],
    },
]


def get_existing_urls():
    """Read pipeline.md and extract all existing job URLs."""
    try:
        with open(PIPELINE, "r") as f:
            content = f.read()
        urls = set(re.findall(r'linkedin\.com/jobs/view/(\d+)', content))
        return urls
    except FileNotFoundError:
        return set()


def is_executive_level(title):
    """Check if job title matches executive seniority."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in EXEC_KEYWORDS)


def should_skip(title):
    """Check if job should be skipped based on domain/level."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in SKIP_KEYWORDS)


def extract_job_id(url):
    """Extract LinkedIn job ID from URL."""
    match = re.search(r'linkedin\.com/jobs/view/(\d+)', str(url))
    return match.group(1) if match else None


def run_search(search_config):
    """Run a single search and return results."""
    try:
        sites = search_config.get("sites", ["indeed", "google"])
        kwargs = {
            "site_name": sites,
            "search_term": search_config["search_term"],
            "location": search_config.get("location", "Dubai"),
            "results_wanted": 15,
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
        return "\n".join(lines), []
    if df is None or len(df) == 0:
        lines.append("No results found.\n")
        return "\n".join(lines), []

    qualified = []
    count = 0
    for _, row in df.iterrows():
        title = str(row.get("title", "N/A"))
        company = str(row.get("company", "N/A"))
        location_val = str(row.get("location", "N/A"))
        url = str(row.get("job_url", ""))
        date_posted = str(row.get("date_posted", ""))
        salary_min = row.get("min_amount", "")
        salary_max = row.get("max_amount", "")
        salary_str = ""
        if salary_min and salary_max:
            salary_str = f" | 💰 {salary_min}-{salary_max}"
        elif salary_min:
            salary_str = f" | 💰 {salary_min}+"

        # Tag executive vs skip
        exec_match = is_executive_level(title)
        skip_match = should_skip(title)
        tag = ""
        if skip_match:
            tag = " ⛔"
        elif exec_match:
            tag = " 🎯"
            qualified.append({
                "title": title,
                "company": company,
                "location": location_val,
                "url": url,
                "date_posted": date_posted,
            })

        lines.append(f"- **{title}** at {company}{tag}")
        lines.append(f"  📍 {location_val} | 📅 {date_posted}{salary_str}")
        if url and url != "nan":
            lines.append(f"  🔗 {url}")
        lines.append("")
        count += 1

    lines.append(f"*{count} results ({len(qualified)} executive-level)*\n")
    return "\n".join(lines), qualified


def add_to_pipeline(new_jobs, existing_ids):
    """Append new qualified jobs to pipeline.md as Discovered."""
    if not new_jobs:
        return 0

    added = 0
    lines_to_add = []
    
    # Read current pipeline to find the last row number
    try:
        with open(PIPELINE, "r") as f:
            content = f.read()
        # Find the highest row number
        row_nums = re.findall(r'\|\s*(\d+)\s*\|', content)
        next_num = max(int(n) for n in row_nums) + 1 if row_nums else 1
    except Exception:
        next_num = 1
        content = ""

    for job in new_jobs:
        job_id = extract_job_id(job["url"])
        if job_id and job_id in existing_ids:
            continue  # Already in pipeline
        
        # Clean location for table
        loc = job["location"].split(",")[0].strip() if job["location"] else "GCC"
        
        line = f"| {next_num} | 🆕 | {job['company']} | {job['title']} | {loc} | — | 🆕 Discovered | Radar | {DATE} | — | [LinkedIn]({job['url']}) | — |"
        lines_to_add.append(line)
        next_num += 1
        added += 1

    if lines_to_add:
        # Find the end of the Active Pipeline table and append
        # Look for the last table row before any section break
        insert_text = "\n".join(lines_to_add) + "\n"
        
        # Find position after last pipeline row
        table_rows = list(re.finditer(r'\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|', content))
        if table_rows:
            last_row_end = table_rows[-1].end()
            content = content[:last_row_end] + "\n" + insert_text + content[last_row_end:]
        else:
            content += "\n" + insert_text

        with open(PIPELINE, "w") as f:
            f.write(content)

    return added


def main():
    print(f"🔍 Job Radar v3 running: {DATE}")
    
    existing_ids = get_existing_urls()
    print(f"   Pipeline has {len(existing_ids)} existing job IDs")
    
    all_results = []
    all_results.append(f"# Job Radar: {DATE}\n")
    all_results.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*\n")
    all_results.append(f"*Engine: JobSpy (LinkedIn, Indeed, Google Jobs)*\n")
    all_results.append(f"*🎯 = Executive match | ⛔ = Auto-skipped*\n")
    all_results.append("---\n")

    seen_urls = set()
    all_qualified = []

    for search in SEARCHES:
        print(f"  Searching: {search['label']}...")
        df = run_search(search)
        
        # Deduplicate across searches
        if not isinstance(df, str) and df is not None and len(df) > 0:
            mask = ~df["job_url"].isin(seen_urls)
            new_urls = set(df["job_url"].dropna().tolist())
            seen_urls.update(new_urls)
            df = df[mask]
        
        formatted, qualified = format_jobs(df, search["label"])
        all_results.append(formatted)
        all_qualified.extend(qualified)

    # Deduplicate qualified jobs
    seen_qualified = set()
    unique_qualified = []
    for job in all_qualified:
        job_id = extract_job_id(job["url"])
        if job_id and job_id not in seen_qualified:
            seen_qualified.add(job_id)
            unique_qualified.append(job)

    # Add to pipeline
    added = add_to_pipeline(unique_qualified, existing_ids)
    
    all_results.append("---\n")
    all_results.append(f"## Summary\n")
    all_results.append(f"- Total unique jobs found: {len(seen_urls)}")
    all_results.append(f"- Executive-level matches: {len(unique_qualified)}")
    all_results.append(f"- Already in pipeline: {len(unique_qualified) - added}")
    all_results.append(f"- **New jobs added to pipeline: {added}**\n")

    # Write radar output
    with open(OUTPUT, "w") as f:
        f.write("\n".join(all_results))

    print(f"✅ Results written to {OUTPUT}")
    print(f"   Total unique jobs: {len(seen_urls)}")
    print(f"   Executive matches: {len(unique_qualified)}")
    print(f"   New added to pipeline: {added}")


if __name__ == "__main__":
    main()
