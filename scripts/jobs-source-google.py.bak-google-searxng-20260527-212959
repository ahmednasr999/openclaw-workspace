#!/usr/bin/env python3
"""
jobs-source-google.py — Web Aggregator via Exa AI search (v3).

Strategy: Discover executive jobs across MULTIPLE job boards that our
LinkedIn/Indeed-only scrapers miss. Three-phase approach:

  Phase 1a: Exa keyword search → broad discovery across all boards
  Phase 1b: Exa auto search + includeDomains → targeted discovery on GCC boards
  Phase 1c: Exa neural catch-all → unconventional postings
  Phase 2:  Classify URLs (single job vs listing page vs noise)
  Phase 3:  EXA_GET_CONTENTS on listing pages → extract individual jobs from text
  Phase 4:  DB write + output

Output: data/jobs-raw/google-jobs.json
"""

import hashlib
import json
import re
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from _imports import agent_common, jobs_source_common

# Agent framework
AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
load_json = agent_common.load_json
WORKSPACE = agent_common.WORKSPACE
DATA_DIR = agent_common.DATA_DIR
JOBS_RAW_DIR = agent_common.JOBS_RAW_DIR

# Job search config
ALL_TITLES = jobs_source_common.ALL_TITLES
PRIORITY_COUNTRIES = jobs_source_common.PRIORITY_COUNTRIES
COUNTRY_SEARCH_TERMS = jobs_source_common.COUNTRY_SEARCH_TERMS
GCC_COUNTRIES = jobs_source_common.GCC_COUNTRIES
standard_job_dict = jobs_source_common.standard_job_dict

# Pipeline DB
try:
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

# Configuration
AGENT_NAME = "jobs-source-google"
OUTPUT_FILE = JOBS_RAW_DIR / "google-jobs.json"
CONFIG_FILE = Path("/root/.openclaw/openclaw.json")
WATCHLIST_FILE = DATA_DIR / "sayyad-company-watchlist.json"
COMPOSIO_MCP_URL = "https://connect.composio.dev/mcp"
RATE_LIMIT_DELAY = 1.2  # seconds between Exa calls
RECENCY_DAYS = 10

# ── GCC job boards to discover (NOT already covered by our linkedin/indeed sources) ──
DISCOVERY_BOARDS = [
    "bayt.com", "gulftalent.com", "naukrigulf.com", "founditgulf.com",
    "glassdoor.com", "michaelpage.ae", "michaelpage.com", "hays.ae",
    "roberthalf.ae", "careerjet.ae", "jooble.org", "drjobpro.com",
    # "wuzzuf.net",  # Disabled 2026-04-05 — Egyptian portal, irrelevant for GCC
    "jobaaj.com", "interviewpal.com",
]

# Consolidated title groups for keyword searches.
# Google is our highest-yield discovery source, so bias toward Ahmed's exact role lanes.
TITLE_GROUPS = [
    '"Director Digital Transformation" OR "VP Digital Transformation" OR "Head of Digital Transformation" OR "Chief Digital Officer"',
    '"Chief Technology Officer" OR "CTO" OR "Chief Information Officer" OR "CIO" OR "Head of Technology" OR "IT Director" OR "Head of IT"',
    '"PMO Director" OR "Program Director" OR "Head of PMO" OR "Director of Program Management"',
    '"Portfolio Director" OR "Delivery Director" OR "Head of Delivery" OR "EPMO Director" OR "Programme Manager"',
    '"Head of Transformation" OR "Business Excellence Director" OR "Operational Excellence Director" OR "Transformation Director"',
]

LOCATION_GROUPS = [
    "Dubai OR Abu Dhabi OR UAE",
    "Riyadh OR Saudi Arabia OR KSA",
    "Doha OR Qatar",
    "Bahrain OR Kuwait OR Oman",
]

# For auto+includeDomains searches (more specific)
AUTO_TITLE_GROUPS = [
    "Director OR VP digital transformation technology hiring GCC",
    "CTO OR CIO OR Chief Technology Officer hiring GCC",
    "Head of IT OR IT Director OR Head of Technology hiring GCC",
    "Program Director OR PMO Director OR Director of Program Management hiring GCC",
    "Portfolio Director OR Delivery Director OR EPMO Director hiring GCC",
    "Head of Transformation OR Business Excellence Director hiring GCC",
]

