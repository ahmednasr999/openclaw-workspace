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

# Kill list: domains/roles to skip entirely
KILL_LIST = [
    # Sales & Revenue
    "sales", "account executive", "business development", "revenue",
    # HR
    "human resources", "hr manager", "recruiter", "talent acquisition",
    # Supply Chain & Operations (non-tech)
    "supply chain", "logistics", "procurement", "warehouse",
    # Admin & Support
    "admin", "office manager", "executive assistant", "receptionist",
    # Beauty & Fashion
    "beauty", "cosmetics", "fashion", "retail",
    # Construction & Facilities
    "construction", "facilities", "property", "real estate",
    # Other non-tech
    "marketing coordinator", "social media manager", "content writer",
    "teacher", "instructor", "professor", "lecturer",
]

# ATS score thresholds (simplified keyword-based proxy scoring)
# Real ATS scoring requires JD + CV, done manually per application
ATS_THRESHOLD = 82  # Floor from MEMORY.md
BORDERLINE_MIN = 80  # Buffer zone: 80-81

# Ghost job detection: keywords that indicate vague/risky postings
GHOST_INDICATORS = [
    "fast-paced", "rockstar", "ninja", "wear many hats",
    "must love dogs", "work hard play hard",
]

# Days after which a job is considered stale (likely ghost)
STALE_DAYS = 14

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


