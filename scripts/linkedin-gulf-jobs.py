#!/usr/bin/env python3
"""
LinkedIn Gulf Jobs Scanner v2.1 - Production-Ready (JobSpy Primary)
Spec: scripts/linkedin-gulf-jobs-cron-v2.1.md

Process:
 1. Load CV keywords from master-cv-data.md
 2. Check cookie age (warn if >30 days)
 3. Generate 120 combinations (20 titles x 6 countries)
 4. Search via JobSpy (returns full JD text) with 48h filter
 5. ATS score against full JD text
 6. Check duplicates (notified + applied)
 7. If qualified (82+): send to Slack #ai-jobs
 8. If 0 qualified: send summary to Slack (count + borderline)
 9. Runtime guard: 20 minutes max
"""

import os
import re
import json
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# ===================== CONFIGURATION =====================

COUNTRIES = [
    "Saudi Arabia",
    "United Arab Emirates",
    "Qatar",
    "Bahrain",
    "Kuwait",
    "Oman",
]

PREFERRED_COUNTRIES = ["Saudi Arabia", "United Arab Emirates"]

TITLES = [
    "Chief Digital Officer",
    "Chief Technology Officer",
    "Chief Information Officer",
    "VP Digital Transformation",
    "Director Digital Transformation",
    "Head of Digital Transformation",
    "Head of IT",
    "Head of Technology",
    "Director of Technology",
    "VP Technology",
    "VP IT",
    "Director of IT",
    "Senior Director Digital Transformation",
    "Head of Digital",
    "Director of Digital Innovation",
    "Head of Digital Innovation",
    "Program Director",
    "PMO Director",
    "Chief Strategy Officer",
    "Chief Operating Officer",
]

KEYWORDS = ["digital transformation", "AI", "PMO", "fintech", "healthtech", "e-commerce"]

# Paths
BASE_DIR = Path("/root/.openclaw/workspace")
OUTPUT_DIR = BASE_DIR / "jobs-bank" / "scraped"
LOG_FILE = OUTPUT_DIR / "cron-logs.md"
DETAILED_LOG = OUTPUT_DIR / "detailed-search-log.md"
NOTIFIED_FILE = OUTPUT_DIR / "notified-jobs.md"
APPLICATIONS_DIR = BASE_DIR / "jobs-bank" / "applications"
CV_FILE = BASE_DIR / "memory" / "master-cv-data.md"
COOKIES_FILE = BASE_DIR / "config" / "linkedin-cookies.json"
CONFIG_FILE = Path("/root/.openclaw/openclaw.json")

# Limits
ATS_THRESHOLD = 65
BORDERLINE_MIN = 55
AUTO_CV_THRESHOLD = 70
MAX_JOBS_PER_SEARCH = 5
MAX_RUNTIME_SECONDS = 20 * 60  # 20 minutes

# ===================== ATS SCORING (v2.1 exact points) =====================

KEYWORD_POINTS = {
    "digital transformation": 5,
    "pmo": 5,
    "project management": 4,
    "program management": 4,
    "portfolio management": 3,
    "ai": 3,
    "artificial intelligence": 3,
    "fintech": 3,
    "healthtech": 3,
    "e-commerce": 3,
    "pmp": 2,
    "csm": 2,
    "cspo": 2,
    "lean six sigma": 2,
    "cbap": 2,
    "20+ years": 3,
    "20 years": 3,
}

GROWTH_KEYWORDS = ["scale", "transformation", "optimization", "growth"]
GROWTH_POINTS = 3

PENALTY_NON_GCC = ["usa", "us ", "united states", "uk ", "united kingdom", "europe",
                    "america", "canada", "germany", "france", "india", "china", "australia"]
PENALTY_UNRELATED = ["beauty", "retail", "fashion", "restaurant", "hospitality",
                     "real estate agent", "construction", "facilities"]
PENALTY_DISGUISED = ["sales manager", "hr manager", "supply chain manager",
                     "sales director", "hr director", "supply chain director",
                     "account manager", "business development manager"]
PENALTY_CLEARANCE = ["security clearance", "top secret", "ts/sci", "secret clearance"]