AUTO_LOCATION_GROUPS = [
    "Dubai Abu Dhabi UAE",
    "Riyadh Saudi Arabia KSA",
    "Doha Qatar Bahrain Kuwait",
]

# ── URL classification ────────────────────────────────────────────────────

SINGLE_JOB_PATTERNS = [
    r'linkedin\.com/jobs/view/\d+',
    r'indeed\.com/viewjob',
    r'indeed\.com/rc/clk',
    r'glassdoor\.com/job-listing/',
    r'bayt\.com/en/.+/jobs/.+/\d+',
    r'gulftalent\.com/\w+/jobs/.+-\d+$',
    r'naukrigulf\.com/.*-jid-\d+',
    r'drjobpro\.com/.*job/',
    r'jooble\.org/jdp/',
    r'michaelpage\..+/job-detail/',
    r'jobaaj\.com/job/',
    r'interviewpal\.com/jobs/\d+',
    r'founditgulf\.com/job/',
]

NOISE_PATTERNS = [
    r'instagram\.com', r'twitter\.com', r'x\.com/(?!jobs)',
    r'youtube\.com', r'facebook\.com', r'wikipedia\.org',
    r'gartner\.com/en/conferences', r'event\.', r'summit',
    r'gulftalent\.com/people/',  # people profiles, not jobs
    r'theorg\.com/org/', r'adapt\.io/contact/',
    r'digitaljournal\.com', r'cio\.com/article/',
    r'eyeofriyadh\.com', r'globalaishow\.com',
    r'milestonesglobal\.com', r'svarecruitment\.com',
    r'mitsloanme\.com', r'wuzzuf\.net',
]

LOCATION_MAP = {
    "dubai": "Dubai, UAE", "abu dhabi": "Abu Dhabi, UAE", "abu-dhabi": "Abu Dhabi, UAE",
    "uae": "UAE", "riyadh": "Riyadh, Saudi Arabia", "saudi": "Saudi Arabia",
    "ksa": "Saudi Arabia", "doha": "Doha, Qatar", "qatar": "Qatar",
    "bahrain": "Bahrain", "kuwait": "Kuwait", "oman": "Oman",
}


def load_composio_key() -> str:
    try:
        config = load_json(CONFIG_FILE)
        return config.get("plugins", {}).get("entries", {}).get("composio", {}).get("config", {}).get("consumerKey", "")
    except Exception:
        return ""


def load_watchlist() -> dict:
    try:
        data = load_json(WATCHLIST_FILE)
        return {
            "priority_companies": data.get("priority_companies", []),
            "priority_domains": data.get("priority_domains", []),
        }
    except Exception:
        return {"priority_companies": [], "priority_domains": []}


def mcp_call(method: str, params: dict, consumer_key: str, timeout: int = 45) -> dict | None:
    import requests
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "x-consumer-api-key": consumer_key,
    }
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1000000,
        "method": method,
        "params": params,
    }
    try:
        resp = requests.post(COMPOSIO_MCP_URL, json=payload, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            print(f"    MCP HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        for line in resp.text.split("\n"):
            if line.startswith("data:"):
                data = json.loads(line[5:].strip())
                if "error" in data:
                    print(f"    MCP error: {data['error']}")
                    return None
                return data.get("result", {})
        return None
    except Exception as e:
        print(f"    MCP error: {e}")
        return None


def mcp_initialize(consumer_key: str) -> bool:
    result = mcp_call("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "jobs-source-google", "version": "3.0"},
    }, consumer_key)
    return result is not None


def _parse_exa_response(result: dict) -> list[dict]:
    """Parse nested Composio MCP → Exa response into list of result dicts."""
    if not result:
        return []
    try:
        content = result.get("content", [])
        if not content:
            return []
        text = content[0].get("text", "")
        if not text:
            return []
        outer = json.loads(text)
        if not outer.get("successful"):
            return []
        results_list = outer.get("data", {}).get("results", [])
        if not results_list:
            return []
        inner = results_list[0].get("response", {})
        if not inner.get("successful"):
            return []
        return inner.get("data", {}).get("results", [])
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"    Parse error: {e}")
        return []


