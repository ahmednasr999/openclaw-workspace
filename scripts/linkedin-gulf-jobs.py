#!/usr/bin/env python3
"""
LinkedIn Gulf Jobs Scanner v3.0 - Fast Title Filter
====================================================
Strategy:
  - Fast search: LinkedIn + Indeed, NO JD fetch (no rate limiting)
  - Filter by: executive title + GCC location + DT/Tech domain
  - Output: "Radar Picks" - relevant leads surfaced for review
  - ATS scoring against full JD happens at apply time (not here)
  - Runs in < 5 minutes for all searches

ATS_THRESHOLD (82) is applied ONLY when full JD is available.
Title-only pass surfaces leads - Ahmed decides which to pursue.
"""

import os, re, json, time
from datetime import datetime
from pathlib import Path

# ===================== CONFIGURATION =====================

# 3 priority + 3 secondary countries
GCC_COUNTRIES = [
    "United Arab Emirates",
    "Saudi Arabia",
    "Qatar",
    "Bahrain",
    "Kuwait",
    "Oman",
]

# All potential executive titles - searched across ALL GCC countries
ALL_TITLES = [
    # Digital Transformation
    "VP Digital Transformation",
    "Director Digital Transformation",
    "Head of Digital Transformation",
    "Senior Director Digital Transformation",
    "Chief Digital Officer",
    # Technology Leadership
    "Chief Technology Officer",
    "Chief Information Officer",
    "Head of Technology",
    "VP Technology",
    "Director of Technology",
    "Head of IT",
    "VP Engineering",
    "Director of Engineering",
    # Executive / C-Suite
    "Chief Operating Officer",
    "Chief Strategy Officer",
    "Chief Product Officer",
    # PMO / Program
    "PMO Director",
    "Program Director",
    "Head of PMO",
    # Transformation / Innovation
    "Head of Transformation",
    "Director of Innovation",
    "VP Operations",
]

# Legacy aliases for backward compatibility
PRIORITY_COUNTRIES = GCC_COUNTRIES[:3]
SECONDARY_COUNTRIES = GCC_COUNTRIES[3:]
PRIMARY_TITLES = ALL_TITLES[:10]
SECONDARY_TITLES = ALL_TITLES[10:15]

PREFERRED_COUNTRIES = ["Saudi Arabia", "United Arab Emirates"]

# Paths
BASE_DIR       = Path("/root/.openclaw/workspace")
OUTPUT_DIR     = BASE_DIR / "jobs-bank" / "scraped"
LOG_FILE       = OUTPUT_DIR / "cron-logs.md"
DETAILED_LOG   = OUTPUT_DIR / "detailed-search-log.md"
NOTIFIED_FILE  = OUTPUT_DIR / "notified-jobs.md"
FILTERED_LOG   = OUTPUT_DIR / "filtered-out-jobs.md"  # v3.1: audit trail for discarded jobs
APPLIED_DIR    = BASE_DIR / "jobs-bank" / "applications"
PIPELINE_FILE  = BASE_DIR / "jobs-bank" / "pipeline.md"
CONFIG_FILE    = Path("/root/.openclaw/openclaw.json")

MAX_JOBS_PER_SEARCH  = 10
MAX_RUNTIME_SECONDS  = 25 * 60   # 25 minutes (138 searches × 5s delay + backoffs)
SEARCH_DELAY         = 5         # seconds between searches (increased for 138 combos)
MIN_JOBS_ALERT       = 10        # alert if fewer total jobs found
ATS_THRESHOLD        = 65        # minimum ATS score to include in picks

# Ahmed's CV keywords for ATS scoring (from master-cv-data.md)
ATS_KEYWORDS = {
    # Core skills (weight 3)
    "digital transformation": 3, "pmo": 3, "program management": 3,
    "project management": 3, "agile": 3, "strategic planning": 3,
    "operational excellence": 3, "change management": 3, "stakeholder management": 3,
    "cross-functional": 3, "p&l": 3,
    # Domain (weight 2)
    "healthtech": 2, "healthcare": 2, "fintech": 2, "e-commerce": 2,
    "payments": 2, "mobile": 2, "saas": 2, "ai": 2, "data analytics": 2,
    "cloud": 2, "emr": 2, "telemedicine": 2, "cybersecurity": 2,
    "infrastructure": 2, "enterprise": 2, "crm": 2, "salesforce": 2,
    # Leadership (weight 2)
    "c-suite": 2, "executive": 2, "director": 2, "vp": 2, "head of": 2,
    "leadership": 2, "team building": 2, "scaling": 2, "growth": 2,
    # Geography (weight 1)
    "gcc": 1, "uae": 1, "saudi": 1, "dubai": 1, "middle east": 1,
    "mena": 1, "egypt": 1, "riyadh": 1, "ksa": 1,
    # Certifications (weight 1)
    "pmp": 1, "scrum": 1, "lean six sigma": 1, "itil": 1, "cbap": 1,
    # Tech (weight 1)
    "lte": 1, "4g": 1, "api": 1, "microservices": 1, "devops": 1,
    "automation": 1, "integration": 1, "architecture": 1, "platform": 1,
}

# Title filter: must match executive level
EXEC_WORDS = ["chief","ceo","cto","cio","cdo","coo","cso","cfo","cmo","cro",
              "vp ","vice president",
              "director","head of","svp","senior director","managing director",
              "executive director","program director","principal"]

# Domain filter: must relate to DT/Tech/PMO (balanced)
DOMAIN_WORDS = ["digital","technology","it ","information","pmo","program","project",
                "transformation","innovation","ai","data","strategy","cyber",
                "cloud","operations","infrastructure","engineering","tech",
                "ict ","software","systems"]