# Title-based skip list (not executive DT roles)
SKIP_TITLES = [
    "marketing", "secretary", "facilitator", "sales", "recruiter", "recruiting",
    "hr ", "human resources", "supply chain", "logistics", "accountant", "accounting",
    "nurse", "doctor", "physician", "pharmacist", "teacher", "instructor",
    "beauty", "fashion", "retail", "restaurant", "hospitality", "real estate agent",
    "content creator", "social media", "graphic design", "copywriter",
    "developer", "engineer", "analyst", "coordinator", "specialist", "associate",
    "consultant", "advisor", "intern", "trainee", "assistant", "admin",
    "staffing", "talent acquisition",
]

GCC_MARKERS = ["saudi", "uae", "dubai", "riyadh", "jeddah", "qatar", "doha",
               "bahrain", "manama", "kuwait", "oman", "muscat", "gcc", "gulf",
               "abu dhabi", "sharjah", "dammam"]


def ats_score(jd_text, job_title="", job_location=""):
    """v4 Recalibrated: Balanced for DT exec + strategy/transformation roles in GCC."""
    text = f"{job_title} {job_location} {jd_text}".lower()
    title_lower = job_title.lower()
    
    # === SECTION 1: Role Alignment (40 max) ===
    role_score = 0
    
    # Executive level (0-15)
    if any(x in title_lower for x in ["chief", "cto", "cio", "cdo", "coo", "cso"]):
        role_score += 15
    elif any(x in title_lower for x in ["vp ", "vice president"]):
        role_score += 13
    elif "executive director" in title_lower:
        role_score += 12
    elif any(x in title_lower for x in ["director", "head of"]):
        role_score += 10
    
    # DT/Tech/Strategy in title (0-15)
    dt_title_scores = {
        "digital transformation": 10, "transformation": 6, "digital": 5,
        "technology": 6, "it ": 5, "information": 4, "innovation": 5,
        "smart city": 8, "iot": 5, "pmo": 7, "program": 4, "data": 4,
        "ai": 5, "strategy": 4, "operations": 3,
    }
    title_pts = sum(pts for kw, pts in dt_title_scores.items() if kw in title_lower)
    role_score += min(title_pts, 15)
    
    # DT/Tech/Strategy in JD (0-10)
    jd_keywords = [
        "digital transformation", "technology strategy", "it strategy",
        "enterprise architecture", "cloud", "agile", "devops", "data-driven",
        "automation", "digitization", "digitalization", "modernization",
        "system integration", "erp", "crm", "business intelligence",
        "saas", "microservices", "api", "infrastructure", "cybersecurity",
        "machine learning", "artificial intelligence", "analytics",
        "technology roadmap", "digital strategy", "it governance",
        "transformation", "change management", "operational excellence",
        "strategic planning", "kpi", "governance framework",
        "execution", "implementation", "performance management",
    ]
    jd_count = sum(1 for kw in jd_keywords if kw in text)
    role_score += min(jd_count * 1, 10)
    role_score = min(role_score, 40)
    
    # === SECTION 2: GCC Location (20 max) ===
    loc_score = 0
    if any(x in text for x in ["saudi", "riyadh", "jeddah", "jiddah", "dammam",
                                 "uae", "dubai", "abu dhabi", "sharjah"]):
        loc_score += 15
    elif any(x in text for x in ["qatar", "doha", "bahrain", "manama",
                                   "kuwait", "oman", "muscat"]):
        loc_score += 10
    if any(x in text for x in ["vision 2030", "saudi vision", "national transformation",
                                 "neom", "giga project", "pif"]):
        loc_score += 5
    loc_score = min(loc_score, 20)
    
    # === SECTION 3: Domain Fit (20 max) ===
    domain_score = 0
    if any(x in text for x in ["healthcare", "healthtech", "hospital", "medical", "clinical"]):
        domain_score += 8
    if any(x in text for x in ["fintech", "payments", "banking", "financial services"]):
        domain_score += 6
    if any(x in text for x in ["e-commerce", "ecommerce", "marketplace"]):
        domain_score += 6
    if any(x in text for x in ["pmo", "program management", "portfolio management", "project governance"]):
        domain_score += 6
    if any(x in text for x in ["multi-country", "multi-entity", "group-wide",
                                 "enterprise-wide", "multiple business", "multi-vertical",
                                 "budget", "p&l", "million", "large-scale"]):
        domain_score += 5
    if any(x in text for x in ["stakeholder management", "cross-functional",
                                 "c-suite", "board", "executive committee"]):
        domain_score += 4
    domain_score = min(domain_score, 20)
    
    # === SECTION 4: Experience Match (20 max) ===
    exp_score = 0
    if any(x in text for x in ["15 years", "15+ years", "20 years", "20+ years",
                                 "10+ years", "12+ years"]):
        exp_score += 7
    if any(x in text for x in ["team leadership", "direct reports", "lead team",
                                 "manage team", "senior leader"]):
        exp_score += 5
    certs = ["pmp", "csm", "cspo", "lean six sigma", "cbap", "prince2", "itil",
             "togaf", "safe", "agile"]
    cert_count = sum(1 for c in certs if c in text)
    exp_score += min(cert_count * 3, 8)
    exp_score = min(exp_score, 20)
    
    # === PENALTIES ===
    penalties = 0
    gcc = ["saudi", "uae", "dubai", "riyadh", "qatar", "bahrain", "kuwait", "oman", "gcc", "gulf"]
    non_gcc = ["usa", "united states", "uk ", "united kingdom", "europe", "canada", "india", "china"]
    if any(n in text for n in non_gcc) and not any(g in text for g in gcc):
        penalties += 25
    if any(u in text for u in ["beauty", "fashion", "restaurant", "hospitality"]):
        penalties += 15
    if any(d in title_lower for d in ["sales manager", "hr manager", "supply chain", "recruiter"]):
        penalties += 20
    if any(c in text for c in ["security clearance", "top secret"]):
        penalties += 30
    # Manufacturing/Industrial/Physical ops penalty (not Ahmed's domain)
    mfg_signals = ["manufacturing plant", "production line", "factory", "assembly line",
                    "warehouse manager", "plant manager", "plant operations",
                    "ehs ", "environment health safety", "ohsas", "lean manufacturing",
                    "mcb ", "pcba", "cnc ", "machining", "welding", "forklift",
                    "shop floor", "production supervisor", "quality inspector"]
    mfg_hits = sum(1 for s in mfg_signals if s in text)
    if mfg_hits >= 3:
        penalties += 20  # Strong manufacturing signal
    elif mfg_hits >= 1:
        penalties += 10  # Some manufacturing signal
    # Construction/Real estate/Facilities penalty
    if any(c in text for c in ["construction manager", "site engineer", "quantity surveyor",
                                "real estate broker", "property management"]):
        penalties += 15
    # Pure admin/support penalty
    if any(a in title_lower for a in ["admin manager", "office manager", "coordinator",
                                       "receptionist", "secretary", "clerk"]):
        penalties += 25
    
    total = role_score + loc_score + domain_score + exp_score - penalties
    return max(0, min(100, total))