def exa_search(query: str, consumer_key: str, search_type: str = "keyword",
               num_results: int = 15, include_domains: list = None,
               exclude_domains: list = None, start_date: str = None) -> list[dict]:
    """Unified search via COMPOSIO_SEARCH_WEB (free, no Exa credits needed)."""
    result = mcp_call("tools/call", {
        "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
        "arguments": {
            "tools": [{"tool_slug": "COMPOSIO_SEARCH_WEB", "arguments": {"query": query}}],
            "sync_response_to_workbench": False,
        },
    }, consumer_key, timeout=45)
    # Parse COMPOSIO_SEARCH_WEB response (citations format) into Exa-like result dicts
    if not result:
        return []
    try:
        content = result.get("content", [])
        if not content:
            return []
        text = content[0].get("text", "")
        if not text:
            return []
        outer = json.loads(text)
        if not outer.get("successful"):
            return []
        results_list = outer.get("data", {}).get("results", [])
        if not results_list:
            return []
        inner = results_list[0].get("response", {})
        if not inner.get("successful"):
            return []
        citations = inner.get("data", {}).get("citations", [])
        # Convert citations to Exa-like result dicts
        results = []
        for c in citations:
            results.append({"url": c.get("url", ""), "title": c.get("title", ""),
                           "text": c.get("snippet", "") or c.get("text", "")})
        return results
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"    COMPOSIO_SEARCH_WEB parse error: {e}")
        return []


def exa_get_contents(urls: list[str], consumer_key: str, max_chars: int = 5000) -> list[dict]:
    """Fetch page contents via COMPOSIO_SEARCH_FETCH_URL_CONTENT (free, no Exa credits)."""
    results = []
    for url in urls:
        result = mcp_call("tools/call", {
            "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
            "arguments": {
                "tools": [{"tool_slug": "COMPOSIO_SEARCH_FETCH_URL_CONTENT", "arguments": {
                    "urls": [url],
                    "max_characters": max_chars,
                }}],
                "sync_response_to_workbench": False,
            },
        }, consumer_key, timeout=60)
        if not result:
            continue
        try:
            content = result.get("content", [])
            if not content:
                continue
            text = content[0].get("text", "")
            if not text:
                continue
            outer = json.loads(text)
            if not outer.get("successful"):
                continue
            results_list = outer.get("data", {}).get("results", [])
            if not results_list:
                continue
            inner = results_list[0].get("response", {})
            if not inner.get("successful"):
                continue
            fetched = inner.get("data", {}).get("results", [])
            for item in fetched:
                results.append({"url": item.get("url", url), "text": item.get("text", "")})
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"    FETCH_URL_CONTENT parse error: {e}")
    return results


def classify_url(url: str) -> str:
    """Classify URL as 'single_job', 'listing_page', or 'noise'."""
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return "noise"
    for pattern in SINGLE_JOB_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return "single_job"
    # Check if on a known job board
    for domain in DISCOVERY_BOARDS:
        if domain in url:
            return "listing_page"
    return "noise"


def extract_location(text: str) -> str:
    """Extract GCC location from text."""
    text_lower = text.lower()
    for term, loc in LOCATION_MAP.items():
        if term in text_lower:
            return loc
    return "GCC"


def extract_job_from_exa_result(result: dict) -> dict | None:
    """Convert an Exa result (single job URL) into a standard job dict."""
    url = result.get("url", "")
    if not url:
        return None

    raw_title = result.get("title", "")

    # Clean title: remove site names
    title = re.sub(
        r'\s*[\|–\-]\s*(LinkedIn|Indeed|GulfTalent|Glassdoor|Bayt\.com|NaukriGulf|'
        r'Michael Page|Hays|Robert Half|FounditGulf|CareerJet|Jooble|DrJobPro|'
        r'Apply Now|Jobaaj|InterviewPal).*$',
        '', raw_title, flags=re.IGNORECASE
    ).strip()

    # Handle "Company hiring Title in Location" pattern
    hiring_match = re.match(r'^(.+?)\s+hiring\s+(.+?)(?:\s+in\s+.+)?$', title, re.IGNORECASE)
    company_from_title = None
    if hiring_match:
        company_from_title = hiring_match.group(1).strip()
        title = hiring_match.group(2).strip()

    # Extract company from "at Company" pattern
    company = "Confidential"
    at_match = re.search(r'\s+at\s+(.+?)(?:\s*[\|–\-]|$)', raw_title, re.IGNORECASE)
    if at_match:
        company = at_match.group(1).strip()
        title = re.sub(r'\s+at\s+' + re.escape(company) + r'.*$', '', title, flags=re.IGNORECASE).strip()
    elif company_from_title:
        company = company_from_title

    # Handle "Title with X Years of Experience at Company in Location" (FounditGulf)
    foundit_match = re.match(r'^(.+?)\s+with\s+\d+\s*-\s*\d+\s+Years?\s+of\s+Experience\s+at\s+(.+?)\s+in\s+(.+)', title, re.IGNORECASE)
    if foundit_match:
        title = foundit_match.group(1).strip()
        company = foundit_match.group(2).strip()

    # Handle "Apply to Title Job at Location in Company" (Jobaaj)
    jobaaj_match = re.match(r'^Apply to\s+(.+?)\s+Job\s+at\s+.+?\s+location\s+in\s+(.+?)(?:,|$)', title, re.IGNORECASE)
    if jobaaj_match:
        title = jobaaj_match.group(1).strip()
        company = jobaaj_match.group(2).strip()

    # Remove "Position Closed" suffix
    title = re.sub(r'\s*\|\s*Position Closed\s*$', '', title, flags=re.IGNORECASE).strip()

    location = extract_location(raw_title + " " + url)
    job_id = hashlib.sha256(url.encode()).hexdigest()[:12]
    posted = result.get("publishedDate", "")[:10] if result.get("publishedDate") else ""

    return standard_job_dict(
        job_id=job_id,
        source="google",
        title=title if title else "Executive Role",
        company=company,
        location=location,
        url=url,
        posted=posted,
        raw_snippet=result.get("text", "")[:500] if result.get("text") else "",
    )