# Hard skip: clearly irrelevant (non-tech executive roles)
SKIP_WORDS = ["sales","marketing","hr ","human resources","recruit","account executive",
              "accountant","beauty","fashion","restaurant","hospitality","nurse",
              "doctor","physician","clinical","dental","chef","food","beverage",
              "real estate","broker","supply chain","logistics","secretary",
              "coordinator","specialist","intern","trainee","assistant","admin",
              "recruiter","talent acquisition","web3","crypto","blockchain",
              # Non-tech executive roles to skip
              "fundraising","cfo ","finance ","financial","budget","residences",
              "housing","construction","facility","procurement","legal","compliance",
              "risk ","audit","investment","partnerships","education","academic",
              "medical","healthcare","patient","hospital","content ","creative",
              "communications","pr ","public relations","social media"]

# ===================== FILTER =====================

def is_relevant(title, location=""):
    """Three-criteria filter: executive + domain + not irrelevant."""
    t = title.lower()
    loc = location.lower()

    # 1. Must have executive keyword
    if not any(w in t for w in EXEC_WORDS):
        return False, "not-exec"

    # 2. Must relate to DT/Tech/PMO OR location is GCC (broad exec catch)
    gcc = any(w in loc for w in ["saudi","uae","united arab emirates","dubai",
                                  "riyadh","qatar","doha","bahrain","kuwait",
                                  "oman","abu dhabi","jeddah","dammam","sharjah",
                                  "ajman","muscat"])
    domain_match = any(w in t for w in DOMAIN_WORDS)
    if not domain_match and not gcc:
        return False, "no-domain"

    # 3. Must not be in hard skip list
    for skip in SKIP_WORDS:
        if skip in t:
            # Allow only if title ALSO has strong exec+domain combo
            strong_exec = any(w in t for w in ["chief","vp ","vice president","cto","cio","cdo"])
            strong_domain = any(w in t for w in ["digital","technology","pmo","transformation"])
            if not (strong_exec and strong_domain):
                return False, "skip-word"

    return True, "ok"


def is_priority(title, location):
    """Is this a priority role? ANY 2 of 3 criteria: C-suite title + GCC location + DT sector.
    
    Changed Mar 17, 2026: triple-AND was too strict. A COO in Dubai shouldn't need 
    "digital transformation" in the title to be flagged as priority. Most GCC JDs 
    don't include DT keywords in the title even when the role IS digital transformation.
    """
    t = title.lower()
    loc = location.lower()
    # Exclusion: roles that contain executive-sounding words but aren't relevant
    exclude_roles = ["accountant","accounting","fire & life","fire safety","fitout",
                     "fit-out","interior","architect","civil","mechanical","electrical",
                     "structural","nurse","nursing","medical director","clinical",
                     "executive assistant","personal assistant","secretary",
                     "chef","culinary","hospitality manager","hotel manager",
                     "sales director","sales manager","talent director",
                     "culture director","hr director","recruitment"]
    if any(x in t for x in exclude_roles):
        return False
    
    is_csuite = any(w in t for w in ["chief","cto","cio","cdo","coo","cmo","cfo",
                                      "vp ","vice president","head of technology",
                                      "head of digital","head of it","head of data",
                                      "head of product","head of engineering",
                                      "managing director","general manager","gm ",
                                      "director of technology","director of digital",
                                      "director of it","director of engineering",
                                      "director of product","director of data",
                                      "director of pmo","director of transformation",
                                      "director of operations","project director"])
    is_dt = any(w in t for w in ["digital","transformation","technology","pmo",
                                  "data","ai ","artificial","automation","it ",
                                  "information","software","engineering","product",
                                  "platform","cloud","cyber","innovation"])
    is_top_gcc = any(w in loc for w in ["saudi","uae","dubai","riyadh","abu dhabi",
                                         "jeddah","doha","qatar","bahrain","kuwait",
                                         "oman","muscat"])
    
    # ANY 2 of 3 = priority pick
    score = sum([is_csuite, is_dt, is_top_gcc])
    return score >= 2

# ===================== DEDUP =====================

def load_notified():
    if NOTIFIED_FILE.exists():
        return set(re.findall(r"(\d{8,})", NOTIFIED_FILE.read_text()))
    return set()

def load_applied():
    s = set()
    if APPLIED_DIR.exists():
        for f in APPLIED_DIR.iterdir():
            if f.is_dir(): s.add(f.name.lower())
    return s

def load_pipeline():
    companies = set()
    # Non-company entries to skip from pipeline matching
    skip_entries = {"company","none","date","applied","new","confidential",
                    "target salary","total tracked","active interviews",
                    "avg ats score (all cvs)","radar (no cv yet)",
                    "day 30 cold","discovered mena","chief operating officer",
                    "all feb 27 batch"}
    try:
        with open(PIPELINE_FILE) as f:
            for line in f:
                m = re.search(r'\|\s*(?:☑️|~~)?\s*([A-Za-z][A-Za-z0-9\s&\(\)\.]+?)\s*(?:~~)?\s*\|', line)
                if m:
                    c = m.group(1).strip().lower()
                    if c and c not in skip_entries and len(c) > 3:
                        companies.add(c)
    except FileNotFoundError:
        pass
    return companies