# ===================== SEARCH (JobSpy PRIMARY) =====================

def search_jobspy(title, country):
    """PRIMARY: Search via JobSpy. Returns jobs with full JD text."""
    try:
        from jobspy import scrape_jobs
        results = scrape_jobs(
            site_name=["linkedin"],
            search_term=f"{title}",
            location=country,
            hours_old=48,
            results_wanted=MAX_JOBS_PER_SEARCH,
            linkedin_fetch_description=True,
        )

        jobs = []
        if results is not None and len(results) > 0:
            for _, row in results.iterrows():
                job_url = str(row.get("job_url", ""))
                jid_match = re.search(r'/jobs/view/(\d+)', job_url)
                jid = jid_match.group(1) if jid_match else str(abs(hash(job_url)))[:10]

                title_found = str(row.get("title", "")) if row.get("title") else title
                company_found = str(row.get("company", "")).strip() if row.get("company") else "Confidential"
                location_found = str(row.get("location", "")) if row.get("location") else country
                jd_text = str(row.get("description", "")).strip() if row.get("description") else ""
                salary_str = None
                if row.get("min_amount"):
                    salary_str = f"{row.get('min_amount')}-{row.get('max_amount', '?')} {row.get('currency', '')}"

                jobs.append({
                    "id": jid,
                    "url": job_url if job_url and "linkedin" in job_url else f"https://www.linkedin.com/jobs/view/{jid}",
                    "search_title": title,
                    "search_country": country,
                    "title": title_found,
                    "company": company_found,
                    "location": location_found,
                    "jd": jd_text,
                    "salary": salary_str,
                    "date_posted": str(row.get("date_posted", "")) if row.get("date_posted") else None,
                })

        return jobs[:MAX_JOBS_PER_SEARCH]

    except Exception as e:
        print(f"    JobSpy error: {e}")
        return []


