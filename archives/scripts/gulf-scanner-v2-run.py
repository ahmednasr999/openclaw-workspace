#!/usr/bin/env python3
"""
LinkedIn Gulf Jobs Scanner v2 - Using python-jobspy
Searches LinkedIn, Indeed, Bayt, Google for GCC executive roles.
"""

import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

from jobspy import scrape_jobs

COUNTRIES = [
    ("Saudi Arabia", "saudi arabia"),
    ("United Arab Emirates", "united arab emirates"),
    ("Qatar", "qatar"),
    ("Bahrain", "bahrain"),
    ("Kuwait", "kuwait"),
    ("Oman", "oman"),
]

PREFERRED = {"Saudi Arabia", "United Arab Emirates"}

# Group titles into search batches to reduce API calls
SEARCH_TERMS = [
    "Chief Digital Officer OR Chief Technology Officer OR CTO OR CDO",
    "VP Digital Transformation OR Director Digital Transformation OR Head of Digital Transformation",
    "Chief Information Officer OR CIO OR Head of IT OR Head of Technology",
    "Director of Technology OR VP Technology OR VP IT OR Director of IT",
    "PMO Director OR Program Director OR Senior Director Digital",
    "Chief Operating Officer OR Chief Strategy Officer OR Head of Digital Innovation",
]

ATS_THRESHOLD = 82
NOTIFIED_FILE = Path("/root/.openclaw/workspace/jobs-bank/scraped/notified-jobs.md")
OUTPUT_DIR = Path("/root/.openclaw/workspace/jobs-bank/scraped")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Ahmed's key skills for ATS matching
AHMED_KEYWORDS = {
    "high": ["digital transformation", "pmo", "program management", "project management",
             "cloud", "aws", "azure", "ai", "artificial intelligence", "machine learning",
             "enterprise architecture", "technology roadmap", "p&l", "vision 2030"],
    "medium": ["fintech", "healthtech", "healthcare", "e-commerce", "ecommerce",
               "agile", "scrum", "lean", "six sigma", "pmp", "change management",
               "stakeholder management", "vendor management", "cybersecurity"],
    "industry": ["hospital", "health", "medical", "insurance", "banking", "payment",
                 "delivery", "logistics", "retail tech"],
    "seniority": ["vp", "vice president", "director", "head of", "chief", "c-level",
                  "executive", "senior director", "svp", "evp", "cto", "cio", "cdo", "coo"],
    "gcc": ["saudi", "uae", "dubai", "riyadh", "jeddah", "doha", "qatar", "bahrain",
            "kuwait", "oman", "muscat", "abu dhabi", "gcc", "gulf"],
}

PENALTY_KEYWORDS = ["beauty", "fashion", "retail sales", "food service", "hospitality",
                    "education teacher", "real estate agent", "construction labor",
                    "hr coordinator", "supply chain coordinator", "admin assistant"]

SENIORITY_EXCLUDE = ["intern", "junior", "entry level", "coordinator", "associate",
                     "analyst", "specialist", "officer" ]  # officer alone is too junior


def load_notified_urls():
    """Load already-notified job URLs."""
    if not NOTIFIED_FILE.exists():
        return set()
    content = NOTIFIED_FILE.read_text()
    urls = set(re.findall(r'https?://[^\s\)]+', content))
    return urls


