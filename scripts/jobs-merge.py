#!/usr/bin/env python3
"""
jobs-merge.py - Layer 2: Merge and deduplicate jobs from all source adapters.

Reads: data/jobs-raw/*.json
Writes: data/jobs-merged.json

Features:
  - Checks freshness (skip stale files older than TTL)
  - Merges all jobs into single list
  - Dedup by URL exact match, then title+company fuzzy match (>85%)
  - Cross-reference with applied-job-ids.txt
  - Apply search policy filters
  - Track which sources found each job
"""

import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(__file__))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from _imports import agent_common, jobs_source_common

# Import from agent_common
AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
load_json = agent_common.load_json
now_cairo = agent_common.now_cairo
WORKSPACE = agent_common.WORKSPACE
DATA_DIR = agent_common.DATA_DIR
JOBS_RAW_DIR = agent_common.JOBS_RAW_DIR

# Import from jobs_source_common
SKIP_WORDS = jobs_source_common.SKIP_WORDS
EXEC_WORDS = jobs_source_common.EXEC_WORDS
DOMAIN_WORDS = jobs_source_common.DOMAIN_WORDS
STRATEGIC_ROLE_WORDS = jobs_source_common.STRATEGIC_ROLE_WORDS
TARGET_INDUSTRY_WORDS = jobs_source_common.TARGET_INDUSTRY_WORDS
EXCLUDED_INDUSTRY_WORDS = jobs_source_common.EXCLUDED_INDUSTRY_WORDS

# Configuration
AGENT_NAME = "jobs-merge"
OUTPUT_FILE = DATA_DIR / "jobs-merged.json"
APPLIED_IDS_FILE = WORKSPACE / "jobs-bank" / "applied-job-ids.txt"
SEARCH_POLICY_FILE = WORKSPACE / "jobs-bank" / "search-policy.md"
FRESHNESS_HOURS = 25  # Max age for source files (survives 1 failed pipeline run)
FUZZY_MATCH_THRESHOLD = 0.85  # 85% similarity for title+company dedup

# Cairo timezone
CAIRO_TZ = timezone(timedelta(hours=2))


def load_applied_ids() -> set[str]:
    """Load already-applied job IDs from tracking file.

    Stores both the raw ID and any numeric suffix extracted from it,
    so matching works regardless of format (plain number or prefixed).
    """
    applied = set()
    try:
        if APPLIED_IDS_FILE.exists():
            with open(APPLIED_IDS_FILE) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("|")
                    if parts:
                        job_id = parts[0].strip()
                        if job_id and len(job_id) >= 6:
                            # Add the raw ID as-is
                            applied.add(job_id)
                            # Also add just the numeric/hex suffix for prefix-agnostic matching
                            suffix = job_id.split("-")[-1]
                            if suffix != job_id and len(suffix) >= 6:
                                applied.add(suffix)
    except Exception as e:
        print(f"  Warning: Could not load applied IDs: {e}")
    return applied


def is_stale(meta: dict, max_hours: int) -> bool:
    """Check if source file is stale based on generated_at timestamp."""
    try:
        generated_at = meta.get("generated_at", "")
        if not generated_at:
            return True

        gen_time = datetime.fromisoformat(generated_at)
        age = now_cairo() - gen_time
        age_hours = age.total_seconds() / 3600

        return age_hours > max_hours
    except Exception:
        return True