def search_linkedin_fallback(title, country):
    """FALLBACK: Search LinkedIn directly if JobSpy fails."""
    keyword_str = " OR ".join([f'"{title}"'] + [f'"{k}"' for k in KEYWORDS[:3]])
    t = quote(keyword_str)
    c = quote(country)

    url = f"https://www.linkedin.com/jobs/search/?keywords={t}&location={c}&f_TPR=r172800&f_E=6&f_WT=1"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }

    jobs = []
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 429:
            time.sleep(30)
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 429:
                return []

        text = resp.text
        if "authwall" in text.lower() or "login" in resp.url.lower():
            return []

        job_ids = re.findall(r'data-entity-urn="urn:li:jobPosting:(\d+)"', text)
        if not job_ids:
            job_ids = re.findall(r'data-job-id=["\']?(\d+)', text)
        if not job_ids:
            job_ids = re.findall(r'/jobs/view/(\d+)', text)

        seen = set()
        for jid in job_ids:
            if jid not in seen and len(jobs) < MAX_JOBS_PER_SEARCH:
                seen.add(jid)
                jobs.append({
                    "id": jid,
                    "url": f"https://www.linkedin.com/jobs/view/{jid}",
                    "search_title": title,
                    "search_country": country,
                    "title": title,
                    "company": "Confidential",
                    "location": country,
                    "jd": "",  # No JD from fallback
                })
    except Exception as e:
        print(f"    LinkedIn fallback error: {e}")

    return jobs


# ===================== DEDUPLICATION =====================

def load_notified():
    if NOTIFIED_FILE.exists():
        return set(re.findall(r"(\d{8,})", NOTIFIED_FILE.read_text()))
    return set()


def load_applied():
    applied = set()
    if APPLICATIONS_DIR.exists():
        for f in APPLICATIONS_DIR.iterdir():
            if f.is_dir():
                applied.add(f.name.lower())
    return applied


def is_duplicate(job_id, company="", title=""):
    if job_id in _notified_cache:
        return True
    company_slug = re.sub(r"[^a-z0-9]", "-", company.lower()).strip("-")
    title_slug = re.sub(r"[^a-z0-9]", "-", title.lower()).strip("-")
    # Skip generic company names for matching
    skip_companies = {"confidential", "undisclosed", "company", "unknown"}
    for app in _applied_cache:
        if company_slug and len(company_slug) > 3 and company_slug not in skip_companies and company_slug in app:
            return True
        if title_slug and len(title_slug) > 10 and title_slug in app:
            return True
    return False


def save_notified(job):
    with open(NOTIFIED_FILE, "a") as f:
        f.write(f"\n- {job['id']}: {job.get('title','?')} at {job.get('company','?')} ({job.get('location','?')})")


# ===================== SLACK =====================

def get_slack_token():
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        return config.get("channels", {}).get("slack", {}).get("botToken", "")
    except Exception:
        return ""


def send_slack(text, channel="C0AJX895U3E"):
    import urllib.request
    import urllib.parse

    token = get_slack_token()
    if not token:
        print("  No Slack bot token found")
        return False

    url = "https://slack.com/api/chat.postMessage"
    data = urllib.parse.urlencode({
        "channel": channel,
        "text": text,
        "mrkdwn": "true",
    }).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            if result.get("ok"):
                print("  Slack notification sent")
                return True
            else:
                print(f"  Slack API error: {result.get('error', 'unknown')}")
    except Exception as e:
        print(f"  Slack send error: {e}")
    return False