# Domain keywords — jobs from listing pages MUST match these (stricter than direct results)
DOMAIN_MUST_MATCH = [
    "digital", "technology ", "tech ", "it ", "i.t.", " data", "analytics",
    "transformation", "innovation", "software", "engineering director",
    "engineering manager", "cto", "cio", "cdo",
    "chief technology", "chief digital", "chief information",
    "chief data", "pmo", "program director", "program manager",
    "devops", "cloud", "cyber", "ai ", "artificial intelligence",
    "machine learning", "product", "platform", "automation",
    "erp", "sap", "agile", "scrum",
]

NON_GCC_LOCATIONS = ["egypt", "cairo", "india", "pakistan", "jordan", "lebanon",
                     "morocco", "tunisia", "iraq", "syria", "libya", "yemen"]


def _listing_job_is_relevant(title: str, location: str) -> bool:
    """Stricter relevancy for jobs parsed from listing pages: must match tech domain."""
    t = title.lower()
    loc = location.lower()
    if any(x in loc for x in NON_GCC_LOCATIONS):
        return False
    if not any(kw in t for kw in DOMAIN_MUST_MATCH):
        return False
    return True


def parse_jobs_from_listing_text(text: str, page_url: str) -> list[dict]:
    """
    Parse structured job listings from extracted page text (e.g., Bayt listing pages).
    Returns list of parsed job dicts.
    """
    # Fix encoding: "Â·" → "·"
    text = text.replace("\u00c2\u00b7", "·").replace("Â·", "·")
    jobs = []

    # Pattern 1: Bayt-style "## Title\nCompany\nLocation\nSummary: ..."
    bayt_pattern = re.compile(
        r'##\s+(.+?)\n+([A-Z][\w\s&\-\.]+?)\n+([A-Z][\w\s,·]+?)(?:\n|$)',
        re.MULTILINE
    )
    for match in bayt_pattern.finditer(text):
        raw_title = match.group(1).strip()
        company = match.group(2).strip()
        location = match.group(3).strip()

        # Skip non-job matches
        if any(skip in raw_title.lower() for skip in ['filter', 'sign up', 'submit', 'select']):
            continue
        if len(raw_title) < 5 or len(raw_title) > 100:
            continue
        if len(company) < 2 or len(company) > 60:
            continue

        # Clean location
        location = re.sub(r'^[\s·]+', '', location).replace("Â·", ",").replace("·", ",").strip()

        job_id = hashlib.sha256((raw_title + company).encode()).hexdigest()[:12]
        job = standard_job_dict(
            job_id=job_id,
            source="google",
            title=raw_title,
            company=company,
            location=location if location else extract_location(text),
            url=page_url,
            posted="",
            raw_snippet="",
        )
        if job.get("relevant", False) and _listing_job_is_relevant(raw_title, location):
            jobs.append(job)

    # Pattern 2: GulfTalent similar jobs table "| Title Company | Location | Date |"
    gt_pattern = re.compile(r'\|\s+(.+?)\s+\|\s+([A-Z][\w\s,]+?)\s+\|\s+\d+\s+\w+\s+\|')
    for match in gt_pattern.finditer(text):
        title_company = match.group(1).strip()
        location = match.group(2).strip()

        # Split title and company (last word group is usually company)
        parts = re.split(r'\s{2,}', title_company)
        if len(parts) >= 2:
            raw_title = parts[0].strip()
            company = parts[-1].strip()
        else:
            raw_title = title_company
            company = "Confidential"

        if len(raw_title) < 5:
            continue

        job_id = hashlib.sha256((raw_title + company).encode()).hexdigest()[:12]
        job = standard_job_dict(
            job_id=job_id,
            source="google",
            title=raw_title,
            company=company,
            location=location,
            url=page_url,
            posted="",
            raw_snippet="",
        )
        if job.get("relevant", False) and _listing_job_is_relevant(raw_title, location):
            jobs.append(job)

    # Pattern 3: Glassdoor-style or generic "Title - Company - Location"
    generic_pattern = re.compile(r'^(.{10,80}?)\s*[-–]\s*(.{3,50}?)\s*[-–]\s*(.{3,50})$', re.MULTILINE)
    for match in generic_pattern.finditer(text):
        raw_title = match.group(1).strip()
        company = match.group(2).strip()
        location = match.group(3).strip()

        if any(skip in raw_title.lower() for skip in ['filter', 'sign up', 'cookie', 'privacy']):
            continue

        job_id = hashlib.sha256((raw_title + company).encode()).hexdigest()[:12]
        job = standard_job_dict(
            job_id=job_id,
            source="google",
            title=raw_title,
            company=company,
            location=location if location else "GCC",
            url=page_url,
            posted="",
            raw_snippet="",
        )
        if job.get("relevant", False) and _listing_job_is_relevant(raw_title, location):
            jobs.append(job)

    return jobs