def ats_score(title, company, location, description, job_level="", job_function="", company_industry=""):
    """Score job against Ahmed's profile. Returns 0-100."""
    # Combine all text fields for scoring
    text = f"{title} {company} {location} {description} {job_level} {job_function} {company_industry}".lower()
    score = 0

    # Keyword Match (40 pts) - more lenient
    kw_score = 0
    for kw in AHMED_KEYWORDS["high"]:
        if kw in text:
            kw_score += 5
    kw_score = min(kw_score, 25)
    for kw in AHMED_KEYWORDS["medium"]:
        if kw in text:
            kw_score += 3
    kw_score = min(kw_score, 40)
    score += kw_score

    # Experience Alignment (30 pts)
    exp_score = 0
    # Check job_level field for executive roles
    if job_level and "executive" in job_level.lower():
        exp_score += 15
    elif job_level and "senior" in job_level.lower():
        exp_score += 10
    # Check title for seniority
    for kw in AHMED_KEYWORDS["seniority"]:
        if kw in text:
            exp_score += 10
            break
    # Industry match
    for kw in AHMED_KEYWORDS["industry"]:
        if kw in text:
            exp_score += 5
    # Growth/transformation keywords
    if any(x in text for x in ["transformation", "scale", "growth", "enterprise", "digital"]):
        exp_score += 5
    exp_score = min(exp_score, 30)
    score += exp_score

    # Location Fit (20 pts)
    loc_score = 0
    for kw in AHMED_KEYWORDS["gcc"]:
        if kw in text:
            loc_score += 10
            break
    if any(x in text for x in ["saudi", "uae", "dubai", "riyadh"]):
        loc_score += 10  # Priority countries bonus
    loc_score = min(loc_score, 20)
    score += loc_score

    # Skills bonus (10 pts)
    skill_score = 0
    if any(x in text for x in ["ai", "artificial intelligence", "machine learning", "genai", "llm"]):
        skill_score += 5
    if any(x in text for x in ["healthtech", "health tech", "healthcare", "hospital", "medical"]):
        skill_score += 5
    if company_industry and any(x in company_industry.lower() for x in ["health", "hospital", "medical", "fintech", "payment", "banking", "retail", "logistics"]):
        skill_score += 3
    skill_score = min(skill_score, 10)
    score += skill_score

    # Penalties - be more lenient
    for kw in PENALTY_KEYWORDS:
        if kw in text:
            score -= 10
            break

    # Seniority filter: penalize junior roles more explicitly
    title_lower = title.lower()
    is_senior = any(s in title_lower for s in ["director", "head", "chief", "vp", "vice", "president", "executive", "senior"])
    if not is_senior:
        score -= 15

    return max(0, min(100, score))