def format_slack_message(qualified, borderline, stats):
    if not qualified:
        text = f"📊 *LinkedIn Gulf Jobs Scanner v2.1 - No Qualified Jobs*\n\n"
        text += f"Scanned {stats['searches']} searches | {stats['found']} jobs found | {stats['scored']} scored\n"
        text += f"Threshold: {ATS_THRESHOLD}+\n"
        if borderline:
            text += f"\n⚠️ {len(borderline)} borderline job(s) (75-81) logged for manual review."
        else:
            text += f"\nNo borderline jobs either. Market may be quiet today."
        return text

    sorted_jobs = sorted(
        qualified,
        key=lambda j: (j.get("location", "") not in PREFERRED_COUNTRIES, -j.get("score", 0)),
    )

    text = f"🎯 *LinkedIn Gulf Jobs Scanner v2.1 - {len(sorted_jobs)} Qualified Job(s)*\n\n"

    for job in sorted_jobs:
        notes = []
        loc = job.get("location", "")
        if any(p.lower() in loc.lower() for p in PREFERRED_COUNTRIES):
            notes.append("⭐ Priority")
        if job.get("vision_2030"):
            notes.append("🇸🇦 Vision 2030")
        if job.get("easy_apply"):
            notes.append("⚡ Easy Apply")
        if job.get("salary"):
            notes.append(f"💰 {job['salary']}")
        if job.get("hot"):
            notes.append("🔥 Hot")

        notes_str = " | ".join(notes) if notes else "-"

        text += f"*{job.get('title', '?')}*\n"
        text += f"   Company: {job.get('company', 'Confidential')}\n"
        text += f"   Location: {loc} | Score: {job['score']}/100\n"
        text += f"   Notes: {notes_str}\n"
        text += f"   Link: {job.get('url', '?')}\n\n"

    text += f"📊 Summary: {stats['searches']} searches | {stats['found']} jobs | {stats['scored']} scored | {len(qualified)} qualified"
    if borderline:
        text += f" | {len(borderline)} borderline"

    return text


# ===================== COOKIE CHECK =====================

def check_cookie_age():
    if not COOKIES_FILE.exists():
        print("  WARNING: No LinkedIn cookies file found")
        return False
    mtime = COOKIES_FILE.stat().st_mtime
    age_days = (time.time() - mtime) / 86400
    if age_days > 30:
        print(f"  WARNING: LinkedIn cookies are {int(age_days)} days old. May be stale.")
        return False
    print(f"  Cookies age: {int(age_days)} days (OK)")
    return True


# ===================== MAIN =====================

_notified_cache = set()
_applied_cache = set()