def is_duplicate(jid, company=""):
    if jid in _notified:
        return True
    slug = re.sub(r"[^a-z0-9]", "-", company.lower()).strip("-")
    # Skip generic/ambiguous company names for dedup
    skip = {"confidential","undisclosed","company","unknown","nan",
            "confidential-careers","new","applied","date","active-interviews",
            "target-salary","total-tracked","radar-no-cv-yet"}
    if slug and len(slug) > 5 and slug not in skip:
        # Exact match against applied dirs
        for app in _applied:
            if slug == app or (len(slug) > 8 and slug in app) or (len(app) > 8 and app in slug):
                return True
        # Stricter pipeline match: require longer strings to avoid false positives
        for pc in _pipeline:
            if len(pc) < 5:
                continue  # skip short pipeline entries like "new", "du", "fab"
            if pc == slug:
                return True
            # Only do substring match if both are reasonably long
            if len(pc) > 8 and len(slug) > 8:
                if pc in slug or slug in pc:
                    return True
    return False

def save_notified(job):
    with open(NOTIFIED_FILE, "a") as f:
        f.write(f"\n- {job['id']}: {job['title']} at {job['company']} ({job['location']})")

# ===================== GOOGLE JOBS (via Playwright) =====================

def scrape_google_jobs(search_term, location, max_results=10):
    """Scrape Google Jobs using Playwright headless browser."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  Google Jobs: playwright not installed")
        return []

    jobs = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
                locale="en-US",
            )
            page = context.new_page()

            query = f"{search_term} {location} jobs"
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}&udm=8&hl=en&gl=ae"

            page.goto(url, timeout=15000)
            page.wait_for_timeout(3000)

            # Handle consent page
            content = page.content()
            if "consent" in content.lower() or "accepter" in content.lower():
                for b in page.query_selector_all('button'):
                    t = b.inner_text().lower()
                    if "accept" in t or "accepter" in t or "tout" in t:
                        b.click()
                        page.wait_for_timeout(2000)
                        break
                page.goto(url, timeout=15000)
                page.wait_for_timeout(5000)

            body_text = page.query_selector('body').inner_text() if page.query_selector('body') else ""

            if "unusual traffic" in body_text:
                browser.close()
                return []

            # Parse job listings from visible text
            lines = [l.strip() for l in body_text.split('\n') if l.strip()]
            skip_words = ['sign in', 'accessibility', 'filters', 'search results', 'date posted',
                          'job type', 'follow', 'job postings', 'saved jobs', 'following',
                          'results for', 'choose area', 'skip to', 'feedback',
                          'all', 'news', 'images', 'forums', 'short videos', 'web', 'more', 'tools', 'jobs']

            i = 0
            while i < len(lines) and len(jobs) < max_results:
                line = lines[i]
                if any(skip in line.lower() for skip in skip_words) and len(line) < 30:
                    i += 1
                    continue

                if i + 2 < len(lines) and '•' in lines[i+2] and 'via' in lines[i+2].lower():
                    title = lines[i]
                    company = lines[i+1]
                    loc_via = lines[i+2]

                    parts = loc_via.split('•')
                    job_loc = parts[0].strip() if parts else ""
                    source = ""
                    if len(parts) > 1:
                        via_match = re.search(r'via\s+(.+)', parts[1], re.IGNORECASE)
                        if via_match:
                            source = via_match.group(1).strip()

                    if len(title) > 5 and len(company) > 2:
                        jid = str(abs(hash(f"{title}{company}")))[:10]
                        jobs.append({
                            "id": jid,
                            "title": title,
                            "company": company,
                            "location": job_loc or location,
                            "site": "google",
                            "source_via": source,
                            "url": f"https://www.google.com/search?q={(title+' '+company).replace(' ', '+')}&udm=8&hl=en",
                            "search_country": location,
                            "search_title": search_term,
                        })
                    i += 3
                else:
                    i += 1

            browser.close()
    except Exception as e:
        print(f"  Google Jobs error: {e}")

    return jobs


# ===================== JD FETCH & ATS SCORING =====================

def fetch_jd(url, site="linkedin"):
    """Fetch full job description from LinkedIn or Indeed URL."""
    try:
        import urllib.request, ssl
        ctx = ssl.create_default_context()
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")

        # Extract job description text from HTML
        # LinkedIn: look for description section
        jd_text = ""

        # Try common patterns
        import re as _re

        # LinkedIn pattern: description in a specific div or section
        patterns = [
            r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
            r'"description"\s*:\s*"(.*?)"',
            r'<section[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</section>',
        ]

        for pat in patterns:
            m = _re.search(pat, html, _re.DOTALL | _re.IGNORECASE)
            if m:
                jd_text = m.group(1)
                break

        if not jd_text:
            # Fallback: extract all visible text between body tags
            body_match = _re.search(r'<body[^>]*>(.*?)</body>', html, _re.DOTALL | _re.IGNORECASE)
            if body_match:
                jd_text = body_match.group(1)

        # Clean HTML tags
        jd_text = _re.sub(r'<[^>]+>', ' ', jd_text)
        jd_text = _re.sub(r'&[a-z]+;', ' ', jd_text)
        jd_text = _re.sub(r'\s+', ' ', jd_text).strip()

        # Limit to reasonable length
        return jd_text[:5000] if len(jd_text) > 100 else ""

    except Exception as e:
        return ""


def fetch_jd_jobspy(url, site="linkedin"):
    """Fetch JD using jobspy with description enabled (more reliable than raw HTTP)."""
    try:
        from jobspy import scrape_jobs
        # Extract job ID from URL
        m = re.search(r'/jobs/view/(\d+)', url)
        if not m:
            return ""

        job_id = m.group(1)
        # Re-scrape with description enabled
        results = scrape_jobs(
            site_name=[site if site != "unknown" else "linkedin"],
            search_term="",
            location="",
            results_wanted=1,
            linkedin_fetch_description=True,
            job_url=url,
        )
        if results is not None and len(results) > 0:
            desc = str(results.iloc[0].get("description", ""))
            if desc and desc != "nan":
                return desc[:5000]
    except:
        pass
    return ""


def score_ats(jd_text, title=""):
    """Score a job description against Ahmed's CV keywords. Returns 0-100."""
    if not jd_text and not title:
        return 0, []

    text = (jd_text + " " + title).lower()
    matched = []
    total_weight = 0
    max_possible = sum(ATS_KEYWORDS.values())

    for keyword, weight in ATS_KEYWORDS.items():
        if keyword in text:
            matched.append(keyword)
            total_weight += weight

    # A weight of 30+ = near-perfect match for Ahmed's profile
    # 25+ = strong (75%+), 15-24 = moderate (50-74%), <15 = weak
    score = min(100, int(total_weight / 30 * 100))

    return score, matched