def main():
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    print(f"=== LinkedIn Gulf Jobs Scanner v2 === {ts}")

    notified_urls = load_notified_urls()
    print(f"Previously notified: {len(notified_urls)} URLs")

    all_qualified = []
    all_borderline = []
    total_found = 0
    total_scored = 0
    errors = 0

    for country_name, country_query in COUNTRIES:
        print(f"\n--- {country_name} ---")
        country_jobs = []

        for search_term in SEARCH_TERMS:
            try:
                print(f"  Searching: {search_term[:60]}...")
                jobs = scrape_jobs(
                    site_name=["linkedin", "indeed", "bayt", "google"],
                    search_term=search_term,
                    location=country_query,
                    results_wanted=15,
                    hours_old=168,  # 7 days (wider net for v2)
                    linkedin_fetch_description=True,
                    country_indeed=country_query,
                    verbose=0,
                )

                if jobs is not None and len(jobs) > 0:
                    print(f"    Found: {len(jobs)} jobs")
                    for _, row in jobs.iterrows():
                        job_url = str(row.get("job_url", ""))
                        title = str(row.get("title", ""))
                        company = str(row.get("company", "Unknown"))
                        loc = str(row.get("location", country_name))
                        desc = str(row.get("description", ""))
                        date_posted = str(row.get("date_posted", ""))
                        salary_min = row.get("min_amount", None)
                        salary_max = row.get("max_amount", None)
                        site = str(row.get("site", ""))

                        if not job_url or job_url == "nan" or not title or title == "nan":
                            continue

                        job_level = str(row.get("job_level", "")) if str(row.get("job_level", "")) != "nan" else ""
                        job_function = str(row.get("job_function", "")) if str(row.get("job_function", "")) != "nan" else ""
                        company_industry = str(row.get("company_industry", "")) if str(row.get("company_industry", "")) != "nan" else ""

                        country_jobs.append({
                            "title": title,
                            "company": company,
                            "location": loc if loc != "nan" else country_name,
                            "country": country_name,
                            "url": job_url,
                            "description": desc[:2000] if desc != "nan" else "",
                            "date_posted": date_posted if date_posted != "nan" else "",
                            "salary_min": salary_min,
                            "salary_max": salary_max,
                            "site": site,
                            "job_level": job_level,
                            "job_function": job_function,
                            "company_industry": company_industry,
                        })
                else:
                    print(f"    Found: 0 jobs")

                time.sleep(2)  # Rate limit protection

            except Exception as e:
                errors += 1
                print(f"    ERROR: {e}")
                time.sleep(3)

        # Deduplicate by URL within country
        seen_urls = set()
        unique_jobs = []
        for job in country_jobs:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                unique_jobs.append(job)
        
        total_found += len(unique_jobs)
        print(f"  Unique jobs for {country_name}: {len(unique_jobs)}")

        # Score
        for job in unique_jobs:
            if job["url"] in notified_urls:
                continue
            total_scored += 1
            score = ats_score(
                job["title"], job["company"], job["location"], job["description"],
                job.get("job_level", ""), job.get("job_function", ""), job.get("company_industry", "")
            )
            job["score"] = score

            if score >= ATS_THRESHOLD:
                all_qualified.append(job)
            elif score >= 75:
                all_borderline.append(job)

    # Sort: priority countries first, then by score
    all_qualified.sort(key=lambda x: (x["country"] not in PREFERRED, -x["score"]))
    all_borderline.sort(key=lambda x: (x["country"] not in PREFERRED, -x["score"]))

    # Save results
    result_file = OUTPUT_DIR / f"qualified-jobs-{date_str}.md"
    with open(result_file, "w") as f:
        f.write(f"# Gulf Jobs Scanner v2 Results - {date_str}\n\n")
        f.write(f"**Run:** {ts}\n")
        f.write(f"**Total found:** {total_found}\n")
        f.write(f"**Scored:** {total_scored}\n")
        f.write(f"**Qualified (82+):** {len(all_qualified)}\n")
        f.write(f"**Borderline (75-81):** {len(all_borderline)}\n")
        f.write(f"**Errors:** {errors}\n\n")

        if all_qualified:
            f.write("## Qualified Jobs (82+)\n\n")
            for job in all_qualified:
                f.write(f"### {job['title']}\n")
                f.write(f"- **Company:** {job['company']}\n")
                f.write(f"- **Location:** {job['location']} ({job['country']})\n")
                f.write(f"- **ATS Score:** {job['score']}/100\n")
                f.write(f"- **Posted:** {job.get('date_posted', 'N/A')}\n")
                if job.get("salary_min"):
                    f.write(f"- **Salary:** {job['salary_min']} - {job.get('salary_max', 'N/A')}\n")
                f.write(f"- **Source:** {job['site']}\n")
                f.write(f"- **URL:** {job['url']}\n\n")

        if all_borderline:
            f.write("## Borderline Jobs (75-81)\n\n")
            for job in all_borderline:
                f.write(f"- {job['title']} at {job['company']} ({job['country']}) - Score: {job['score']} - {job['url']}\n")

    # Update notified
    if all_qualified:
        with open(NOTIFIED_FILE, "a") as f:
            f.write(f"\n### {date_str} - Scanner v2 Run\n")
            for job in all_qualified:
                f.write(f"- {job['score']}/100: {job['title']} at {job['company']} ({job['country']})\n")
                f.write(f"  {job['url']}\n")

    # Log
    log_file = OUTPUT_DIR / "cron-logs.md"
    with open(log_file, "a") as f:
        f.write(f"\n## {ts}\n")
        f.write(f"- Total found: {total_found}\n")
        f.write(f"- Scored: {total_scored}\n")
        f.write(f"- Qualified (82+): {len(all_qualified)}\n")
        f.write(f"- Borderline (75-81): {len(all_borderline)}\n")
        f.write(f"- Errors: {errors}\n")

    # Print summary for NASR to relay
    print(f"\n{'='*60}")
    print(f"SCAN COMPLETE")
    print(f"Total found: {total_found}")
    print(f"New scored: {total_scored}")
    print(f"Qualified (82+): {len(all_qualified)}")
    print(f"Borderline (75-81): {len(all_borderline)}")
    print(f"Errors: {errors}")
    
    if all_qualified:
        print(f"\n=== QUALIFIED JOBS ===")
        for job in all_qualified:
            priority = "🔥" if job["country"] in PREFERRED else "  "
            print(f"{priority} [{job['score']}] {job['title']} @ {job['company']} ({job['country']})")
            print(f"   {job['url']}")
    
    if all_borderline:
        print(f"\n=== BORDERLINE (75-81) ===")
        for job in all_borderline:
            print(f"   [{job['score']}] {job['title']} @ {job['company']} ({job['country']})")

    # Output JSON for easy parsing
    output = {
        "timestamp": ts,
        "total_found": total_found,
        "total_scored": total_scored,
        "qualified_count": len(all_qualified),
        "borderline_count": len(all_borderline),
        "errors": errors,
        "qualified": [{k: v for k, v in j.items() if k != "description"} for j in all_qualified],
        "borderline": [{k: v for k, v in j.items() if k != "description"} for j in all_borderline],
    }
    
    json_file = OUTPUT_DIR / f"scan-results-{date_str}.json"
    with open(json_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\nResults saved to: {result_file}")
    print(f"JSON saved to: {json_file}")


if __name__ == "__main__":
    main()