def should_skip(title):
    """Check if job should be skipped based on kill list."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in KILL_LIST)


def proxy_ats_score(title, description=""):
    """
    Proxy ATS scoring based on keyword matching with Ahmed's profile.
    This is a simplified heuristic - real scoring requires JD + CV.
    Returns: (score, factors)
    """
    title_lower = title.lower()
    desc_lower = description.lower() if description else ""
    combined = title_lower + " " + desc_lower
    
    score = 50  # Base score
    factors = []
    
    # Strong positive indicators (executive level + tech/DT/PMO)
    exec_strong = ["vp", "vice president", "svp", "evp", "chief", "cto", "cio", "cdo", "cpo", "cfo", "coo"]
    if any(kw in title_lower for kw in exec_strong):
        score += 15
        factors.append("executive")
    
    # Director level
    if "director" in title_lower:
        score += 12
        factors.append("director")
    
    # Head of / GM
    if "head of" in title_lower or "general manager" in title_lower:
        score += 10
        factors.append("senior")
    
    # Managing / Program / Transformation
    if any(kw in combined for kw in ["transformation", "program", "managing"]):
        score += 8
        factors.append("transformation")
    
    # Tech/DT/PMO domain keywords
    tech_keywords = [
        "digital", "technology", "it ", "ict", "software", "ai", "artificial intelligence",
        "machine learning", "data", "analytics", "cloud", "cybersecurity", "erp",
        "pmo", "project management", "program management", "change management",
        "healthtech", "fintech", "e-commerce", "ecommerce",
    ]
    tech_count = sum(1 for kw in tech_keywords if kw in combined)
    score += min(tech_count * 4, 16)
    if tech_count > 0:
        factors.append("tech")
    
    # Negative indicators
    if any(kw in title_lower for kw in ["intern", "junior", "associate", "coordinator"]):
        score -= 20
        factors.append("junior")
    
    if any(kw in combined for kw in ["web3", "crypto", "blockchain"]):
        score -= 15
    
    # Clamp score
    score = max(0, min(100, score))
    
    return score, factors


def is_ghost_job(row):
    """Check if job is likely a ghost job or stale posting."""
    from datetime import timedelta
    
    title = str(row.get("title", "")).lower()
    company = str(row.get("company", "")).lower()
    description = str(row.get("description", "")).lower() if "description" in row else ""
    date_posted = str(row.get("date_posted", ""))
    
    # Check for stale posting (older than STALE_DAYS)
    # Try to parse common date formats
    try:
        if date_posted and date_posted != "nan" and date_posted != "":
            # Handle "X days ago" format
            if "day" in date_posted.lower():
                import re
                match = re.search(r'(\d+)', date_posted)
                if match:
                    days_old = int(match.group(1))
                    if days_old > STALE_DAYS:
                        return "stale"
            # Handle "X hours ago" - always fresh
            elif "hour" in date_posted.lower():
                pass  # Fresh
            # Handle relative dates like "yesterday" 
            elif "yesterday" in date_posted.lower():
                pass  # 1 day old, fresh enough
            else:
                # Try parsing as date
                try:
                    from datetime import datetime
                    parsed = datetime.strptime(date_posted[:10], "%Y-%m-%d")
                    age = datetime.now() - parsed
                    if age > timedelta(days=STALE_DAYS):
                        return "stale"
                except:
                    pass
    except:
        pass
    
    # Check for vague/ghost indicators in title or description
    ghost_score = 0
    for indicator in GHOST_INDICATORS:
        if indicator in title or indicator in description:
            ghost_score += 1
    
    if ghost_score >= 2:
        return "vague"
    
    return None  # Not a ghost job


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
    """Format job results with ATS proxy scoring."""
    lines = [f"### {label}\n"]
    if isinstance(df, str):
        lines.append(f"⚠️ {df}\n")
        return "\n".join(lines), [], {}
    if df is None or len(df) == 0:
        lines.append("No results found.\n")
        return "\n".join(lines), [], {}

    qualified = []
    borderline = []
    skipped = 0
    ghost_count = 0
    for _, row in df.iterrows():
        title = str(row.get("title", "N/A"))
        company = str(row.get("company", "N/A"))
        location_val = str(row.get("location", "N/A"))
        url = str(row.get("job_url", ""))
        date_posted = str(row.get("date_posted", ""))
        description = str(row.get("description", "")) if "description" in row else ""
        salary_min = row.get("min_amount", "")
        salary_max = row.get("max_amount", "")
        salary_str = ""
        if salary_min and salary_max:
            salary_str = f" | 💰 {salary_min}-{salary_max}"
        elif salary_min:
            salary_str = f" | 💰 {salary_min}+"

        # Check for ghost jobs
        ghost_status = is_ghost_job(row)
        
        # Kill list check
        if should_skip(title):
            tag = " ⛔ (kill list)"
            skipped += 1
        # Ghost job
        elif ghost_status:
            tag = f" 👻 ({ghost_status})"
            ghost_count += 1
        else:
            # ATS proxy scoring
            ats_score, factors = proxy_ats_score(title, description)
            
            if ats_score >= ATS_THRESHOLD:
                tag = f" 🎯 ATS:{ats_score}"
                qualified.append({
                    "title": title,
                    "company": company,
                    "location": location_val,
                    "url": url,
                    "date_posted": date_posted,
                    "ats_score": ats_score,
                })
            elif ats_score >= BORDERLINE_MIN:
                tag = f" ⚠️ ATS:{ats_score} (borderline)"
                borderline.append({
                    "title": title,
                    "company": company,
                    "location": location_val,
                    "url": url,
                    "ats_score": ats_score,
                })
            else:
                tag = f" ⛔ ATS:{ats_score} (low)"
                skipped += 1

        lines.append(f"- **{title}** at {company}{tag}")
        lines.append(f"  📍 {location_val} | 📅 {date_posted}{salary_str}")
        if url and url != "nan":
            lines.append(f"  🔗 {url}")
        lines.append("")

    lines.append(f"*{len(qualified)} qualified (ATS {ATS_THRESHOLD}+), {len(borderline)} borderline ({BORDERLINE_MIN}-{ATS_THRESHOLD-1}), {skipped} skipped, {ghost_count} ghost jobs*\n")
    return "\n".join(lines), qualified, borderline


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
    print(f"   ATS Threshold: {ATS_THRESHOLD}+ | Borderline: {BORDERLINE_MIN}-{ATS_THRESHOLD-1}")
    
    existing_ids = get_existing_urls()
    print(f"   Pipeline has {len(existing_ids)} existing job IDs")
    
    all_results = []
    all_results.append(f"# Job Radar: {DATE}\n")
    all_results.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*\n")
    all_results.append(f"*Engine: JobSpy (LinkedIn, Indeed, Google Jobs)*\n")
    all_results.append(f"*Filter: ATS {ATS_THRESHOLD}+ required | Borderline {BORDERLINE_MIN}-{ATS_THRESHOLD-1} in buffer*\n")
    all_results.append(f"*🎯 = Qualified (ATS {ATS_THRESHOLD}+) | ⚠️ = Borderline (buffer) | ⛔ = Skipped | 👻 = Ghost job*\n")
    all_results.append("---\n")

    seen_urls = set()
    all_qualified = []
    all_borderline = []

    for search in SEARCHES:
        print(f"  Searching: {search['label']}...")
        df = run_search(search)
        
        # Deduplicate across searches
        if not isinstance(df, str) and df is not None and len(df) > 0:
            mask = ~df["job_url"].isin(seen_urls)
            new_urls = set(df["job_url"].dropna().tolist())
            seen_urls.update(new_urls)
            df = df[mask]
        
        formatted, qualified, borderline = format_jobs(df, search["label"])
        all_results.append(formatted)
        all_qualified.extend(qualified)
        all_borderline.extend(borderline)

    # Deduplicate qualified jobs
    seen_qualified = set()
    unique_qualified = []
    for job in all_qualified:
        job_id = extract_job_id(job["url"])
        if job_id and job_id not in seen_qualified:
            seen_qualified.add(job_id)
            unique_qualified.append(job)

    # Deduplicate borderline
    seen_borderline = set()
    unique_borderline = []
    for job in all_borderline:
        job_id = extract_job_id(job["url"])
        if job_id and job_id not in seen_borderline and job_id not in seen_qualified:
            seen_borderline.add(job_id)
            unique_borderline.append(job)

    # Add to pipeline
    added = add_to_pipeline(unique_qualified, existing_ids)
    
    all_results.append("---\n")
    all_results.append(f"## Summary\n")
    all_results.append(f"- Total unique jobs found: {len(seen_urls)}")
    all_results.append(f"- **Qualified (ATS {ATS_THRESHOLD}+): {len(unique_qualified)}**")
    all_results.append(f"- Borderline (ATS {BORDERLINE_MIN}-{ATS_THRESHOLD-1}): {len(unique_borderline)}")
    all_results.append(f"- Already in pipeline: {len(unique_qualified) - added}")
    all_results.append(f"- **New jobs added to pipeline: {added}**\n")
    all_results.append(f"*Borderline jobs held in buffer (not added to pipeline).*\n")
    all_results.append(f"*Ghost job filter: Jobs >14 days old or with vague indicators flagged.*\n")
    all_results.append(f"*Kill list: Sales, HR, supply chain, admin, beauty, construction, facilities excluded.*\n")

    # Write radar output
    with open(OUTPUT, "w") as f:
        f.write("\n".join(all_results))

    print(f"✅ Results written to {OUTPUT}")
    print(f"   Total unique jobs: {len(seen_urls)}")
    print(f"   Qualified (ATS {ATS_THRESHOLD}+): {len(unique_qualified)}")
    print(f"   Borderline (buffer): {len(unique_borderline)}")
    print(f"   New added to pipeline: {added}")


if __name__ == "__main__":
    main()