def fuzzy_match(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def normalize_title_company(title: str, company: str) -> str:
    """Create a normalized key for fuzzy matching."""
    title = title.lower().strip()
    company = company.lower().strip()

    title = re.sub(r'\s*[\(\--]\s*(dubai|uae|saudi|riyadh|qatar|doha|bahrain|kuwait|oman|muscat|abu dhabi|jeddah).*$', '', title, flags=re.IGNORECASE)
    company = re.sub(r'\s*(llc|ltd|inc|corp|corporation|limited|fzc|fze|fz|dmcc|difc)\.?$', '', company, flags=re.IGNORECASE).strip()

    return f"{title}|||{company}"


def find_fuzzy_duplicate(job: dict, existing_jobs: list[dict], threshold: float = FUZZY_MATCH_THRESHOLD) -> dict | None:
    """Find if a job is a fuzzy duplicate of any existing job."""
    job_key = normalize_title_company(job.get("title", ""), job.get("company", ""))

    for existing in existing_jobs:
        existing_key = normalize_title_company(existing.get("title", ""), existing.get("company", ""))

        similarity = fuzzy_match(job_key, existing_key)
        if similarity >= threshold:
            return existing

    return None


# ── Country extraction ────────────────────────────────────────────────────────
GCC_COUNTRY_MAP = {
    "gcc": "GCC",  # pass-through for Google source; not a real country but better than Unknown
    "uae": "United Arab Emirates", "united arab emirates": "United Arab Emirates",
    "dubai": "United Arab Emirates", "abu dhabi": "United Arab Emirates",
    "sharjah": "United Arab Emirates", "ajman": "United Arab Emirates",
    "saudi arabia": "Saudi Arabia", "riyadh": "Saudi Arabia", "jeddah": "Saudi Arabia",
    "khobar": "Saudi Arabia", "dammam": "Saudi Arabia", "dhahran": "Saudi Arabia", "eastern province": "Saudi Arabia",
    "qatar": "Qatar", "doha": "Qatar", "lusail": "Qatar",
    "bahrain": "Bahrain", "manama": "Bahrain", "awali": "Bahrain", "capital governorate": "Bahrain",
    "kuwait": "Kuwait", "kuwait city": "Kuwait",
    "oman": "Oman", "muscat": "Oman",
}


def extract_country(location: str = "", search_country: str = "", url: str = "") -> str:
    """Extract GCC country from location/search_country/url fields.
    Returns canonical country name or 'Unknown' if none matched.
    """
    text = " ".join(filter(None, [location, search_country, url])).lower()
    for keyword, country in GCC_COUNTRY_MAP.items():
        if keyword in text:
            return country
    return "Unknown"


def clean_title(title: str) -> str:
    """Strip location leakage from title (e.g. 'Engineering Director | Job in Abu Dhabi, UAE')."""
    title = re.sub(r'\s*\|\s*Job\s+in\s+.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*-\s*\d+\s*vacancies?.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(.*(?:Dubai|UAE|Saudi|Riyadh|Doha|Qatar|Bahrain|Kuwait|Oman|Jeddah|Abu Dhabi|Muscat).*\)\s*$', '', title, flags=re.IGNORECASE)
    return title.strip()


# ── Negative keyword filters (education, HR, finance, non-exec, low-seniority) ─
NEGATIVE_TITLE_KEYWORDS = [
    "arabic studies", "islamic studies", "english studies", "head of arabic",
    "human resources", "hr director", "hr manager", "hr business partner",
    "credit & execution", "credit risk", "credit analysis",
    "accounts payable", "accounts receivable", "payroll",
    "customer service", "call center", "data entry",
    "intern", "internship", "junior", "associate analyst",
    "teacher", "professor", "lecturer", "teaching assistant",
    "school", "university", "education director", "head of education","education supervisor", "education supervisor",
    "nurse", "doctor", "physician", "pharmacy",
    "head of finance", "chief financial officer", "cfo", "finance manager", "finance director",
    # Added 2026-04-05 — GTM, staffing, agriculture, pure sales, business development
    "staffing", "staff augmentation", "recruitment consultant",
    "headhunter", "search firm", "talent partner",
    "agricultur", "farming", "livestock",
    "go to market", "gtm strategy", "g2m",
    "sales engineer", "sales operations", "revenue operations",
    "business developer", "business development executive",
    "account manager", "account director", "client partner",
    "retail", "store manager", "merchandising",
    "oil and gas", "petroleum", "drilling",  # Ahmed not targeting oil/gas
    # Added 2026-04-05 — catch remaining non-exec noise
    "analyst", "associate", "graduate", "coordinator",
    "home service", "concierge", "beauty salon",
    "commercial director",  # Usually sales/commercial, not exec ops
    # Tightened 2026-04-10 - recurrent Sayyad false positives
    "public affairs", "government affairs", "public policy",
    "urban designer", "urban design",
    "commercial management", "commercial manager",
    "events and sports management", "sports management",
]


## Aggregator / listing page patterns to filter out
AGGREGATOR_DOMAINS = {
    "glassdoor.com", "trovit.com", "indeed.com", "linkedin.com/jobs/search",
    "bayt.com/en/jobs", "naukri.com/jobs-in", "monster.com", "ziprecruiter.com",
    "simplyhired.com", "careerbuilder.com", "jooble.org", "jobrapido.com",
    # Added 2026-04-05: Egyptian/non-GCC portals and staffing agencies
    "wuzzuf.net",   # Egyptian jobs only — zero GCC value
    "forasati.net", # Algerian portal
    "akhtaboot.com",# Jordanian — rarely relevant for GCC executive
    "gulfjobs.com", # Low quality aggregator
    "oceansmart.com", # Staffing/recruitment
}

AGGREGATOR_TITLE_PATTERNS = [
    r'^\d+\s+.+jobs?\s+in\s+',          # "47 Head of digital transformation jobs in Dubai"
    r'.+jobs?\s+in\s+.+\s*[--]\s*\d+',   # "PMO Director Jobs in Riyadh - 124 Vacancies"
    r'.+vacancies?\s+\w+\s+\d{4}',       # "... Vacancies Mar 2026"
    r'.+job offers?\s+in\s+',             # "Pmo director job offers in dubai"
    r'^top\s+\d+\s+',                     # "Top 10 PMO jobs..."
    r'.+jobs?\s+[--]\s+\d+\s+vacancies', # "... jobs - 551 Vacancies"
]


def is_aggregator_listing(job: dict) -> tuple[bool, str]:
    """Detect aggregator listing pages masquerading as individual jobs."""
    title = job.get("title", "")
    url = job.get("url", "").lower()
    company = job.get("company", "").lower()

    # Check URL domain
    for domain in AGGREGATOR_DOMAINS:
        if domain in url and "/jobs/" not in url.split("?")[0].rsplit("/", 1)[-1]:
            # Allow individual job pages (URL ends with job ID), block listing pages
            if re.search(r'/jobs?/\d+', url) or re.search(r'/job/[a-z0-9-]+$', url):
                continue  # This is an individual job page, keep it
            return True, f"aggregator-domain:{domain}"

    # Check title patterns
    for pattern in AGGREGATOR_TITLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return True, f"aggregator-title-pattern"

    # Check company name is actually a job board
    job_board_names = ["glassdoor", "trovit", "indeed", "bayt", "linkedin", "naukrigulf", "monster"]
    for board in job_board_names:
        if board in company:
            return True, f"aggregator-company:{board}"

    return False, "individual-job"


def is_bad_url(url: str) -> tuple[bool, str]:
    """Detect broken/invalid/non-job URLs."""
    if not url:
        return True, "no-url"

    url_lower = url.lower().strip()

    # URL is just a domain with no path
    from urllib.parse import urlparse
    parsed = urlparse(url_lower)
    path = parsed.path.strip("/")
    if not path:
        return True, "domain-only-url"

    # Profile pages (not jobs)
    profile_patterns = [
        "/me/", "/profile/", "/u/", "/user/", "/cv/", "/resume/",
        "linkedin.com/in/",
    ]
    for p in profile_patterns:
        if p in url_lower:
            return True, f"profile-page:{p}"

    return False, ""


def apply_search_policy(job: dict) -> tuple[bool, str]:
    """Apply search policy filters. Returns (keep, reason)."""
    title_raw = job.get("title", "")
    title = title_raw.lower()
    url = job.get("url", "")
    jd_text = (job.get("jd_text", "") or job.get("raw_snippet", "") or "").lower()
    combined = f"{title} {jd_text}"

    # Filter bad URLs (broken links, profile pages)
    is_bad, bad_reason = is_bad_url(url)
    if is_bad:
        return False, bad_reason

    # Filter jobs with person names in title (CV pages indexed as jobs)
    import re
    # Pattern: "FirstName LastName - Title" or "FirstName LastName - Title"
    if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+\s+[-–—]\s+', title_raw):
        return False, "person-name-in-title"

    # Filter aggregator listings - only for Exa results
    # Jobs from Indeed/LinkedIn/Bayt/Google are already individual listings
    source = job.get("source", "")
    if source == "exa":
        is_agg, agg_reason = is_aggregator_listing(job)
        if is_agg:
            return False, agg_reason

    # Must be senior enough to matter
    has_exec = any(w in title for w in EXEC_WORDS)
    if not has_exec:
        return False, "no-seniority"

    # Tight role-family alignment: broad senior management is not enough.
    strategic_role_match = any(w in combined for w in STRATEGIC_ROLE_WORDS)
    domain_match = any(w in combined for w in DOMAIN_WORDS)
    target_industry_match = any(w in combined for w in TARGET_INDUSTRY_WORDS)

    # Allow strong watchlist-company scans some flexibility, but still require
    # either a role-family match or target-industry evidence.
    search_title = (job.get("search_title", "") or "").lower()
    watchlist_query = 'chief technology officer' in search_title or 'head of business excellence' in search_title

    if not strategic_role_match and not domain_match:
        if not (watchlist_query and target_industry_match):
            return False, "no-role-family"

    # Pure operations titles are only useful when clearly tied to the target lanes.
    if "operations" in title and not any(w in combined for w in [
        "program", "programme", "pmo", "portfolio", "delivery",
        "transformation", "digital", "technology", "it ", "head of project management"
    ]):
        return False, "operations-no-target-lane"

    return True, "pass"


def run_merge(result: AgentResult):
    """Main merge logic."""

    applied_ids = load_applied_ids()
    print(f"Loaded {len(applied_ids)} applied job IDs")

    if is_dry_run():
        print("\n=== DRY RUN: Merge Preview ===")

        source_files = list(JOBS_RAW_DIR.glob("*.json"))
        print(f"\nSource files in {JOBS_RAW_DIR}:")

        total_jobs = 0
        for f in source_files:
            data = load_json(f, {})
            if isinstance(data, list):
                jobs = data
                meta = {}
            else:
                meta = data.get("meta", {})
                jobs = data.get("jobs", data.get("data", []))
            if isinstance(jobs, list):
                count = len(jobs)
            else:
                count = 0

            status = "✅" if not is_stale(meta, FRESHNESS_HOURS) else "⚠️ STALE"
            print(f"  {status} {f.name}: {count} jobs | {meta.get('source', '?')} | {meta.get('generated_at', '?')}")
            total_jobs += count

        print(f"\nTotal jobs across sources: {total_jobs}")
        print(f"Applied IDs to filter: {len(applied_ids)}")
        print(f"Fuzzy match threshold: {FUZZY_MATCH_THRESHOLD * 100}%")

        result.set_data([])
        result.set_kpi({
            "source_files": len(source_files),
            "total_raw": total_jobs,
            "applied_ids_loaded": len(applied_ids),
        })
        return

    source_files = list(JOBS_RAW_DIR.glob("*.json"))
    print(f"Found {len(source_files)} source files")

    all_jobs_raw = []
    sources_loaded = {}
    stale_sources = []

    for f in source_files:
        data = load_json(f, {})
        # Handle raw list format (some sources output list directly)
        if isinstance(data, list):
            jobs = data
            source = f.stem
            # Use file mtime as proxy for freshness
            from datetime import datetime
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
            meta = {"generated_at": mtime.isoformat()} if age_hours < 24 else {}
        else:
            meta = data.get("meta", {})
            source = meta.get("source", f.stem)
            jobs = data.get("jobs", data.get("data", []))

        if is_stale(meta, FRESHNESS_HOURS):
            print(f"  ⚠️ Skipping stale: {f.name}")
            stale_sources.append(source)
            continue

        if not isinstance(jobs, list):
            print(f"  ⚠️ Invalid format: {f.name}")
            continue

        for job in jobs:
            job["_source_file"] = source

        all_jobs_raw.extend(jobs)
        sources_loaded[source] = len(jobs)
        print(f"  ✅ {f.name}: {len(jobs)} jobs")

    print(f"\nTotal raw jobs: {len(all_jobs_raw)}")

    # Stage 1: URL exact dedup
    seen_urls = {}
    url_deduped = []

    for job in all_jobs_raw:
        url = job.get("url", "")
        if not url:
            continue

        if url in seen_urls:
            existing = seen_urls[url]
            existing_sources = existing.get("_sources", [existing.get("_source_file", "")])
            if job.get("_source_file") not in existing_sources:
                existing_sources.append(job.get("_source_file", ""))

            # Prefer the record with more data (snippet + keyword_score)
            existing_richness = len(existing.get("raw_snippet", "") or "") + (existing.get("keyword_score") or 0)
            job_richness = len(job.get("raw_snippet", "") or "") + (job.get("keyword_score") or 0)
            if job_richness > existing_richness:
                # Replace with richer record, preserve merged sources
                job["_sources"] = existing_sources
                job["source_count"] = len(existing_sources)
                seen_urls[url] = job
                # Replace in url_deduped list
                for idx, j in enumerate(url_deduped):
                    if j.get("url") == url:
                        url_deduped[idx] = job
                        break
            else:
                existing["_sources"] = existing_sources
                existing["source_count"] = len(existing_sources)
        else:
            job["_sources"] = [job.get("_source_file", "")]
            job["source_count"] = 1
            seen_urls[url] = job
            url_deduped.append(job)

    print(f"After URL dedup: {len(url_deduped)} jobs")

    # Track per-source URL-deduped counts (for source_runs reporting)
    url_deduped_per_source = {}
    for job in url_deduped:
        for src in job.get("_sources", [job.get("_source_file", "unknown")]):
            url_deduped_per_source[src] = url_deduped_per_source.get(src, 0) + 1

    # Stage 2: Fuzzy title+company dedup
    fuzzy_deduped = []

    for job in url_deduped:
        existing = find_fuzzy_duplicate(job, fuzzy_deduped)
        if existing:
            existing_sources = existing.get("_sources", [])
            job_source = job.get("_source_file", "")
            if job_source and job_source not in existing_sources:
                existing_sources.append(job_source)
                existing["_sources"] = existing_sources
                existing["source_count"] = len(existing_sources)
        else:
            fuzzy_deduped.append(job)

    print(f"After fuzzy dedup: {len(fuzzy_deduped)} jobs")

    # Stage 3: Filter already-applied jobs
    not_applied = []
    applied_filtered = 0

    for job in fuzzy_deduped:
        job_id = job.get("id", "").split("-")[-1]
        url = job.get("url", "")

        # Check job ID directly
        if job_id in applied_ids:
            applied_filtered += 1
            continue

        # Also extract any numeric ID from URL (LinkedIn URLs contain job IDs)
        import re
        url_ids = re.findall(r'(\d{8,})', url)
        if any(uid in applied_ids for uid in url_ids):
            applied_filtered += 1
            continue

        not_applied.append(job)

    print(f"After applied filter: {len(not_applied)} jobs (removed {applied_filtered})")

    # Stage 3b: DB-backed fuzzy dedup against ALL applied jobs (by applied_date)
    # Catches same role re-posted with different URL/ID (e.g., LinkedIn reposts)
    # Bug fix: query by applied_date IS NOT NULL, not status (many applied have status='skipped')
    # Also check against all historical jobs, not just those marked 'applied'
    db_deduped = []
    db_dedup_filtered = 0
    try:
        import sqlite3
        _db = sqlite3.connect(str(Path(__file__).parent.parent / "data" / "nasr-pipeline.db"))
        applied_rows = _db.execute(
            "SELECT id, title, company, applied_date, verdict FROM jobs WHERE applied_date IS NOT NULL"
        ).fetchall()
        applied_keys = []
        for row in applied_rows:
            ak = normalize_title_company(row[1] or "", row[2] or "")
            applied_keys.append((row[0], ak, row[3], row[4]))
        _db.close()

        for job in not_applied:
            job_key = normalize_title_company(job.get("title", ""), job.get("company", ""))
            is_dup = False
            for aid, ak, apply_dt, vrd in applied_keys:
                if fuzzy_match(job_key, ak) >= 0.82:
                    db_dedup_filtered += 1
                    is_dup = True
                    break
            if not is_dup:
                db_deduped.append(job)

        print(f"After DB applied dedup: {len(db_deduped)} jobs (removed {db_dedup_filtered} duplicates of applied jobs)")
    except Exception as e:
        print(f"  Warning: DB applied dedup failed ({e}), skipping")
        db_deduped = not_applied

    # Stage 3c: Dedup against ALL historical jobs by company+title fuzzy match
    # Catches re-posted roles that we've already scored (SUBMIT/REVIEW/SKIP)
    # so we don't re-evaluate the same role under a new URL
    db_deduped2 = []
    repost_filtered = 0
    try:
        import sqlite3
        _db = sqlite3.connect(str(Path(__file__).parent.parent / "data" / "nasr-pipeline.db"))
        scored_rows = _db.execute(
            "SELECT id, title, company, verdict, url_hash FROM jobs WHERE verdict IS NOT NULL AND verdict != '' AND url_hash IS NOT NULL"
        ).fetchall()
        historical_keys = []
        for row in scored_rows:
            hk = normalize_title_company(row[1] or "", row[2] or "")
            historical_keys.append((row[0], hk, row[3], row[4]))
        _db.close()

        for job in db_deduped:
            job_key = normalize_title_company(job.get("title", ""), job.get("company", ""))
            is_repost = False
            for hid, hk, h_verdict, h_hash in historical_keys:
                # Only dedup if URL is different (same hash = already caught by URL dedup)
                job_url_hash = job.get("job_url_hash", "")
                if job_url_hash and job_url_hash == h_hash:
                    continue
                if fuzzy_match(job_key, hk) >= 0.88:
                    is_repost = True
                    break
            if not is_repost:
                db_deduped2.append(job)
            else:
                repost_filtered += 1

        print(f"After historical repost dedup: {len(db_deduped2)} jobs (removed {repost_filtered} reposts of previously scored roles)")
    except Exception as e:
        print(f"  Warning: DB dedup failed ({e}), skipping")
        db_deduped2 = db_deduped  # not_applied already in db_deduped

    # Stage 4: Apply search policy
    policy_passed = []
    policy_filtered = 0

    for job in db_deduped2:
        # Clean title first (strip location leakage)
        raw_title = job.get("title", "")
        cleaned = clean_title(raw_title)
        if cleaned != raw_title:
            job["title"] = cleaned

        # Country extraction
        job["country"] = extract_country(
            location=job.get("location", ""),
            search_country=job.get("search_country", ""),
            url=job.get("url", ""),
        )

        # Negative keyword filter (block education/HR/finance/noise titles)
        title_lower = job.get("title", "").lower()
        negated = False
        for neg_kw in NEGATIVE_TITLE_KEYWORDS:
            if neg_kw in title_lower:
                job["policy_status"] = f"negative-filter:{neg_kw}"
                policy_filtered += 1
                negated = True
                break
        if negated:
            continue

        # Industry targeting — block excluded industries
        jd_text = (job.get("jd_text", "") or "").lower()
        combined_text = f"{title_lower} {jd_text}"
        industry_blocked = False
        for exc_word in EXCLUDED_INDUSTRY_WORDS:
            if exc_word in combined_text:
                job["policy_status"] = f"excluded-industry:{exc_word}"
                policy_filtered += 1
                industry_blocked = True
                break
        if industry_blocked:
            continue

        keep, reason = apply_search_policy(job)
        if keep:
            # Bonus points for target industry match
            industry_match_count = sum(1 for w in TARGET_INDUSTRY_WORDS if w in combined_text)
            if industry_match_count > 0:
                job["industry_bonus"] = industry_match_count * 3
            job["policy_status"] = "pass"
            policy_passed.append(job)
        else:
            job["policy_status"] = reason
            policy_filtered += 1

    print(f"After policy filter: {len(policy_passed)} jobs (removed {policy_filtered})")

    # Sort by keyword score (descending) — with industry targeting boost
    def sort_key(j):
        base = j.get('keyword_score', 0)
        boost = 0
        # +5 points if job is in Ahmed's target industries
        jd_and_title = (j.get('jd_text', '') + ' ' + j.get('title', '')).lower()
        for w in TARGET_INDUSTRY_WORDS:
            if w in jd_and_title:
                boost += 5
                break  # one-time boost, not per-word
        return base + boost
    policy_passed.sort(key=sort_key, reverse=True)

    multi_source = sum(1 for j in policy_passed if j.get("source_count", 1) > 1)

    # ── First-seen tracking ──────────────────────────────────────────────
    first_seen_path = DATA_DIR / "jobs-first-seen.json"
    try:
        first_seen_db = json.loads(first_seen_path.read_text()) if first_seen_path.exists() else {}
    except Exception:
        first_seen_db = {}

    from datetime import datetime as _dt_cls
    _now_utc = _dt_cls.now(timezone.utc)
    today_str = _now_utc.strftime("%Y-%m-%d")
    new_today_count = 0

    # Clean up internal fields for output
    final_jobs = []
    for job in policy_passed:
        clean_job = {k: v for k, v in job.items() if not k.startswith("_")}
        clean_job["sources"] = job.get("_sources", [job.get("source", "")])

        # Assign first_seen
        url = clean_job.get("url", "")
        job_key = url or f"{clean_job.get('company','')}|{clean_job.get('title','')}"
        if job_key and job_key in first_seen_db:
            clean_job["first_seen"] = first_seen_db[job_key]
        else:
            clean_job["first_seen"] = today_str
            if job_key:
                first_seen_db[job_key] = today_str
            new_today_count += 1

        final_jobs.append(clean_job)

    # Prune entries older than 60 days to keep file small
    cutoff = (_now_utc - timedelta(days=60)).strftime("%Y-%m-%d")
    first_seen_db = {k: v for k, v in first_seen_db.items() if v >= cutoff}
    first_seen_path.write_text(json.dumps(first_seen_db, indent=2))
    print(f"First-seen: {new_today_count} new today, {len(first_seen_db)} tracked")
    # ─────────────────────────────────────────────────────────────────────

    print(f"\nFinal candidates: {len(final_jobs)}")
    print(f"Multi-source jobs: {multi_source}")

    # ── DB write (dual-write, non-blocking) ───────────────────────────────────
    if _pdb:
        try:
            db_count = 0
            # Track per-source DB insert counts for source_runs reporting
            db_registered_per_source = {}
            # Collect per-source title/country aggregates for source_runs logging
            titles_per_source = {}
            countries_per_source = {}

            # Canonical source map: resolve raw source names to canonical names
            # linkedin_jobspy jobs have source='linkedin_jobspy' in JSON but should use 'linkedin'
            _canonical = {src: src for src in sources_loaded}
            _canonical.update({"linkedin_jobspy": "linkedin", "google_jobs": "google-jobs"})

            for j in final_jobs:
                raw_src = j.get("source", "unknown")
                job_source = j.get("_source_file") or _canonical.get(raw_src, raw_src)
                _pdb.register_job(
                    source=job_source,
                    job_id=str(j.get("id", j.get("job_id", ""))) if j.get("id", j.get("job_id")) else "",
                    company=j.get("company", "Unknown"),
                    title=j.get("title", "Unknown"),
                    location=j.get("location"),
                    country=j.get("country", "Unknown"),
                    url=j.get("url"),
                    jd_text=j.get("jd_text") or j.get("raw_snippet") or None,
                    search_country=j.get("search_country"),
                    search_title=j.get("search_title"),
                    status="discovered",
                )
                db_count += 1
                db_registered_per_source[job_source] = db_registered_per_source.get(job_source, 0) + 1

                # Aggregate titles and countries for reporting
                title = j.get("title", "Unknown") or "Unknown"
                country = j.get("country", "Unknown") or "Unknown"
                titles_per_source.setdefault(job_source, {})[title] = titles_per_source.get(job_source, {}).get(title, 0) + 1
                countries_per_source.setdefault(job_source, {})[country] = countries_per_source.get(job_source, {}).get(country, 0) + 1

            print(f"  DB: {db_count} jobs upserted")

            # ── Log source_runs for each source (per-source isolation) ───────────
            import json as _json
            logged_sources = []
            for src, raw_count in sources_loaded.items():
                try:
                    unique_count = url_deduped_per_source.get(src, 0)
                    reg_count = db_registered_per_source.get(src, 0)
                    titles_json = _json.dumps(
                        dict(sorted(titles_per_source.get(src, {}).items(), key=lambda x: -x[1])[:10])
                    )
                    countries_json = _json.dumps(countries_per_source.get(src, {}))
                    _pdb.log_source_run(
                        source=src,
                        raw_count=raw_count,
                        unique_count=unique_count,
                        db_registered=reg_count,
                        countries_json=countries_json,
                        titles_json=titles_json,
                        duration_ms=0,
                        errors=0,
                    )
                    logged_sources.append(src)
                except Exception as _ls_e:
                    print(f"  source_runs failed for '{src}': {_ls_e}")
            print(f"  source_runs: logged for {len(logged_sources)}/{len(sources_loaded)} sources: {logged_sources}")
            # ───────────────────────────────────────────────────────────────────

        except Exception as _e:
            import traceback
            traceback.print_exc()
            print(f"  DB write failed (non-fatal): {_e}")
    # ─────────────────────────────────────────────────────────────────────────

    result.set_data(final_jobs)
    result.set_kpi({
        "total_raw": len(all_jobs_raw),
        "sources_loaded": len(sources_loaded),
        "stale_sources": len(stale_sources),
        "unique_after_dedup": len(fuzzy_deduped),
        "applied_filtered": applied_filtered,
        "policy_filtered": policy_filtered,
        "final_candidates": len(final_jobs),
        "multi_source_jobs": multi_source,
        "new_today": len(final_jobs),
    })


def main():
    """Entry point."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(
        agent_name=AGENT_NAME,
        run_func=run_merge,
        output_path=OUTPUT_FILE,
        ttl_hours=6,
        version="1.0.0"
    )


if __name__ == "__main__":
    main()