def enrich_picks_with_jd(picks):
    """Fetch JDs and score ATS for priority picks. Returns enriched list."""
    enriched = []
    total = len(picks)
    fetched = 0
    scored = 0

    print(f"\n  Enriching {total} picks with JD + ATS scoring...")

    for i, job in enumerate(picks):
        url = job.get("url", "")
        site = job.get("site", "linkedin")

        # Try fetching JD
        jd = ""
        if url:
            jd = fetch_jd(url, site)
            if jd:
                fetched += 1
            time.sleep(1)  # Rate limit between fetches

        # Score ATS
        ats_score, matched_keywords = score_ats(jd, job.get("title", ""))
        job["jd_text"] = jd[:2000] if jd else ""
        job["jd_fetched"] = bool(jd)
        job["ats_score"] = ats_score
        job["ats_keywords"] = matched_keywords
        scored += 1

        if (i + 1) % 5 == 0:
            print(f"    Progress: {i+1}/{total} (fetched: {fetched}, scored: {scored})")

        enriched.append(job)

    # Sort by ATS score descending
    enriched.sort(key=lambda x: x.get("ats_score", 0), reverse=True)

    print(f"  Enrichment done: {fetched}/{total} JDs fetched, {scored} scored")

    # Cache JDs to disk for CV builder
    today_str = time.strftime("%Y-%m-%d")
    jd_cache_file = f"{WORKSPACE}/jobs-bank/scraped/jd-cache-{today_str}.json"
    jd_cache = {}
    for job in enriched:
        if job.get("jd_text"):
            jd_cache[job.get("url", "")] = {
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "jd_text": job["jd_text"],
                "ats_score": job.get("ats_score", 0),
                "ats_keywords": job.get("ats_keywords", []),
            }
    with open(jd_cache_file, "w") as f:
        json.dump(jd_cache, f, indent=2)
    print(f"  JD cache saved: {len(jd_cache)} JDs → {jd_cache_file}")

    # Apply semantic career-fit filter
    for job in enriched:
        verdict, fit_score, reason = semantic_fit_filter(job)
        job["career_verdict"] = verdict
        job["career_fit"] = fit_score
        job["career_reason"] = reason

    apply_count = sum(1 for j in enriched if j["career_verdict"] == "APPLY")
    skip_count = sum(1 for j in enriched if j["career_verdict"] == "SKIP")
    stretch_count = sum(1 for j in enriched if j["career_verdict"] == "STRETCH")
    print(f"  Career fit: {apply_count} APPLY, {skip_count} SKIP, {stretch_count} STRETCH")

    return enriched


# ===================== SEARCH =====================

def search(title, country):
    """Fast search: no JD fetch, LinkedIn + Indeed."""
    try:
        from jobspy import scrape_jobs
        # Load LinkedIn cookie from file
        _li_at = None
        for _cpath in ["/root/.openclaw/cookies/linkedin.txt", "/root/.openclaw/workspace/config/nasr-linkedin-cookies.txt"]:
            try:
                _txt = open(_cpath).read()
                import re as _re
                _m = _re.search(r'li_at\s+(\S+)', _txt)
                if _m:
                    _li_at = _m.group(1)
                    break
            except:
                pass

        # Indeed needs full country name (not code)
        INDEED_COUNTRY_MAP = {
            "United Arab Emirates": "united arab emirates",
            "Saudi Arabia": "saudi arabia",
            "Qatar": "qatar",
            "Bahrain": "bahrain",
            "Kuwait": "kuwait",
            "Oman": "oman",
        }
        indeed_country = INDEED_COUNTRY_MAP.get(country, country.lower())

        results = scrape_jobs(
            site_name=["linkedin", "indeed"],
            search_term=title,
            location=country,
            country_indeed=indeed_country,
            hours_old=72,
            results_wanted=MAX_JOBS_PER_SEARCH,
            linkedin_fetch_description=False,
            **({"linkedin_cookie": _li_at} if _li_at else {}),
        )
        jobs = []
        if results is not None and len(results) > 0:
            for _, row in results.iterrows():
                nan = lambda v: str(v) == "nan" or v is None
                url = str(row.get("job_url",""))
                m = re.search(r'/jobs/view/(\d+)', url)
                jid = m.group(1) if m else str(abs(hash(url)))[:10]
                jobs.append({
                    "id":       jid,
                    "url":      url if "linkedin" in url or "indeed" in url else f"https://www.linkedin.com/jobs/view/{jid}",
                    "title":    str(row.get("title","")) if not nan(row.get("title")) else title,
                    "company":  str(row.get("company","")).strip() if not nan(row.get("company")) else "Confidential",
                    "location": str(row.get("location","")) if not nan(row.get("location")) else country,
                    "site":     str(row.get("site","")) if not nan(row.get("site")) else "unknown",
                    "date_posted": str(row.get("date_posted",""))[:10] if not nan(row.get("date_posted")) else "",
                    "job_type":    str(row.get("job_type","")) if not nan(row.get("job_type")) else "",
                    "job_level":   str(row.get("job_level","")) if not nan(row.get("job_level")) else "",
                    "job_function": str(row.get("job_function","")) if not nan(row.get("job_function")) else "",
                    "company_industry": str(row.get("company_industry","")) if not nan(row.get("company_industry")) else "",
                    "is_remote":   str(row.get("is_remote","")) if not nan(row.get("is_remote")) else "",
                    "company_url": str(row.get("company_url","")) if not nan(row.get("company_url")) else "",
                    "min_salary":  str(row.get("min_amount","")) if not nan(row.get("min_amount")) else "",
                    "max_salary":  str(row.get("max_amount","")) if not nan(row.get("max_amount")) else "",
                    "currency":    str(row.get("currency","")) if not nan(row.get("currency")) else "",
                    "search_country": country,
                    "search_title":   title,
                })
        return jobs
    except Exception as e:
        print(f"    Search error: {e}")
        return []