BAD_TITLE_PHRASES = [
    "didn't find the right",
    "create job alert",
    "job alert to receive",
    "refine your search",
    "search results for",
]

EMPLOYMENT_TYPE_LOCATIONS = {
    "permanent", "temporary", "contract", "full time", "part time",
}

LOCATION_LIKE_COMPANIES = {
    "united arab emirates", "uae", "saudi arabia", "riyadh", "jeddah",
    "dubai", "abu dhabi", "qatar", "doha", "oman", "muscat",
    "kuwait", "kuwait city", "bahrain", "manama",
}

GENERIC_COMPANY_WORDS = {
    "infrastructure", "semi", "government", "contractor", "telecom",
    "retail", "healthcare", "banking", "technology",
}


def normalize_google_job(job: dict) -> dict:
    """Clean obvious title/company formatting artefacts before malformed checks."""
    normalized = dict(job)
    title = (normalized.get("title", "") or "").strip()
    company = (normalized.get("company", "") or "").strip()
    url = (normalized.get("url", "") or "").strip().lower()

    title = re.sub(r'^\s*[#*\-]+\s*', '', title).strip()

    if "jobaaj.com/job/" in url:
        title = re.sub(r'^Apply to\s+', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'\s+Job$', '', title, flags=re.IGNORECASE).strip()
        if company.lower() in LOCATION_LIKE_COMPANIES:
            company = "Confidential"

    by_match = re.match(r'^(.*?)\s*\|\s*Jobs?\s+in\s+.+?\s+by\s+(.+)$', title, re.IGNORECASE)
    if by_match:
        title = by_match.group(1).strip()
        if company.lower() == "confidential":
            company = by_match.group(2).strip()

    normalized["title"] = title
    normalized["company"] = company
    return normalized


def is_malformed_google_job(job: dict) -> tuple[bool, str]:
    """Drop listing-page boilerplate or malformed rows before DB write."""
    title = (job.get("title", "") or "").strip().lower()
    company = (job.get("company", "") or "").strip().lower()
    location = (job.get("location", "") or "").strip().lower()
    url = (job.get("url", "") or "").strip().lower()

    if any(phrase in title for phrase in BAD_TITLE_PHRASES):
        return True, "bad-title-phrase"

    if company in {"create an alert", "create job alert"}:
        return True, "alert-boilerplate"

    if location.startswith("create job alert") or location.startswith("job alert to receive"):
        return True, "alert-location"

    if location in EMPLOYMENT_TYPE_LOCATIONS:
        return True, "employment-type-as-location"

    if "michaelpage" in url and company in LOCATION_LIKE_COMPANIES:
        return True, "location-as-company"

    if "michaelpage" in url and company in GENERIC_COMPANY_WORDS:
        return True, "generic-company-from-listing"

    if title != title.lstrip('#*- ').strip():
        return True, "markdown-title-artifact"

    if company in GENERIC_COMPANY_WORDS and location in {"government", "semi-government", "tier 1 contractor - dubai"}:
        return True, "generic-company-location-pair"

    return False, "ok"


