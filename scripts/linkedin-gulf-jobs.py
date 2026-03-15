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
PRIORITY_COUNTRIES  = ["United Arab Emirates", "Saudi Arabia", "Qatar"]
SECONDARY_COUNTRIES = ["Bahrain", "Kuwait", "Oman"]

# 10 primary titles searched across all priority countries
PRIMARY_TITLES = [
    "VP Digital Transformation",
    "Director Digital Transformation",
    "Chief Digital Officer",
    "Chief Technology Officer",
    "Head of Digital Transformation",
    "PMO Director",
    "Head of Technology",
    "VP Technology",
    "Chief Information Officer",
    "Program Director",
]

# 5 secondary titles — UAE + Saudi only
SECONDARY_TITLES = [
    "Chief Operating Officer",
    "Chief Strategy Officer",
    "Head of IT",
    "Director of Technology",
    "Senior Director Digital Transformation",
]

PREFERRED_COUNTRIES = ["Saudi Arabia", "United Arab Emirates"]

# Paths
BASE_DIR       = Path("/root/.openclaw/workspace")
OUTPUT_DIR     = BASE_DIR / "jobs-bank" / "scraped"
LOG_FILE       = OUTPUT_DIR / "cron-logs.md"
DETAILED_LOG   = OUTPUT_DIR / "detailed-search-log.md"
NOTIFIED_FILE  = OUTPUT_DIR / "notified-jobs.md"
APPLIED_DIR    = BASE_DIR / "jobs-bank" / "applications"
PIPELINE_FILE  = BASE_DIR / "jobs-bank" / "pipeline.md"
CONFIG_FILE    = Path("/root/.openclaw/openclaw.json")

MAX_JOBS_PER_SEARCH  = 10
MAX_RUNTIME_SECONDS  = 15 * 60   # 15 minutes
SEARCH_DELAY         = 2         # seconds between searches
MIN_JOBS_ALERT       = 10        # alert if fewer total jobs found

# Title filter: must match executive level
EXEC_WORDS = ["chief","cto","cio","cdo","coo","cso","vp ","vice president",
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
    gcc = any(w in loc for w in ["saudi","uae","dubai","riyadh","qatar","doha",
                                  "bahrain","kuwait","oman","abu dhabi"])
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
    """Is this a priority role (VP+/C-suite + UAE/Saudi + DT)?"""
    t = title.lower()
    loc = location.lower()
    is_csuite = any(w in t for w in ["chief","cto","cio","cdo","coo","vp ","vice president"])
    is_dt = any(w in t for w in ["digital","transformation","technology","pmo"])
    is_top_gcc = any(w in loc for w in ["saudi","uae","dubai","riyadh","abu dhabi"])
    return is_csuite and is_dt and is_top_gcc

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
    try:
        with open(PIPELINE_FILE) as f:
            for line in f:
                m = re.search(r'\|\s*(?:☑️|~~)?\s*([A-Za-z][A-Za-z0-9\s&\(\)\.]+?)\s*(?:~~)?\s*\|', line)
                if m:
                    c = m.group(1).strip().lower()
                    if c and c not in ("company","none"): companies.add(c)
    except FileNotFoundError:
        pass
    return companies

def is_duplicate(jid, company=""):
    if jid in _notified:
        return True
    slug = re.sub(r"[^a-z0-9]", "-", company.lower()).strip("-")
    skip = {"confidential","undisclosed","company","unknown","nan"}
    if slug and len(slug) > 3 and slug not in skip:
        for app in _applied:
            if slug in app: return True
        for pc in _pipeline:
            if pc in slug or slug in pc: return True
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
            site_name=["linkedin", "indeed"],
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

    print(f"=== LinkedIn Gulf Jobs Scanner v3.0 ===")
    print(f"Started: {ts}")

    _notified = load_notified()
    _applied  = load_applied()
    _pipeline = load_pipeline()
    print(f"Cache: {len(_notified)} notified | {len(_applied)} applied | {len(_pipeline)} pipeline")

    # Build search plan
    searches = []
    for c in PRIORITY_COUNTRIES:
        for t in PRIMARY_TITLES:
            searches.append((t, c))
    for c in PRIORITY_COUNTRIES[:2]:   # UAE + Saudi only
        for t in SECONDARY_TITLES:
            searches.append((t, c))
    for c in SECONDARY_COUNTRIES:
        for t in PRIMARY_TITLES[:5]:   # top 5 only
            searches.append((t, c))

    print(f"Search plan: {len(searches)} combinations | Delay: {SEARCH_DELAY}s between searches")

    total_searches = 0
    total_found    = 0
    seen           = set()
    picks          = []    # priority picks (C-suite + UAE/Saudi + DT)
    leads          = []    # other relevant leads

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
                continue

            relevant, reason = is_relevant(job["title"], job["location"])
            if not relevant:
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
        f.write(f"# LinkedIn Gulf Jobs Scanner v3.0 - Report\n\n")
        f.write(f"**Date:** {date_str}\n")
        f.write(f"**Engine:** JobSpy (LinkedIn + Indeed, fast mode)\n")
        f.write(f"**Searches:** {total_searches}\n")
        f.write(f"**Jobs found:** {total_found}\n")
        f.write(f"**Unique/relevant:** {len(picks)+len(leads)}\n")
        f.write(f"**Priority Picks:** {len(picks)} (C-suite + UAE/Saudi + DT)\n")
        f.write(f"**Leads:** {len(leads)} (exec + GCC + domain)\n")
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
                f.write(f"- URL: {job['url']}\n\n")
        else:
            f.write(f"## Priority Picks\n\nNo priority picks today.\n\n")

        if leads:
            f.write(f"## Executive Leads — All GCC Relevant\n\n")
            for job in leads:
                f.write(f"- **{job['title']}** | {job['company']} | {job['location']} | [{job['site']}]({job['url']})\n")

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
    print(f"\n=== DONE ({elapsed}s) ===")
    print(f"Searches:       {total_searches}")
    print(f"Jobs found:     {total_found}")
    print(f"Priority picks: {len(picks)}")
    print(f"Exec leads:     {len(leads)}")
    print(f"Output:         {out_file}")

if __name__ == "__main__":
    main()