# ===================== SLACK =====================

def get_slack_token():
    try:
        with open(CONFIG_FILE) as f: config = json.load(f)
        return config.get("channels",{}).get("slack",{}).get("botToken","")
    except: return ""

def send_slack(text, channel="C0AJX895U3E"):
    import urllib.request, urllib.parse
    token = get_slack_token()
    if not token: return False
    data = urllib.parse.urlencode({"channel":channel,"text":text,"mrkdwn":"true"}).encode()
    req = urllib.request.Request("https://slack.com/api/chat.postMessage", data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            if result.get("ok"): print("  Slack sent"); return True
    except Exception as e:
        print(f"  Slack error: {e}")
    return False

# ===================== AUTO CV TRIGGER =====================

def trigger_auto_cv(job):
    try:
        cs = re.sub(r"[^a-z0-9]","-", job.get("company","unknown").lower()).strip("-")[:30]
        rs = re.sub(r"[^a-z0-9]","-", job.get("title","unknown").lower()).strip("-")[:40]
        tf = BASE_DIR / "jobs-bank" / "handoff" / f"{cs}-{rs}.trigger"
        tf.parent.mkdir(parents=True, exist_ok=True)
        with open(tf,"w") as f:
            f.write(f"NASR_REVIEW_NEEDED\nType: AUTO_CV_REQUEST\nTitle: {job['title']}\n"
                    f"Company: {job['company']}\nLocation: {job['location']}\n"
                    f"URL: {job['url']}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        print(f"    CV trigger: {tf.name}")
    except Exception as e:
        print(f"    Trigger error: {e}")

# ===================== MAIN =====================

_notified = set()
_applied  = set()
_pipeline = set()

def main():
    global _notified, _applied, _pipeline

    start = time.time()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"=== LinkedIn Gulf Jobs Scanner v3.1 ===")
    print(f"Started: {ts}")

    _notified = load_notified()
    _applied  = load_applied()
    _pipeline = load_pipeline()
    print(f"Cache: {len(_notified)} notified | {len(_applied)} applied | {len(_pipeline)} pipeline")

    # Build search plan
    searches = []
    for c in GCC_COUNTRIES:
        for t in ALL_TITLES:
            searches.append((t, c))

    print(f"Search plan: {len(searches)} combinations | Delay: {SEARCH_DELAY}s between searches")

    total_searches = 0
    total_found    = 0
    seen           = set()
    picks          = []    # priority picks (C-suite + UAE/Saudi + DT)
    leads          = []    # other relevant leads
    filtered_out   = []    # v3.1: jobs that didn't pass filters (audit trail)

    with open(DETAILED_LOG, "a") as f:
        f.write(f"\n## Run: {ts} (v3.0)\n")

    consecutive_errors = 0
    for title, country in searches:
        if time.time() - start > MAX_RUNTIME_SECONDS:
            print(f"  Runtime limit reached. Stopping.")
            break

        # Backoff on consecutive errors (Google 429 rate limiting)
        if consecutive_errors >= 5:
            backoff = min(60, consecutive_errors * 5)
            print(f"  Rate limited ({consecutive_errors} consecutive errors). Backing off {backoff}s...")
            time.sleep(backoff)
            consecutive_errors = 0  # Reset after backoff

        total_searches += 1
        jobs = search(title, country)

        with open(DETAILED_LOG, "a") as f:
            f.write(f"- {title} in {country}: {len(jobs)} jobs\n")

        if not jobs:
            consecutive_errors += 1
            time.sleep(1)
            continue

        consecutive_errors = 0  # Reset on success
        total_found += len(jobs)

        for job in jobs:
            if job["id"] in seen:
                continue
            seen.add(job["id"])

            if is_duplicate(job["id"], job.get("company","")):
                filtered_out.append({**job, "filter_reason": "duplicate"})
                continue

            relevant, reason = is_relevant(job["title"], job["location"])
            if not relevant:
                filtered_out.append({**job, "filter_reason": reason})
                continue

            save_notified(job)

            if is_priority(job["title"], job["location"]):
                picks.append(job)
                print(f"  PICK: {job['title']} | {job['company']} | {job['location']}")
            else:
                leads.append(job)
                print(f"  Lead: {job['title']} | {job['company']} | {job['location']}")

        if total_searches % 10 == 0:
            print(f"  Progress: {total_searches}/{len(searches)} | found {total_found} | picks {len(picks)} | leads {len(leads)}")

        time.sleep(SEARCH_DELAY)

    # ==================== GOOGLE JOBS SUPPLEMENT ====================
    print(f"\n  Google Jobs: searching top titles across GCC...")
    google_titles = ["CTO", "VP Digital Transformation", "Director Digital Transformation",
                     "PMO Director", "Chief Digital Officer", "Head of Technology",
                     "Chief Information Officer", "Chief Operating Officer"]
    google_countries = ["Dubai", "Saudi Arabia", "Qatar", "Abu Dhabi"]
    google_found = 0
    google_new = 0
    google_consent_handled = False

    for gt in google_titles:
        for gc in google_countries:
            if time.time() - start > MAX_RUNTIME_SECONDS:
                break
            gjobs = scrape_google_jobs(gt, gc, max_results=5)
            google_found += len(gjobs)
            for gj in gjobs:
                if gj["id"] in seen:
                    continue
                seen.add(gj["id"])
                if is_duplicate(gj["id"], gj.get("company", "")):
                    continue
                relevant, reason = is_relevant(gj["title"], gj["location"])
                if not relevant:
                    continue
                save_notified(gj)
                if is_priority(gj["title"], gj["location"]):
                    picks.append(gj)
                    google_new += 1
                    print(f"  GOOGLE PICK: {gj['title']} | {gj['company']} | {gj['location']}")
                else:
                    leads.append(gj)
                    google_new += 1
            time.sleep(2)  # Rate limit between Google searches

    print(f"  Google Jobs: {google_found} found, {google_new} new relevant")

    # ==================== JD ENRICHMENT + ATS SCORING ====================
    if picks:
        picks = enrich_picks_with_jd(picks)
        # Log ATS results
        high_ats = [j for j in picks if j.get("ats_score", 0) >= 75]
        mid_ats = [j for j in picks if 65 <= j.get("ats_score", 0) < 75]
        low_ats = [j for j in picks if j.get("ats_score", 0) < 65]
        print(f"  ATS results: {len(high_ats)} high (75+), {len(mid_ats)} mid (65-74), {len(low_ats)} low (<65)")

    # ==================== DEGRADATION CHECK ====================
    if total_found < MIN_JOBS_ALERT:
        msg = f"⚠️ Scanner degradation: {total_found} jobs from {total_searches} searches. Possible rate limit."
        print(f"\n  {msg}")
        send_slack(msg)

    # ==================== SAVE REPORT ====================
    elapsed = int(time.time() - start)
    out_file = OUTPUT_DIR / f"qualified-jobs-{date_str}.md"

    with open(out_file, "w") as f:
        f.write(f"# LinkedIn Gulf Jobs Scanner v3.1 - Report\n\n")
        f.write(f"**Date:** {date_str}\n")
        f.write(f"**Engine:** JobSpy (LinkedIn + Indeed, fast mode)\n")
        f.write(f"**Searches:** {total_searches}\n")
        f.write(f"**Jobs found:** {total_found}\n")
        f.write(f"**Unique/relevant:** {len(picks)+len(leads)}\n")
        f.write(f"**Priority Picks:** {len(picks)} (C-suite + UAE/Saudi + DT)\n")
        f.write(f"**Leads:** {len(leads)} (exec + GCC + domain)\n")
        f.write(f"**Filtered out:** {len(filtered_out)} (see filtered-out-jobs.md for audit)\n")
        f.write(f"**Runtime:** {elapsed}s\n\n")

        if total_found < MIN_JOBS_ALERT:
            f.write(f"⚠️ **DEGRADATION:** Only {total_found} jobs found. Scanner may be rate-limited.\n\n")

        if picks:
            # Separate by career verdict
            apply_jobs = [j for j in picks if j.get('career_verdict') == 'APPLY']
            skip_jobs = [j for j in picks if j.get('career_verdict') == 'SKIP']
            stretch_jobs = [j for j in picks if j.get('career_verdict') == 'STRETCH']
            # Jobs without verdict (legacy) go to apply
            no_verdict = [j for j in picks if not j.get('career_verdict')]
            apply_jobs.extend(no_verdict)

            # Sort each group by career_fit desc, then ats_score desc
            apply_jobs.sort(key=lambda x: (x.get('career_fit', 0), x.get('ats_score', 0)), reverse=True)
            skip_jobs.sort(key=lambda x: x.get('ats_score', 0), reverse=True)
            stretch_jobs.sort(key=lambda x: x.get('career_fit', 0), reverse=True)

            f.write(f"## ✅ APPLY - Genuine Career Fits ({len(apply_jobs)} jobs)\n\n")
            for job in apply_jobs:
                ats = job.get('ats_score', 0)
                fit = job.get('career_fit', 0)
                reason = job.get('career_reason', '')
                f.write(f"### [{fit}/10] {job['title']} (ATS: {ats}%)\n")
                f.write(f"- Company: {job['company']}\n")
                f.write(f"- Location: {job['location']}\n")
                f.write(f"- Career Fit: {fit}/10 - {reason}\n")
                f.write(f"- ATS Score: {ats}%\n")
                if job.get('ats_keywords'):
                    f.write(f"- Matching Keywords: {', '.join(job['ats_keywords'][:10])}\n")
                if job.get('jd_fetched'):
                    f.write(f"- JD: ✅ Fetched ({len(job.get('jd_text',''))} chars)\n")
                else:
                    f.write(f"- JD: ❌ Not fetched\n")
                f.write(f"- URL: {job['url']}\n")
                if job.get('date_posted'): f.write(f"- Posted: {job['date_posted']}\n")
                f.write(f"\n")

            if stretch_jobs:
                f.write(f"## 🟡 STRETCH - Possible but Risky ({len(stretch_jobs)} jobs)\n\n")
                for job in stretch_jobs:
                    f.write(f"- **{job['title']}** @ {job['company']} ({job['location']}) - {job.get('career_reason','')} | {job['url']}\n")
                f.write(f"\n")

            if skip_jobs:
                f.write(f"## ❌ SKIP - Domain Mismatch ({len(skip_jobs)} jobs)\n\n")
                for job in skip_jobs:
                    f.write(f"- ~~{job['title']}~~ @ {job['company']} - {job.get('career_reason','')} (FIT: {job.get('career_fit',0)})\n")
                f.write(f"\n")
        else:
            f.write(f"## Priority Picks\n\nNo priority picks today.\n\n")

        if leads:
            f.write(f"## Executive Leads - All GCC Relevant\n\n")
            for job in leads:
                extras = []
                if job.get('job_level'): extras.append(job['job_level'])
                if job.get('company_industry'): extras.append(job['company_industry'])
                if job.get('min_salary') and job.get('currency'): extras.append(f"{job['currency']} {job['min_salary']}-{job.get('max_salary','')}")
                if job.get('date_posted'): extras.append(f"posted {job['date_posted']}")
                extra_str = f" | {', '.join(extras)}" if extras else ""
                f.write(f"- **{job['title']}** | {job['company']} | {job['location']}{extra_str} | [{job['site']}]({job['url']})\n")

    # ==================== FILTERED-OUT AUDIT LOG ====================
    with open(FILTERED_LOG, "w") as f:
        f.write(f"# Filtered-Out Jobs Audit - {date_str}\n\n")
        f.write(f"**Total filtered:** {len(filtered_out)}\n\n")
        # Group by reason
        reasons = {}
        for j in filtered_out:
            r = j.get("filter_reason", "unknown")
            reasons.setdefault(r, []).append(j)
        for reason, jobs_list in sorted(reasons.items()):
            f.write(f"## {reason} ({len(jobs_list)})\n\n")
            for j in jobs_list:
                f.write(f"- **{j['title']}** | {j['company']} | {j['location']} | {j['url']}\n")
            f.write("\n")

    # ==================== SLACK ====================
    if picks:
        msg = f"🎯 *Gulf Scanner v3.0 - {len(picks)} Priority Picks*\n\n"
        for j in picks[:5]:
            msg += f"*{j['title']}* at {j['company']} ({j['location']})\n{j['url']}\n\n"
        if leads:
            msg += f"Plus {len(leads)} additional exec leads."
    else:
        msg = f"📊 *Gulf Scanner v3.0 - {len(leads)} Exec Leads*\n"
        msg += f"Searches: {total_searches} | Found: {total_found} | Leads: {len(leads)}\n"
        if leads:
            msg += "\n*Top Leads:*\n"
            for j in leads[:5]:
                msg += f"• {j['title']} | {j['company']} | {j['location']}\n  {j['url']}\n"
        if total_found < MIN_JOBS_ALERT:
            msg += f"\n⚠️ Low job count - possible rate limit."

    send_slack(msg)

    # ==================== CRON LOG ====================
    with open(LOG_FILE, "a") as f:
        f.write(f"\n## {ts} (v3.0)\n")
        f.write(f"- Searches: {total_searches}\n")
        f.write(f"- Found: {total_found}\n")
        f.write(f"- Priority picks: {len(picks)}\n")
        f.write(f"- Leads: {len(leads)}\n")
        f.write(f"- Runtime: {elapsed}s\n")
        if total_found < MIN_JOBS_ALERT:
            f.write(f"- ⚠️ DEGRADATION\n")

    # ==================== SUMMARY ====================
    # ==================== SELF-VALIDATION (Fix 1) ====================
    expected_searches = len(searches)
    validation_warnings = []
    if total_searches != expected_searches:
        validation_warnings.append(f"SEARCH COUNT MISMATCH: ran {total_searches}, expected {expected_searches}. Runtime limit or errors.")
    if total_found == 0 and total_searches > 5:
        validation_warnings.append(f"ZERO RESULTS: {total_searches} searches returned 0 jobs. Possible rate limiting or cookie expiry.")
    if total_found > 0 and len(picks) + len(leads) == 0 and len(filtered_out) == 0:
        validation_warnings.append(f"DATA LOSS: {total_found} jobs found but none classified. Filter logic error.")
    if len(filtered_out) + len(picks) + len(leads) + len(seen) < total_found * 0.5:
        validation_warnings.append(f"ACCOUNTING GAP: classified {len(filtered_out)+len(picks)+len(leads)} but found {total_found}. Dedup may be too aggressive.")

    if validation_warnings:
        print(f"\n⚠️ VALIDATION WARNINGS ({len(validation_warnings)}):")
        for w in validation_warnings:
            print(f"  - {w}")
        # Append to report
        with open(out_file, "a") as f:
            f.write(f"\n## Validation Warnings\n\n")
            for w in validation_warnings:
                f.write(f"- ⚠️ {w}\n")
    else:
        print(f"\n✅ Validation passed: {total_searches}/{expected_searches} searches, {total_found} found, {len(picks)+len(leads)} relevant, {len(filtered_out)} filtered.")

    # === Save scanner metadata JSON for briefing orchestrator ===
    scanner_meta = {
        "date": date_str,
        "total_searches": total_searches,
        "expected_searches": expected_searches,
        "total_found": total_found,
        "priority_picks": len(picks),
        "exec_leads": len(leads),
        "filtered_out": len(filtered_out),
        "runtime_seconds": elapsed,
        "countries": list(set(s[1] for s in searches)),
        "sources": ["LinkedIn", "Indeed", "Google"],
        "source_status": {
            src: ("✅" if any(j.get("site","").lower() == src.lower() for j in picks + leads) else "⚠️")
            for src in ["LinkedIn", "Indeed", "Google"]
        },
        "cookie_age_days": None,
        "validation_warnings": validation_warnings,
        "degraded": total_found < MIN_JOBS_ALERT,
    }
    # Check cookie age
    for _cpath in ["/root/.openclaw/cookies/linkedin.txt"]:
        try:
            import pathlib
            mtime = pathlib.Path(_cpath).stat().st_mtime
            age_days = int((time.time() - mtime) / 86400)
            scanner_meta["cookie_age_days"] = age_days
        except:
            pass

    meta_file = OUTPUT_DIR / f"scanner-meta-{date_str}.json"
    with open(meta_file, "w") as f:
        json.dump(scanner_meta, f, indent=2)
    print(f"\nScanner metadata saved: {meta_file}")

    # === Notion Sync ===
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from notion_sync import sync_new_jobs, sync_system_event, sync_scanner_run
        all_new = picks + leads
        if all_new:
            added = sync_new_jobs(all_new)
        # Sync scanner run metadata to Notion
        scanner_meta = {
            "total_searches": search_count,
            "total_found": total_found,
            "priority_picks": len(qualified),
            "exec_leads": len(exec_leads),
            "filtered_out": len(filtered_jobs),
            "runtime_seconds": int(time.time() - start_time),
            "degraded": degradation_flag,
            "cookie_age_days": (datetime.now() - cookie_mtime).days if cookie_mtime else None,
            "validation_warnings": validation_warnings,
            "source_status": source_status,
        }
        try:
            sync_scanner_run(scanner_meta, today_str)
        except Exception as e:
            print(f"Scanner sync error: {e}")
            print(f"\nNotion: {added} jobs synced to pipeline")
        sync_system_event(
            f"Scanner: {total_found} found, {len(picks)} priority, {len(leads)} leads",
            component="Scanner",
            details=f"Searches: {total_searches}, Filtered: {len(filtered_out)}, Warnings: {len(validation_warnings)}"
        )
        # Sync scanner run metadata to Notion
        scanner_meta = {
            "total_searches": search_count,
            "total_found": total_found,
            "priority_picks": len(qualified),
            "exec_leads": len(exec_leads),
            "filtered_out": len(filtered_jobs),
            "runtime_seconds": int(time.time() - start_time),
            "degraded": degradation_flag,
            "cookie_age_days": (datetime.now() - cookie_mtime).days if cookie_mtime else None,
            "validation_warnings": validation_warnings,
            "source_status": source_status,
        }
        try:
            sync_scanner_run(scanner_meta, today_str)
        except Exception as e:
            print(f"Scanner sync error: {e}")
    except Exception as e:
        print(f"\nNotion sync skipped: {e}")

    print(f"\n=== DONE ({elapsed}s) ===")
    print(f"Searches:       {total_searches}/{expected_searches}")
    print(f"Jobs found:     {total_found}")
    print(f"Filtered out:   {len(filtered_out)}")
    print(f"Priority picks: {len(picks)}")
    print(f"Exec leads:     {len(leads)}")
    print(f"Output:         {out_file}")
    print(f"Audit log:      {FILTERED_LOG}")

if __name__ == "__main__":
    main()


# ===================== SEMANTIC FIT FILTER (Added 2026-03-18) =====================
# This filter runs AFTER ATS keyword scoring to eliminate domain mismatches.
# ATS score measures WORD OVERLAP. This filter measures CAREER FIT.

AHMED_DOMAINS = ["digital transformation", "pmo", "program management", "project management",
    "healthcare", "healthtech", "fintech", "payments", "e-commerce", "ecommerce",
    "operational excellence", "change management", "enterprise", "consulting"]

AHMED_ROLES = ["pmo", "program", "director", "vp", "vice president", "head of", "chief",
    "transformation", "operations", "strategy", "product management", "delivery"]

SKIP_DOMAINS = {
    "cybersecurity": ["ciso", "information security officer", "security engineer", "penetration", "soc analyst"],
    "hands-on coding": ["software engineer", "developer", "full stack", "backend engineer", "frontend engineer", "code reviews", "sdlc", "hands-on technical"],
    "oil & gas": ["offshore", "upstream", "downstream", "drilling", "petroleum", "subsea", "oil and gas", "oil & gas"],
    "civil engineering": ["roads", "highways", "bridges", "tunnels", "structural engineer", "geotechnical", "civil engineer"],
    "investment banking": ["equity capital markets", "ecm", "ipo execution", "block trades", "league table", "deal origination"],
    "aviation": ["aircraft", "mro", "ground support equipment", "aviation maintenance"],
    "pure sales": ["quota-carrying", "business development representative", "sales representative"],
}

def semantic_fit_filter(job):
    """Returns (verdict, fit_score, reason) based on actual career fit."""
    title = job.get("title", "").lower()
    jd = job.get("jd_text", "").lower()
    combined = title + " " + jd

    # Check SKIP domains first
    for domain, keywords in SKIP_DOMAINS.items():
        matches = [k for k in keywords if k in combined]
        if len(matches) >= 2:
            return "SKIP", max(1, min(3, job.get("ats_score", 0) // 30)), f"Domain mismatch: {domain}"
        if len(matches) == 1 and any(k in title for k in keywords):
            return "SKIP", 2, f"Title indicates {domain} specialization"

    # Check domain relevance
    domain_hits = sum(1 for d in AHMED_DOMAINS if d in combined)
    role_hits = sum(1 for r in AHMED_ROLES if r in combined)

    if domain_hits >= 3 and role_hits >= 2:
        return "APPLY", min(10, 6 + domain_hits), "Strong career fit"
    elif domain_hits >= 2 or role_hits >= 2:
        return "APPLY", min(8, 5 + domain_hits), "Good career fit"
    elif domain_hits >= 1:
        return "STRETCH", 4, "Partial domain overlap"
    else:
        return "SKIP", 2, "No relevant domain experience"
