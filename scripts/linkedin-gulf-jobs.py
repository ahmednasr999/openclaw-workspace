#!/usr/bin/env python3
"""
LinkedIn Gulf Jobs Scanner v3.0 - Fast Title Filter
====================================================
Strategy:
  - Fast search: LinkedIn + Indeed, NO JD fetch (no rate limiting)
  - Filter by: executive title + GCC location + DT/Tech domain
  - Output: "Radar Picks" — relevant leads surfaced for review
  - ATS scoring against full JD happens at apply time (not here)
  - Runs in < 5 minutes for all searches

ATS_THRESHOLD (82) is applied ONLY when full JD is available.
Title-only pass surfaces leads — Ahmed decides which to pursue.
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

# All potential executive titles — searched across ALL GCC countries
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
MAX_RUNTIME_SECONDS  = 15 * 60   # 15 minutes
SEARCH_DELAY         = 2         # seconds between searches
MIN_JOBS_ALERT       = 10        # alert if fewer total jobs found

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

# ===================== SEARCH =====================

def search(title, country):
    """Fast search: no JD fetch, LinkedIn + Indeed."""
    try:
        from jobspy import scrape_jobs
        results = scrape_jobs(
            site_name=["linkedin", "indeed", "glassdoor", "google"],
            search_term=title,
            location=country,
            hours_old=72,
            results_wanted=MAX_JOBS_PER_SEARCH,
            linkedin_fetch_description=False,
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

    for title, country in searches:
        if time.time() - start > MAX_RUNTIME_SECONDS:
            print(f"  Runtime limit reached. Stopping.")
            break

        total_searches += 1
        jobs = search(title, country)

        with open(DETAILED_LOG, "a") as f:
            f.write(f"- {title} in {country}: {len(jobs)} jobs\n")

        if not jobs:
            time.sleep(1)
            continue

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
            f.write(f"## Priority Picks — C-Suite + UAE/Saudi + DT\n\n")
            for job in picks:
                f.write(f"### {job['title']}\n")
                f.write(f"- Company: {job['company']}\n")
                f.write(f"- Location: {job['location']}\n")
                f.write(f"- Source: {job['site']}\n")
                if job.get('job_level'): f.write(f"- Level: {job['job_level']}\n")
                if job.get('job_type'): f.write(f"- Type: {job['job_type']}\n")
                if job.get('job_function'): f.write(f"- Function: {job['job_function']}\n")
                if job.get('company_industry'): f.write(f"- Industry: {job['company_industry']}\n")
                if job.get('min_salary') and job.get('currency'): f.write(f"- Salary: {job['currency']} {job['min_salary']}-{job.get('max_salary','')}\n")
                if job.get('is_remote') == 'True': f.write(f"- ⚠️ Remote (Ahmed prefers on-site)\n")
                if job.get('company_url'): f.write(f"- Company: [{job['company']}]({job['company_url']})\n")
                f.write(f"- URL: {job['url']}\n")
                if job.get('date_posted'): f.write(f"- Posted: {job['date_posted']}\n")
                f.write(f"\n")
        else:
            f.write(f"## Priority Picks\n\nNo priority picks today.\n\n")

        if leads:
            f.write(f"## Executive Leads — All GCC Relevant\n\n")
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
        f.write(f"# Filtered-Out Jobs Audit — {date_str}\n\n")
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
        msg = f"🎯 *Gulf Scanner v3.0 — {len(picks)} Priority Picks*\n\n"
        for j in picks[:5]:
            msg += f"*{j['title']}* at {j['company']} ({j['location']})\n{j['url']}\n\n"
        if leads:
            msg += f"Plus {len(leads)} additional exec leads."
    else:
        msg = f"📊 *Gulf Scanner v3.0 — {len(leads)} Exec Leads*\n"
        msg += f"Searches: {total_searches} | Found: {total_found} | Leads: {len(leads)}\n"
        if leads:
            msg += "\n*Top Leads:*\n"
            for j in leads[:5]:
                msg += f"• {j['title']} | {j['company']} | {j['location']}\n  {j['url']}\n"
        if total_found < MIN_JOBS_ALERT:
            msg += f"\n⚠️ Low job count — possible rate limit."

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