def trigger_auto_cv(job):
    """Auto-trigger CV tailoring for high-scoring jobs (80+)."""
    try:
        company_slug = job.get("company", "unknown").lower()
        company_slug = re.sub(r"[^a-z0-9]", "-", company_slug).strip("-")[:30]
        role_slug = job.get("title", "unknown").lower()
        role_slug = re.sub(r"[^a-z0-9]", "-", role_slug).strip("-")[:40]
        
        trigger_file = BASE_DIR / "jobs-bank" / "handoff" / f"{company_slug}-{role_slug}.trigger"
        trigger_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(trigger_file, "w") as f:
            f.write(f"NASR_REVIEW_NEEDED\n")
            f.write(f"Type: AUTO_CV_REQUEST\n")
            f.write(f"Score: {job.get('score', 0)}/100\n")
            f.write(f"Title: {job.get('title', 'Unknown')}\n")
            f.write(f"Company: {job.get('company', 'Confidential')}\n")
            f.write(f"Location: {job.get('location', 'GCC')}\n")
            f.write(f"URL: {job.get('url', '')}\n")
            f.write(f"JD Length: {job.get('jd_length', 0)} chars\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            if job.get('jd'):
                f.write(f"\n---JD---\n{job['jd'][:5000]}\n")
        
        print(f"    📋 CV trigger saved: {trigger_file.name}")
    except Exception as e:
        print(f"    ⚠️ CV trigger error: {e}")


def main():
    global _notified_cache, _applied_cache

    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"=== LinkedIn Gulf Jobs Scanner v2.1 (JobSpy Primary) ===")
    print(f"Started: {timestamp}")
    print(f"Countries: {len(COUNTRIES)} | Titles: {len(TITLES)} | Threshold: {ATS_THRESHOLD}+")

    # --- Step 1: Load CV ---
    if CV_FILE.exists():
        cv_text = CV_FILE.read_text().lower()
        print(f"  CV loaded: {len(cv_text)} chars")
    else:
        cv_text = ""
        print("  WARNING: CV file not found")

    # --- Step 2: Check cookie age ---
    check_cookie_age()

    # --- Load caches ---
    _notified_cache = load_notified()
    _applied_cache = load_applied()
    print(f"  Notified: {len(_notified_cache)} | Applied: {len(_applied_cache)}")

    # Counters
    total_searches = 0
    total_jobs_found = 0
    total_scored = 0
    qualified_jobs = []
    borderline_jobs = []
    errors = 0
    jobspy_failures = 0
    all_jobs_seen = set()  # Global dedup by job ID

    # Init detailed log
    with open(DETAILED_LOG, "a") as f:
        f.write(f"\n## Run: {timestamp}\n")

    # --- Main loop: 120 combinations ---
    for country in COUNTRIES:
        print(f"\n--- {country} ---")
        country_jobs = 0

        for title in TITLES:
            # Runtime guard
            elapsed = time.time() - start_time
            if elapsed > MAX_RUNTIME_SECONDS:
                print(f"\n⚠️ Runtime limit ({int(elapsed)}s). Stopping.")
                send_slack(
                    f"⚠️ Scanner hit 20-min limit. Partial: "
                    f"{total_searches}/120 searches. {len(qualified_jobs)} qualified."
                )
                break

            total_searches += 1

            # --- Search via JobSpy (primary) ---
            jobs = search_jobspy(title, country)

            # Fallback to LinkedIn HTTP if JobSpy fails
            if not jobs:
                jobspy_failures += 1
                jobs = search_linkedin_fallback(title, country)

            # Log
            with open(DETAILED_LOG, "a") as f:
                f.write(f"- {title} in {country}: {len(jobs)} jobs\n")

            if not jobs:
                time.sleep(0.5)
                continue

            total_jobs_found += len(jobs)
            country_jobs += len(jobs)
            print(f"  {title}: {len(jobs)} jobs")

            # --- Process each job ---
            for job in jobs:
                # Global dedup by ID
                if job["id"] in all_jobs_seen:
                    continue
                all_jobs_seen.add(job["id"])

                # Check notified + applied
                if is_duplicate(job["id"], job.get("company", ""), job.get("title", "")):
                    continue

                # Skip irrelevant titles
                title_lower = job.get("title", "").lower()
                skip = False
                for skip_word in SKIP_TITLES:
                    if skip_word in title_lower:
                        # Allow if title also has executive keywords
                        exec_words = ["chief", "vp ", "vice president", "director", "head of", "cto", "cio", "cdo", "coo", "cso"]
                        has_exec = any(e in title_lower for e in exec_words)
                        if not has_exec:
                            skip = True
                            break
                if skip:
                    continue

                # Get JD text
                jd_text = job.get("jd", "")
                has_full_jd = len(jd_text) > 100

                # ATS score against FULL JD text
                score = ats_score(jd_text, job["title"], job["location"])
                job["score"] = score
                job["jd_length"] = len(jd_text)
                job["has_full_jd"] = has_full_jd
                total_scored += 1

                # Enrichment flags
                jd_lower = jd_text.lower() if jd_text else ""
                job["vision_2030"] = "vision 2030" in jd_lower or "saudi vision" in jd_lower
                job["easy_apply"] = "easy apply" in jd_lower
                job["hot"] = False
                if job.get("date_posted"):
                    try:
                        from datetime import timedelta
                        posted = datetime.strptime(str(job["date_posted"])[:10], "%Y-%m-%d")
                        if (datetime.now() - posted) < timedelta(hours=6):
                            job["hot"] = True
                    except Exception:
                        pass

                # Classify
                if score >= ATS_THRESHOLD:
                    qualified_jobs.append(job)
                    save_notified(job)
                    if score >= AUTO_CV_THRESHOLD:
                        print(f"    🎯 AUTO-CV: {job['title']} at {job['company']} ({score}/100) [JD: {len(jd_text)} chars]")
                        trigger_auto_cv(job)
                    else:
                        print(f"    ✅ QUALIFIED: {job['title']} at {job['company']} ({score}/100) [JD: {len(jd_text)} chars]")
                elif score >= BORDERLINE_MIN:
                    borderline_jobs.append(job)
                    print(f"    ⚠️ Borderline: {job['title']} at {job['company']} ({score}/100)")

            time.sleep(1)  # Rate limit

        # Runtime check after each country
        if time.time() - start_time > MAX_RUNTIME_SECONDS:
            break

        with open(DETAILED_LOG, "a") as f:
            f.write(f"\n**{country}:** {country_jobs} jobs\n")

    # --- Save report ---
    qualified_file = str(OUTPUT_DIR / f"qualified-jobs-{date_str}.md")
    with open(qualified_file, "w") as f:
        f.write(f"# LinkedIn Gulf Jobs Scanner v2.1 - Report\n\n")
        f.write(f"**Date:** {date_str}\n")
        f.write(f"**Engine:** JobSpy (full JD text)\n")
        f.write(f"**Threshold:** ATS {ATS_THRESHOLD}+\n")
        f.write(f"**Qualified:** {len(qualified_jobs)}\n")
        f.write(f"**Borderline ({BORDERLINE_MIN}-{ATS_THRESHOLD-1}):** {len(borderline_jobs)}\n\n")

        if qualified_jobs:
            f.write(f"## Qualified Jobs ({ATS_THRESHOLD}+)\n\n")
            for job in qualified_jobs:
                notes = []
                if any(p.lower() in job["location"].lower() for p in PREFERRED_COUNTRIES):
                    notes.append("Saudi/UAE Priority")
                if job.get("vision_2030"):
                    notes.append("Vision 2030")
                if job.get("salary"):
                    notes.append(f"Salary: {job['salary']}")
                f.write(f"### {job['title']}\n")
                f.write(f"- Company: {job['company']}\n")
                f.write(f"- Location: {job['location']}\n")
                f.write(f"- Score: {job['score']}/100\n")
                f.write(f"- URL: {job['url']}\n")
                if notes:
                    f.write(f"- Notes: {', '.join(notes)}\n")
                f.write(f"- JD: {job.get('jd_length', 0)} chars ({'full' if job.get('has_full_jd') else 'partial'})\n\n")

        if borderline_jobs:
            f.write(f"## Borderline Jobs ({BORDERLINE_MIN}-{ATS_THRESHOLD-1}) - Manual Review\n\n")
            for job in borderline_jobs:
                f.write(f"### {job['title']}\n")
                f.write(f"- Company: {job['company']}\n")
                f.write(f"- Location: {job['location']}\n")
                f.write(f"- Score: {job['score']}/100\n")
                f.write(f"- URL: {job['url']}\n\n")

    # --- Slack ---
    stats = {"searches": total_searches, "found": total_jobs_found, "scored": total_scored}
    slack_msg = format_slack_message(qualified_jobs, borderline_jobs, stats)
    if slack_msg:
        send_slack(slack_msg)

    # --- Cron log ---
    elapsed = int(time.time() - start_time)
    with open(LOG_FILE, "a") as f:
        f.write(f"\n## {timestamp}\n")
        f.write(f"- Version: v2.1 (JobSpy primary)\n")
        f.write(f"- Searches: {total_searches}\n")
        f.write(f"- Jobs found: {total_jobs_found}\n")
        f.write(f"- Unique jobs: {len(all_jobs_seen)}\n")
        f.write(f"- Scored: {total_scored}\n")
        f.write(f"- Qualified ({ATS_THRESHOLD}+): {len(qualified_jobs)}\n")
        f.write(f"- Borderline ({BORDERLINE_MIN}-{ATS_THRESHOLD-1}): {len(borderline_jobs)}\n")
        f.write(f"- Errors: {errors}\n")
        f.write(f"- Runtime: {elapsed}s\n")
        f.write(f"- JobSpy failures: {jobspy_failures}\n")

    # --- Summary ---
    print(f"\n=== DONE ({elapsed}s) ===")
    print(f"Searches: {total_searches}")
    print(f"Jobs found: {total_jobs_found}")
    print(f"Unique: {len(all_jobs_seen)}")
    print(f"Scored: {total_scored}")
    print(f"Qualified ({ATS_THRESHOLD}+): {len(qualified_jobs)}")
    print(f"Borderline ({BORDERLINE_MIN}-{ATS_THRESHOLD-1}): {len(borderline_jobs)}")
    print(f"Output: {qualified_file}")


if __name__ == "__main__":
    main()