def run_google_scanner(result: AgentResult):
    """Main scanner: three-phase Exa search → classify → extract."""

    consumer_key = load_composio_key()
    if not consumer_key:
        result.set_error("No Composio consumer key found in openclaw.json")
        return

    if is_dry_run():
        kw_total = len(TITLE_GROUPS) * len(LOCATION_GROUPS)
        auto_total = len(AUTO_TITLE_GROUPS) * len(AUTO_LOCATION_GROUPS)
        neural_total = 3
        total = kw_total + auto_total + neural_total
        print(f"\n=== DRY RUN: {total} searches planned ===")
        print(f"  Keyword: {kw_total} | Auto+domain: {auto_total} | Neural: {neural_total}")
        result.set_data([])
        result.set_kpi({"searches_planned": total, "keyword": kw_total, "auto": auto_total, "neural": neural_total})
        return

    # Initialize MCP
    print("Initializing Composio MCP...")
    if not mcp_initialize(consumer_key):
        result.set_error("Failed to initialize MCP session")
        return
    print("  MCP session initialized ✓")

    start_date = (datetime.now() - timedelta(days=RECENCY_DAYS)).strftime("%Y-%m-%d")
    watchlist = load_watchlist()
    watch_companies = watchlist.get("priority_companies", [])
    watch_domains = watchlist.get("priority_domains", [])
    all_exa_results = []
    searches_run = 0
    errors = 0

    # ── Phase 1a: Keyword searches (broad, no domain filter) ────────────
    kw_total = len(TITLE_GROUPS) * len(LOCATION_GROUPS)
    print(f"\n=== Phase 1a: Keyword discovery ({kw_total} queries) ===")

    for title_group in TITLE_GROUPS:
        for location_group in LOCATION_GROUPS:
            searches_run += 1
            query = f"{title_group} job {location_group} 2026"
            results = exa_search(query, consumer_key, search_type="keyword", num_results=15)
            if not results:
                errors += 1
            else:
                all_exa_results.extend(results)
            if searches_run % 8 == 0:
                print(f"  Progress: {searches_run}/{kw_total} | results: {len(all_exa_results)}")
            time.sleep(RATE_LIMIT_DELAY)

    print(f"  Keyword done: {len(all_exa_results)} results")

    # ── Phase 1b: Auto + includeDomains (targeted GCC boards) ──────────
    auto_total = len(AUTO_TITLE_GROUPS) * len(AUTO_LOCATION_GROUPS)
    print(f"\n=== Phase 1b: Auto+domain discovery ({auto_total} queries) ===")

    before_auto = len(all_exa_results)
    for title_q in AUTO_TITLE_GROUPS:
        for loc_q in AUTO_LOCATION_GROUPS:
            searches_run += 1
            query = f"{title_q} {loc_q} 2026"
            results = exa_search(
                query, consumer_key, search_type="auto",
                num_results=20, include_domains=DISCOVERY_BOARDS,
                start_date=start_date,
            )
            if not results:
                errors += 1
            else:
                all_exa_results.extend(results)
            time.sleep(RATE_LIMIT_DELAY)

    print(f"  Auto done: {len(all_exa_results) - before_auto} new results")

    # ── Phase 1c: Neural catch-all ──────────────────────────────────────
    neural_queries = [
        "executive technology leadership role hiring GCC Middle East 2026",
        "digital transformation director VP hiring Dubai Abu Dhabi Riyadh 2026",
        "CIO CTO CDO senior role opening Gulf region 2026",
    ]
    print(f"\n=== Phase 1c: Neural catch-all ({len(neural_queries)} queries) ===")

    before_neural = len(all_exa_results)
    for nq in neural_queries:
        searches_run += 1
        results = exa_search(
            nq, consumer_key, search_type="neural",
            num_results=15, start_date=start_date,
            exclude_domains=["instagram.com", "youtube.com", "twitter.com",
                             "x.com", "facebook.com", "wikipedia.org"],
        )
        if results:
            all_exa_results.extend(results)
        else:
            errors += 1
        time.sleep(RATE_LIMIT_DELAY)

    print(f"  Neural done: {len(all_exa_results) - before_neural} new results")

    # ── Phase 1d: Watchlist company discovery ─────────────────────────────
    if watch_companies:
        print(f"\n=== Phase 1d: Watchlist company discovery ({len(watch_companies)} queries) ===")
        before_watch = len(all_exa_results)
        for company in watch_companies:
            searches_run += 1
            query = f'("{company}" AND ("digital transformation" OR PMO OR "program director" OR CTO OR CIO OR "head of IT" OR "business excellence")) GCC job 2026'
            results = exa_search(query, consumer_key, search_type="keyword", num_results=10, start_date=start_date)
            if results:
                for item in results:
                    item["watchlist_company"] = company
                all_exa_results.extend(results)
            else:
                errors += 1
            time.sleep(RATE_LIMIT_DELAY)
        print(f"  Watchlist done: {len(all_exa_results) - before_watch} new results")

    # ── Phase 1e: Watchlist career page discovery ──────────────────────────
    if watch_companies:
        print(f"\n=== Phase 1e: Watchlist career-page discovery ({len(watch_companies)} queries) ===")
        before_careers = len(all_exa_results)
        for company in watch_companies:
            searches_run += 1
            query = f'("{company}" AND (careers OR jobs OR hiring) AND ("digital transformation" OR PMO OR "program director" OR CTO OR CIO OR "head of IT")) GCC'
            results = exa_search(
                query, consumer_key, search_type="keyword", num_results=8,
                include_domains=["bayt.com", "gulftalent.com", "greenhouse.io", "lever.co", "smartrecruiters.com", "workday.com"],
                start_date=start_date,
            )
            if results:
                for item in results:
                    item["watchlist_company"] = company
                    item["watchlist_careers"] = True
                all_exa_results.extend(results)
            else:
                errors += 1
            time.sleep(RATE_LIMIT_DELAY)
        print(f"  Career-page discovery done: {len(all_exa_results) - before_careers} new results")

    print(f"\nPhase 1 total: {len(all_exa_results)} raw results from {searches_run} queries ({errors} errors)")

    # ── Phase 2: Classify URLs ──────────────────────────────────────────
    print(f"\n=== Phase 2: Classify URLs ===")

    seen_urls = set()
    all_jobs = []
    listing_pages = []
    stats = {"single_job": 0, "listing_page": 0, "noise": 0}

    for r in all_exa_results:
        url = r.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        url_type = classify_url(url)
        stats[url_type] = stats.get(url_type, 0) + 1

        if url_type == "single_job":
            job = extract_job_from_exa_result(r)
            if job and job.get("relevant", False):
                all_jobs.append(job)
        elif url_type == "listing_page":
            listing_pages.append(url)

    print(f"  Single jobs: {stats['single_job']} | Listing pages: {stats['listing_page']} | Noise: {stats['noise']}")
    print(f"  Relevant single jobs: {len(all_jobs)}")

    # ── Phase 3: Extract jobs from listing pages via EXA_GET_CONTENTS ───
    if listing_pages:
        # Filter to boards where EXA_GET_CONTENTS works well
        good_boards = ["bayt.com", "gulftalent.com", "glassdoor.com",
                       "michaelpage", "founditgulf.com"]
        # wuzzuf.net removed 2026-04-05 — Egyptian portal, irrelevant for GCC
        extractable = [u for u in listing_pages
                       if any(b in u for b in good_boards)]
        # Cap at 15 to avoid excessive API costs
        pages_to_extract = extractable[:15]

        if pages_to_extract:
            print(f"\n=== Phase 3: Extracting from {len(pages_to_extract)} listing pages ===")

            # Batch into groups of 5 (EXA_GET_CONTENTS handles multiple URLs)
            for batch_start in range(0, len(pages_to_extract), 5):
                batch = pages_to_extract[batch_start:batch_start + 5]
                print(f"  Fetching batch {batch_start // 5 + 1}: {len(batch)} pages...")

                contents = exa_get_contents(batch, consumer_key, max_chars=6000)
                for content_item in contents:
                    page_url = content_item.get("url", "")
                    page_text = content_item.get("text", "")
                    if not page_text or len(page_text) < 200:
                        continue

                    parsed = parse_jobs_from_listing_text(page_text, page_url)
                    if parsed:
                        # Dedup against already found jobs
                        for job in parsed:
                            job_key = (job.get("title", "").lower(), job.get("company", "").lower())
                            if job_key not in seen_urls:
                                seen_urls.add(job_key)
                                all_jobs.append(job)
                        print(f"    {page_url[:60]}... → {len(parsed)} jobs parsed")

                time.sleep(RATE_LIMIT_DELAY)

    # ── Phase 4: DB write ─────────────────────────────────────────────────
    # Dedup all_jobs by URL
    final_jobs = []
    final_urls = set()
    malformed_filtered = 0
    for raw_job in all_jobs:
        j = normalize_google_job(raw_job)
        malformed, malformed_reason = is_malformed_google_job(j)
        if malformed:
            malformed_filtered += 1
            j["filter_reason"] = malformed_reason
            continue
        url = j.get("url", "")
        if url not in final_urls:
            final_urls.add(url)
            final_jobs.append(j)

    if malformed_filtered:
        print(f"  Malformed rows filtered: {malformed_filtered}")

    watch_company_hits = 0
    watch_domain_hits = 0
    for j in final_jobs:
        company_lower = (j.get("company", "") or "").lower()
        text_blob = f"{j.get('title','')} {j.get('raw_snippet','')} {j.get('company','')}".lower()
        matched_companies = [c for c in watch_companies if c.lower() in company_lower]
        matched_domains = [d for d in watch_domains if d.lower() in text_blob]
        if matched_companies:
            watch_company_hits += 1
            j["watchlist_company"] = matched_companies[0]
        if matched_domains:
            watch_domain_hits += 1
            j["watchlist_domain"] = matched_domains[0]

    print(f"\n=== Final: {len(final_jobs)} unique relevant jobs ===")
    if watch_company_hits or watch_domain_hits:
        print(f"  Watchlist hits: company={watch_company_hits}, domain={watch_domain_hits}")

    if _pdb:
        try:
            db_count = 0
            countries_seen = {}
            titles_seen = {}
            for j in final_jobs:
                _pdb.register_job(
                    source="google",
                    job_id=j.get("id", ""),
                    company=j.get("company", "Unknown"),
                    title=j.get("title", "Unknown"),
                    location=j.get("location"),
                    url=j.get("url"),
                    jd_text=j.get("raw_snippet") or None,
                    country=j.get("search_country"),
                    search_country=j.get("search_country"),
                    search_title=j.get("search_title"),
                )
                db_count += 1
                sc = j.get("search_country") or j.get("country") or "Unknown"
                st = j.get("search_title") or j.get("title") or "Unknown"
                countries_seen[sc] = countries_seen.get(sc, 0) + 1
                titles_seen[st] = titles_seen.get(st, 0) + 1
            print(f"  DB: {db_count} jobs registered")

            import json as _json
            _pdb.log_source_run(
                source="google",
                raw_count=len(all_exa_results),
                unique_count=len(final_jobs),
                db_registered=db_count,
                countries_json=_json.dumps(countries_seen),
                titles_json=_json.dumps(dict(sorted(titles_seen.items(), key=lambda x: -x[1])[:10])),
                duration_ms=0,
                errors=errors,
            )
            print(f"  source_runs: logged")
        except Exception as e:
            print(f"  DB write failed (non-fatal): {e}")

    result.set_data(final_jobs)
    result.set_kpi({
        "searches_run": searches_run,
        "exa_results_raw": len(all_exa_results),
        "single_jobs_direct": stats.get("single_job", 0),
        "listing_pages_found": stats.get("listing_page", 0),
        "listing_pages_extracted": min(len([u for u in listing_pages if any(b in u for b in ["bayt", "gulftalent", "glassdoor", "michaelpage", "founditgulf"])]), 15),
        "noise_filtered": stats.get("noise", 0),
        "malformed_filtered": malformed_filtered,
        "unique_jobs_final": len(final_jobs),
        "errors": errors,
        "exa_cost_estimate_usd": round(searches_run * 0.007 + min(len(listing_pages), 15) * 0.003, 3),
        "strategy": "Exa keyword + auto(domain) + neural + watchlist company discovery → classify → GET_CONTENTS",
        "watchlist_companies": len(watch_companies),
    })


if __name__ == "__main__":
    JOBS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(AGENT_NAME, run_google_scanner, OUTPUT_FILE)
