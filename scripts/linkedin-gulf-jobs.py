#!/usr/bin/env python3
"""
LinkedIn Gulf Jobs Scanner v4.0 - Exa API Search
====================================================
Strategy:
  - Fast search: Exa neural search via Composio MCP (no browser, no Playwright)
  - Filter by: executive title + GCC location + DT/Tech domain
  - Output: "Radar Picks" - relevant leads surfaced for review
  - ATS scoring against full JD happens at apply time (not here)
  - Runs in < 5 minutes for all searches

v4.0 Changes (2026-03-20):
  - Replaced Playwright Google scraping with Exa API via Composio MCP
  - Replaced jobspy LinkedIn/Indeed scraping with Exa neural search
  - No browser automation, no bot detection issues
  - Parallel-safe batched API calls with rate limiting
"""

import hashlib, os, re, json, time, sys
from datetime import datetime, timedelta
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

# Country short names for search queries
COUNTRY_SEARCH_TERMS = {
    "United Arab Emirates": ["Dubai", "Abu Dhabi", "UAE"],
    "Saudi Arabia": ["Riyadh", "Saudi Arabia", "KSA"],
    "Qatar": ["Doha", "Qatar"],
    "Bahrain": ["Bahrain"],
    "Kuwait": ["Kuwait"],
    "Oman": ["Muscat", "Oman"],
}

# Paths
BASE_DIR       = Path("/root/.openclaw/workspace")
OUTPUT_DIR     = BASE_DIR / "jobs-bank" / "scraped"
LOG_FILE       = OUTPUT_DIR / "cron-logs.md"
DETAILED_LOG   = OUTPUT_DIR / "detailed-search-log.md"
NOTIFIED_FILE  = OUTPUT_DIR / "notified-jobs.md"
FILTERED_LOG   = OUTPUT_DIR / "filtered-out-jobs.md"
APPLIED_DIR    = BASE_DIR / "jobs-bank" / "applications"
PIPELINE_FILE  = BASE_DIR / "jobs-bank" / "pipeline.md"
CONFIG_FILE    = Path("/root/.openclaw/openclaw.json")

MAX_RUNTIME_SECONDS  = 9 * 60   # 9 minutes - enough for 126 queries at ~3.4s each + buffer
MIN_JOBS_ALERT       = 5        # alert if fewer total jobs found
ATS_THRESHOLD        = 65       # minimum ATS score to include in picks
EXA_RESULTS_PER_QUERY = 10     # results per Exa search
EXA_DELAY_BETWEEN     = 1.5    # seconds between API calls (rate limit)

# Composio MCP config
COMPOSIO_MCP_URL = "https://connect.composio.dev/mcp"
COMPOSIO_CONSUMER_KEY = ""  # loaded from openclaw.json

# Ahmed's CV keywords for ATS scoring (from master-cv-data.md)
ATS_KEYWORDS = {
    # Core skills (weight 3)
    "digital transformation": 3, "pmo": 3, "program management": 3,
    "project management": 3, "agile": 3, "strategic planning": 3,
    "operational excellence": 3, "change management": 3, "stakeholder management": 3,
    "cross-functional": 3, "p&l": 3,
    # Domain (weight 2-3)
    "healthtech": 2, "healthcare": 2, "fintech": 3, "e-commerce": 2,
    "payments": 3, "digital banking": 3, "mobile money": 2, "neobank": 2,
    "digital financial": 3, "superapp": 3, "digital wallet": 2,
    "mobile": 2, "saas": 2, "ai": 2, "data analytics": 2,
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
              "fundraising","cfo ","budget","residences",
              "housing","construction","facility","procurement","legal","compliance",
              "risk ","audit","partnerships","education","academic",
              "medical","patient","hospital","content ","creative",
              "communications","pr ","public relations","social media"]

# Fintech/banking override: these domains are RELEVANT to Ahmed's profile
# (ex-Network International/EMP, PaySky, Yalla SuperApp)
FINTECH_OVERRIDE_WORDS = ["fintech","digital banking","payment","superapp",
                          "digital financial","network international","emp ",
                          "neobank","digital wallet","mobile money"]

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

    # 3. Must not be in hard skip list (with fintech/banking override)
    fintech_match = any(w in t for w in FINTECH_OVERRIDE_WORDS)
    for skip in SKIP_WORDS:
        if skip in t:
            # Allow fintech/banking roles - Ahmed has deep domain experience
            if fintech_match:
                continue
            # Allow only if title ALSO has strong exec+domain combo
            strong_exec = any(w in t for w in ["chief","vp ","vice president","cto","cio","cdo"])
            strong_domain = any(w in t for w in ["digital","technology","pmo","transformation"])
            if not (strong_exec and strong_domain):
                return False, "skip-word"

    return True, "ok"


def is_priority(title, location):
    """Is this a priority role? ANY 2 of 3 criteria: C-suite title + GCC location + DT sector."""
    t = title.lower()
    loc = location.lower()
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

    score = sum([is_csuite, is_dt, is_top_gcc])
    return score >= 2

# ===================== DEDUP (SQLite-based) =====================

def _init_db():
    """Initialize pipeline_db for dedup. Single source of truth."""
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from pipeline_db import is_duplicate as db_is_dup, upsert_job, url_hash
        # Return True sentinel instead of conn (pipeline_db manages its own connections)
        return True, db_is_dup, upsert_job, url_hash
    except Exception as e:
        print(f"  Warning: pipeline_db import failed ({e}), falling back to file dedup")
        return None, None, None, None

_db_conn = None
_db_is_dup = None
_db_upsert = None
_db_url_hash = None

def is_duplicate_db(url, company=""):
    """Check dedup via SQLite. Falls back to notified-file if DB unavailable."""
    global _db_conn, _db_is_dup
    if _db_conn and _db_is_dup:
        return _db_is_dup(url)
    # Fallback: file-based (legacy)
    jid = hashlib.sha256(url.encode()).hexdigest()[:12]
    if jid in _notified:
        return True
    return False

def save_to_db(job):
    """Write job to SQLite. Also append to notified-file for backward compat."""
    global _db_conn, _db_upsert
    if _db_conn and _db_upsert:
        result = _db_upsert(job)
        # pipeline_db manages its own commits
    # Legacy: also write to notified file
    with open(NOTIFIED_FILE, "a") as f:
        f.write(f"\n- {job['id']}: {job['title']} at {job['company']} ({job['location']})")

def load_notified():
    """Load legacy notified set for fallback dedup."""
    if NOTIFIED_FILE.exists():
        return set(re.findall(r"([a-f0-9]{12}|\d{8,})", NOTIFIED_FILE.read_text()))
    return set()

# ===================== COMPOSIO MCP / EXA SEARCH =====================

def load_composio_key():
    """Load Composio consumer key from openclaw.json."""
    global COMPOSIO_CONSUMER_KEY
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        key = config.get("plugins", {}).get("entries", {}).get("composio", {}).get("config", {}).get("consumerKey", "")
        if key:
            COMPOSIO_CONSUMER_KEY = key
            return True
    except Exception as e:
        print(f"  Warning: Could not load Composio key from config: {e}")

    # Fallback: env var
    key = os.environ.get("COMPOSIO_CONSUMER_KEY", "")
    if key:
        COMPOSIO_CONSUMER_KEY = key
        return True

    print("  ERROR: No Composio consumer key found!")
    return False


def mcp_call(method, params, timeout=30):
    """Make a JSON-RPC call to Composio MCP endpoint. Returns parsed result or None."""
    import requests

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "x-consumer-api-key": COMPOSIO_CONSUMER_KEY,
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

        # Parse SSE response
        for line in resp.text.split("\n"):
            if line.startswith("data:"):
                data = json.loads(line[5:].strip())
                if "error" in data:
                    print(f"    MCP error: {data['error']}")
                    return None
                return data.get("result", {})

        return None
    except requests.exceptions.Timeout:
        print(f"    MCP timeout ({timeout}s)")
        return None
    except Exception as e:
        print(f"    MCP error: {e}")
        return None


def mcp_initialize():
    """Initialize MCP session."""
    result = mcp_call("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "gulf-jobs-scanner", "version": "4.0"},
    })
    return result is not None


def exa_search(query, num_results=10, start_date=None):
    """Search via EXA_SEARCH through Composio MCP. Returns list of result dicts."""
    args = {
        "query": query,
        "type": "neural",
        "numResults": num_results,
    }
    if start_date:
        args["startPublishedDate"] = start_date

    result = mcp_call("tools/call", {
        "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
        "arguments": {
            "tools": [{
                "tool_slug": "EXA_SEARCH",
                "arguments": args,
            }],
            "sync_response_to_workbench": False,
        },
    }, timeout=45)

    if not result:
        return []

    # Parse the nested response
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


def composio_web_search(query):
    """Search via COMPOSIO_SEARCH_WEB through MCP. Returns citations list."""
    result = mcp_call("tools/call", {
        "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
        "arguments": {
            "tools": [{
                "tool_slug": "COMPOSIO_SEARCH_WEB",
                "arguments": {"query": query},
            }],
            "sync_response_to_workbench": False,
        },
    }, timeout=45)

    if not result:
        return [], ""

    try:
        content = result.get("content", [])
        if not content:
            return [], ""
        text = content[0].get("text", "")
        outer = json.loads(text)
        if not outer.get("successful"):
            return [], ""
        results_list = outer.get("data", {}).get("results", [])
        if not results_list:
            return [], ""
        inner = results_list[0].get("response", {})
        if not inner.get("successful"):
            return [], ""
        data = inner.get("data", {})
        citations = data.get("citations", [])
        answer = data.get("answer", "")
        return citations, answer
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"    Parse error: {e}")
        return [], ""


def extract_job_from_exa_result(result, search_title="", search_country=""):
    """Convert an Exa search result into a job dict matching our format."""
    url = result.get("url", "")
    raw_title = result.get("title", "")

    # Clean title: remove site names like "| LinkedIn", "| Indeed", "- GulfTalent"
    title = re.sub(r'\s*[\|–-]\s*(LinkedIn|Indeed|GulfTalent|Glassdoor|Bayt|NaukriGulf|Michael Page|Hays|Robert Half|Involved|HubMub|ZeroTaxJobs|Visa Sponsorship Jobs).*$', '', raw_title, flags=re.IGNORECASE).strip()
    # Also remove "at CompanyName" suffix patterns from aggregator titles
    title_for_company = title

    # Try to extract company from title patterns like "Role at Company" or "Role | Company"
    company = "Confidential"
    company_match = re.search(r'\s+at\s+(.+?)(?:\s*[\|–-]|$)', raw_title, re.IGNORECASE)
    if company_match:
        company = company_match.group(1).strip()
        # Remove company from title
        title = re.sub(r'\s+at\s+' + re.escape(company) + r'.*$', '', title, flags=re.IGNORECASE).strip()
    else:
        # Try domain-based company extraction
        domain_match = re.match(r'https?://(?:www\.)?([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            # Known job board domains - company is in the title
            job_boards = ["linkedin.com", "indeed.com", "glassdoor.com", "bayt.com",
                         "naukrigulf.com", "gulftalent.com", "michaelpage.ae",
                         "monster.com", "ziprecruiter.com", "seek.com", "totaljobs.com",
                         "jobleads.com", "jaabz.com", "hubmub.com", "zerotaxjobs.com"]
            if not any(jb in domain for jb in job_boards):
                # Direct company career site
                company = domain.replace("careers.", "").replace("jobs.", "").split(".")[0].title()

    # Extract location from title or URL if possible
    location = search_country
    for country, terms in COUNTRY_SEARCH_TERMS.items():
        for term in terms:
            if term.lower() in raw_title.lower() or term.lower() in url.lower():
                location = country
                break

    # Generate stable ID from URL
    jid = hashlib.sha256(url.encode()).hexdigest()[:12]

    return {
        "id": jid,
        "title": title if title else search_title,
        "company": company,
        "location": location,
        "url": url,
        "site": "exa",
        "source_via": re.match(r'https?://(?:www\.)?([^/]+)', url).group(1) if re.match(r'https?://(?:www\.)?([^/]+)', url) else "",
        "search_country": search_country,
        "search_title": search_title,
        "date_posted": result.get("publishedDate", "")[:10] if result.get("publishedDate") else "",
    }


def extract_job_from_citation(citation, search_title="", search_country=""):
    """Convert a COMPOSIO_SEARCH_WEB citation into a job dict."""
    url = citation.get("url", "") or citation.get("id", "")
    raw_title = citation.get("title", "")
    snippet = citation.get("snippet", "")

    # Same title cleaning as exa results
    title = re.sub(r'\s*[\|–-]\s*(LinkedIn|Indeed|GulfTalent|Glassdoor|Bayt|NaukriGulf|Michael Page|Hays|Robert Half|Involved|HubMub|ZeroTaxJobs|Visa Sponsorship Jobs|GulfTalent\.com|RAKBANK|Etisalat).*$', '', raw_title, flags=re.IGNORECASE).strip()

    company = "Confidential"
    company_match = re.search(r'\s+at\s+(.+?)(?:\s*[\|–-]|$)', raw_title, re.IGNORECASE)
    if company_match:
        company = company_match.group(1).strip()
        title = re.sub(r'\s+at\s+' + re.escape(company) + r'.*$', '', title, flags=re.IGNORECASE).strip()
    else:
        domain_match = re.match(r'https?://(?:www\.)?([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            job_boards = ["linkedin.com", "indeed.com", "glassdoor.com", "bayt.com",
                         "naukrigulf.com", "gulftalent.com", "michaelpage.ae",
                         "monster.com", "ziprecruiter.com", "jobleads.com", "jaabz.com",
                         "hubmub.com", "zerotaxjobs.com"]
            if not any(jb in domain for jb in job_boards):
                company = domain.replace("careers.", "").replace("jobs.", "").split(".")[0].title()

    location = search_country
    combined = (raw_title + " " + snippet).lower()
    for country, terms in COUNTRY_SEARCH_TERMS.items():
        for term in terms:
            if term.lower() in combined:
                location = country
                break

    jid = hashlib.sha256(url.encode()).hexdigest()[:12]

    return {
        "id": jid,
        "title": title if title else search_title,
        "company": company,
        "location": location,
        "url": url,
        "site": "exa-web",
        "source_via": re.match(r'https?://(?:www\.)?([^/]+)', url).group(1) if url and re.match(r'https?://(?:www\.)?([^/]+)', url) else "",
        "search_country": search_country,
        "search_title": search_title,
        "date_posted": citation.get("publishedDate", "")[:10] if citation.get("publishedDate") else "",
    }


def search_jobs_exa(title, country):
    """Search for jobs using Exa neural search. Returns list of job dicts."""
    # Build optimized search queries
    country_terms = COUNTRY_SEARCH_TERMS.get(country, [country])
    # Use first (most specific) location term
    location_term = country_terms[0]

    # Calculate date 14 days ago for recency
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    query = f"{title} {location_term} job opening hiring 2026"
    results = exa_search(query, num_results=EXA_RESULTS_PER_QUERY, start_date=start_date)

    jobs = []
    for r in results:
        job = extract_job_from_exa_result(r, search_title=title, search_country=country)
        if job["url"]:  # Skip results without URL
            jobs.append(job)

    return jobs


def search_jobs_web(title, country):
    """Search for jobs using COMPOSIO_SEARCH_WEB. Returns list of job dicts."""
    country_terms = COUNTRY_SEARCH_TERMS.get(country, [country])
    location_term = country_terms[0]

    query = f"{title} {location_term} job opening apply 2026"
    citations, answer = composio_web_search(query)

    jobs = []
    for c in citations:
        job = extract_job_from_citation(c, search_title=title, search_country=country)
        if job["url"]:
            jobs.append(job)

    return jobs


def search_jobs_linkedin(title, country):
    """Search LinkedIn Jobs via Exa with site: filter. Returns list of job dicts."""
    country_terms = COUNTRY_SEARCH_TERMS.get(country, [country])
    location_term = country_terms[0]
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    query = f"site:linkedin.com/jobs {title} {location_term}"
    results = exa_search(query, num_results=EXA_RESULTS_PER_QUERY, start_date=start_date)

    jobs = []
    for r in results:
        job = extract_job_from_exa_result(r, search_title=title, search_country=country)
        if job["url"]:
            jobs.append(job)
    return jobs


def search_jobs_google(title, country):
    """Search Google Jobs via web search. Returns list of job dicts."""
    country_terms = COUNTRY_SEARCH_TERMS.get(country, [country])
    location_term = country_terms[0]

    query = f"{title} {location_term} jobs site:google.com/search OR site:indeed.com OR site:glassdoor.com 2026"
    citations, answer = composio_web_search(query)

    jobs = []
    for c in citations:
        job = extract_job_from_citation(c, search_title=title, search_country=country)
        if job["url"]:
            jobs.append(job)
    return jobs


# ===================== ATS SCORING =====================

def score_ats(jd_text, title=""):
    """Score a job description against Ahmed's CV keywords. Returns 0-100."""
    if not jd_text and not title:
        return 0, []

    text = (jd_text + " " + title).lower()
    matched = []
    total_weight = 0

    for keyword, weight in ATS_KEYWORDS.items():
        if keyword in text:
            matched.append(keyword)
            total_weight += weight

    score = min(100, int(total_weight / 30 * 100))
    return score, matched


# ===================== SEMANTIC FIT FILTER =====================

AHMED_DOMAINS = ["digital transformation", "pmo", "program management", "project management",
    "healthcare", "healthtech", "fintech", "payments", "e-commerce", "ecommerce",
    "operational excellence", "change management", "enterprise", "consulting"]

AHMED_ROLES = ["pmo", "program", "director", "vp", "vice president", "head of", "chief",
    "transformation", "operations", "strategy", "product management", "delivery"]

SKIP_DOMAINS = {
    "cybersecurity": ["ciso", "information security officer", "security engineer", "penetration", "soc analyst"],
    "hands-on coding": ["software engineer", "developer", "full stack", "backend engineer", "frontend engineer", "code reviews", "sdlc", "hands-on technical", "production-grade ai products", "build platforms from scratch", "technical architecture and product delivery"],
    "oil & gas": ["offshore", "upstream", "downstream", "drilling", "petroleum", "subsea", "oil and gas", "oil & gas"],
    "civil engineering": ["roads", "highways", "bridges", "tunnels", "structural engineer", "geotechnical", "civil engineer"],
    "investment banking": ["equity capital markets", "ecm", "ipo execution", "block trades", "league table", "deal origination"],
    "aviation": ["aircraft", "mro", "ground support equipment", "aviation maintenance"],
    "construction/engineering": ["engineering, construction, and project management services", "engineering and construction consultancy", "construction consultancy solutions", "engineering standards"],
    "pure sales": ["quota-carrying", "business development representative", "sales representative"],
}

CORE_DOMAINS = ["digital transformation", "pmo", "program management", "project management",
    "healthcare", "healthtech", "fintech", "payments", "e-commerce", "enterprise",
    "digital banking", "digital financial", "superapp", "neobank", "mobile money",
    "payment ecosystem", "digital wallet"]

SKIP_TITLES = ["people transformation", "hr ", "human resources", "facilities",
    "asset management", "ip strategy", "intellectual property", "business development",
    "sales director", "marketing director", "design director", "creative director",
    "construction manager", "site manager", "quantity surveyor"]


def semantic_fit_filter(job):
    """Returns (verdict, fit_score, reason) based on actual career fit."""
    title = job.get("title", "").lower()
    jd = job.get("jd_text", "").lower()
    combined = title + " " + jd

    for domain, keywords in SKIP_DOMAINS.items():
        matches = [k for k in keywords if k in combined]
        if len(matches) >= 2:
            return "SKIP", max(1, min(3, job.get("ats_score", 0) // 30)), f"Domain mismatch: {domain}"
        if len(matches) == 1 and any(k in title for k in keywords):
            return "SKIP", 2, f"Title indicates {domain} specialization"

    domain_hits = sum(1 for d in AHMED_DOMAINS if d in combined)
    role_hits = sum(1 for r in AHMED_ROLES if r in combined)

    for st in SKIP_TITLES:
        if st in title:
            return "SKIP", 2, f"Wrong specialization: {st.strip()}"

    core_hits = sum(1 for d in CORE_DOMAINS if d in combined)

    # Title-only boost: if title strongly matches, promote even without JD text
    title_core = sum(1 for d in CORE_DOMAINS if d in title)
    title_role = sum(1 for r in AHMED_ROLES if r in title)

    if core_hits >= 3 and role_hits >= 1:
        return "APPLY", min(10, 6 + core_hits), "Strong career fit"
    elif core_hits >= 2 and role_hits >= 1:
        return "APPLY", min(8, 5 + core_hits), "Good career fit"
    elif core_hits >= 2:
        return "APPLY", min(7, 5 + core_hits), "Good career fit"
    elif title_core >= 1 and title_role >= 1:
        # Title alone has both domain + role match (e.g. "PMO Director", "VP Digital Transformation")
        return "APPLY", min(7, 5 + title_core), "Good career fit"
    elif core_hits == 1 and role_hits >= 1:
        return "STRETCH", min(6, 4 + core_hits), "Partial fit - review JD"
    elif domain_hits >= 1:
        return "STRETCH", 4, "Weak domain overlap"
    else:
        return "SKIP", 2, "No relevant domain experience"


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

def main():
    global _notified, _db_conn, _db_is_dup, _db_upsert, _db_url_hash

    start = time.time()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"=== LinkedIn Gulf Jobs Scanner v4.0 (Exa API) ===")
    print(f"Started: {ts}")

    # Ensure output dir exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load Composio key
    if not load_composio_key():
        print("FATAL: No Composio API key. Exiting.")
        sys.exit(1)

    # Initialize MCP session
    print("Initializing Composio MCP...")
    if not mcp_initialize():
        print("FATAL: Could not initialize MCP session. Exiting.")
        sys.exit(1)
    print("  MCP session initialized ✓")

    # Initialize SQLite dedup (primary) + file fallback
    _db_conn, _db_is_dup, _db_upsert, _db_url_hash = _init_db()
    if _db_conn:
        db_count = _db_conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        print(f"DB dedup: {db_count} jobs in SQLite (primary)")
    _notified = load_notified()
    print(f"Fallback cache: {len(_notified)} notified IDs")

    # Build search plan - deduplicated title+country combos
    # Strategy: group similar titles and use broader queries to reduce API calls
    # Priority countries get both Exa AND web search, secondary get Exa only
    SEARCH_GROUPS = [
        # Group 1: Digital Transformation (most important)
        ["VP Digital Transformation", "Director Digital Transformation",
         "Head of Digital Transformation", "Senior Director Digital Transformation",
         "Chief Digital Officer"],
        # Group 2: Technology Leadership
        ["Chief Technology Officer", "Chief Information Officer",
         "Head of Technology", "VP Technology", "Director of Technology",
         "Head of IT"],
        # Group 3: Engineering
        ["VP Engineering", "Director of Engineering"],
        # Group 4: C-Suite
        ["Chief Operating Officer", "Chief Strategy Officer", "Chief Product Officer"],
        # Group 5: PMO
        ["PMO Director", "Program Director", "Head of PMO"],
        # Group 6: Transformation
        ["Head of Transformation", "Director of Innovation", "VP Operations"],
        # Group 7: Fintech / Digital Banking
        ["VP Digital Banking", "Director Fintech", "Head of Digital Payments",
         "Head of Fintech", "Director Digital Banking"],
    ]

    # D5: Consolidated broader queries + parallel execution
    # Use Exa neural search semantics - broader queries find more with fewer calls
    BROAD_QUERIES = [
        # Group by semantic cluster, one broad query per group per country
        "VP OR Director digital transformation",
        "CTO OR CIO OR Head of Technology",
        "Chief Operating Officer OR Chief Strategy Officer",
        "PMO Director OR Program Director OR Head of PMO",
        "VP Engineering OR Director of Engineering",
        "Head of Transformation OR Director of Innovation OR VP Operations",
        "VP Digital Banking OR Director Fintech OR Head of Digital Payments",
    ]

    searches = []
    for query in BROAD_QUERIES:
        for country in GCC_COUNTRIES:
            searches.append((query, country, "exa"))
        # Priority countries get extra methods
        for country in PREFERRED_COUNTRIES:
            searches.append((query.split(" OR ")[0], country, "linkedin"))

    print(f"Search plan: {len(searches)} queries (D5: consolidated + parallel)")

    total_searches = 0
    total_found    = 0
    seen_urls      = set()
    seen_ids       = set()
    picks          = []
    leads          = []
    filtered_out   = []
    errors         = 0
    _search_lock   = __import__('threading').Lock()
    _rate_semaphore = __import__('threading').Semaphore(3)  # max 3 concurrent API calls

    with open(DETAILED_LOG, "a") as f:
        f.write(f"\n## Run: {ts} (v4.0 - Exa API, parallel)\n")

    def execute_search(args):
        """Execute a single search with rate limiting."""
        title, country, method = args
        _rate_semaphore.acquire()
        try:
            time.sleep(EXA_DELAY_BETWEEN)  # respect rate limit per call
            if method == "web":
                return search_jobs_web(title, country), title, country, method
            elif method == "linkedin":
                return search_jobs_linkedin(title, country), title, country, method
            elif method == "google":
                return search_jobs_google(title, country), title, country, method
            else:
                return search_jobs_exa(title, country), title, country, method
        except Exception as e:
            print(f"  Search error ({method} {title} {country}): {e}")
            return [], title, country, method
        finally:
            _rate_semaphore.release()

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(execute_search, s): s for s in searches}
        for future in as_completed(futures):
            if time.time() - start > MAX_RUNTIME_SECONDS:
                print(f"  Runtime limit reached ({MAX_RUNTIME_SECONDS}s). Stopping.")
                break

            jobs, title, country, method = future.result()
            total_searches += 1

            with open(DETAILED_LOG, "a") as f:
                f.write(f"- [{method}] {title} in {country}: {len(jobs)} results\n")

            if not jobs:
                errors += 1
                continue

            total_found += len(jobs)

        for job in jobs:
            # Dedup by URL
            if job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])

            if job["id"] in seen_ids:
                continue
            seen_ids.add(job["id"])

            if is_duplicate_db(job["url"], job.get("company", "")):
                filtered_out.append({**job, "filter_reason": "duplicate"})
                continue

            relevant, reason = is_relevant(job["title"], job["location"])
            if not relevant:
                filtered_out.append({**job, "filter_reason": reason})
                continue

            # D3: Scanner does discovery only. All scoring deferred to review stage.
            # Lightweight title-only ATS for the markdown report (informational, not gating)
            ats_score, matched = score_ats("", job["title"])
            job["ats_score"] = ats_score
            job["ats_keywords"] = matched
            job["jd_text"] = ""
            job["jd_fetched"] = False
            job["career_verdict"] = "pending_review"
            job["career_fit"] = 0
            job["career_reason"] = "awaiting LLM review"

            save_to_db(job)

            if is_priority(job["title"], job["location"]):
                picks.append(job)
                print(f"  PICK: {job['title']} | {job['company']} | {job['location']}")
            else:
                leads.append(job)
                print(f"  Lead: {job['title']} | {job['company']} | {job['location']}")

        if total_searches % 10 == 0:
            elapsed_so_far = int(time.time() - start)
            print(f"  Progress: {total_searches}/{len(searches)} | found {total_found} | picks {len(picks)} | leads {len(leads)} | {elapsed_so_far}s")

        time.sleep(EXA_DELAY_BETWEEN)

    # ==================== DEGRADATION CHECK ====================
    if total_found < MIN_JOBS_ALERT:
        msg = f"⚠️ Scanner degradation: {total_found} jobs from {total_searches} searches. API may be having issues."
        print(f"\n  {msg}")
        send_slack(msg)

    # ==================== SAVE REPORT ====================
    elapsed = int(time.time() - start)
    out_file = OUTPUT_DIR / f"qualified-jobs-{date_str}.md"

    with open(out_file, "w") as f:
        f.write(f"# LinkedIn Gulf Jobs Scanner v4.0 - Report\n\n")
        f.write(f"**Date:** {date_str}\n")
        f.write(f"**Engine:** Exa neural search via Composio MCP (no browser)\n")
        f.write(f"**Searches:** {total_searches}\n")
        f.write(f"**Jobs found:** {total_found}\n")
        f.write(f"**Unique/relevant:** {len(picks)+len(leads)}\n")
        f.write(f"**Priority Picks:** {len(picks)} (C-suite + UAE/Saudi + DT)\n")
        f.write(f"**Leads:** {len(leads)} (exec + GCC + domain)\n")
        f.write(f"**Filtered out:** {len(filtered_out)} (see filtered-out-jobs.md for audit)\n")
        f.write(f"**Errors:** {errors}\n")
        f.write(f"**Runtime:** {elapsed}s\n\n")

        if total_found < MIN_JOBS_ALERT:
            f.write(f"⚠️ **DEGRADATION:** Only {total_found} jobs found. API may be having issues.\n\n")

        if picks:
            apply_jobs = [j for j in picks if j.get('career_verdict') == 'APPLY']
            skip_jobs = [j for j in picks if j.get('career_verdict') == 'SKIP']
            stretch_jobs = [j for j in picks if j.get('career_verdict') == 'STRETCH']
            no_verdict = [j for j in picks if not j.get('career_verdict')]
            apply_jobs.extend(no_verdict)

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
                if job.get('date_posted'): extras.append(f"posted {job['date_posted']}")
                extra_str = f" | {', '.join(extras)}" if extras else ""
                f.write(f"- **{job['title']}** | {job['company']} | {job['location']}{extra_str} | [{job.get('source_via','')}]({job['url']})\n")

    # ==================== FILTERED-OUT AUDIT LOG ====================
    with open(FILTERED_LOG, "w") as f:
        f.write(f"# Filtered-Out Jobs Audit - {date_str}\n\n")
        f.write(f"**Total filtered:** {len(filtered_out)}\n\n")
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
        msg = f"🎯 *Gulf Scanner v4.0 - {len(picks)} Priority Picks*\n\n"
        for j in picks[:5]:
            msg += f"*{j['title']}* at {j['company']} ({j['location']})\n{j['url']}\n\n"
        if leads:
            msg += f"Plus {len(leads)} additional exec leads."
    else:
        msg = f"📊 *Gulf Scanner v4.0 - {len(leads)} Exec Leads*\n"
        msg += f"Searches: {total_searches} | Found: {total_found} | Leads: {len(leads)}\n"
        if leads:
            msg += "\n*Top Leads:*\n"
            for j in leads[:5]:
                msg += f"• {j['title']} | {j['company']} | {j['location']}\n  {j['url']}\n"
        if total_found < MIN_JOBS_ALERT:
            msg += f"\n⚠️ Low job count - possible API issue."

    send_slack(msg)

    # ==================== CRON LOG ====================
    with open(LOG_FILE, "a") as f:
        f.write(f"\n## {ts} (v4.0)\n")
        f.write(f"- Engine: Exa neural search via Composio MCP\n")
        f.write(f"- Searches: {total_searches}\n")
        f.write(f"- Found: {total_found}\n")
        f.write(f"- Priority picks: {len(picks)}\n")
        f.write(f"- Leads: {len(leads)}\n")
        f.write(f"- Errors: {errors}\n")
        f.write(f"- Runtime: {elapsed}s\n")
        if total_found < MIN_JOBS_ALERT:
            f.write(f"- ⚠️ DEGRADATION\n")

    # ==================== VALIDATION ====================
    expected_searches = len(searches)
    validation_warnings = []
    if total_searches < expected_searches * 0.5:
        validation_warnings.append(f"SEARCH COUNT LOW: ran {total_searches}, expected {expected_searches}. Runtime limit.")
    if total_found == 0 and total_searches > 5:
        validation_warnings.append(f"ZERO RESULTS: {total_searches} searches returned 0 jobs. API may be down.")
    if errors > total_searches * 0.5:
        validation_warnings.append(f"HIGH ERROR RATE: {errors}/{total_searches} searches failed.")

    if validation_warnings:
        print(f"\n⚠️ VALIDATION WARNINGS ({len(validation_warnings)}):")
        for w in validation_warnings:
            print(f"  - {w}")
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
        "sources": ["Exa", "Composio Web", "LinkedIn Jobs", "Google Jobs"],
        "engine": "Exa neural search via Composio MCP",
        "errors": errors,
        "validation_warnings": validation_warnings,
        "degraded": total_found < MIN_JOBS_ALERT,
    }

    meta_file = OUTPUT_DIR / f"scanner-meta-{date_str}.json"
    with open(meta_file, "w") as f:
        json.dump(scanner_meta, f, indent=2)
    print(f"\nScanner metadata saved: {meta_file}")

    # === Raw JSON output (structured data for downstream pipeline) ===
    raw_file = OUTPUT_DIR / f"jobs-raw-{date_str}.json"
    all_jobs = picks + leads
    with open(raw_file, "w") as f:
        json.dump({
            "meta": {
                "date": date_str,
                "engine": "exa-v4.0",
                "total_searches": total_searches,
                "total_found": total_found,
                "runtime_seconds": elapsed,
            },
            "jobs": all_jobs,
            "filtered_out": [{"title": j.get("title",""), "company": j.get("company",""), "url": j.get("url",""), "reason": j.get("filter_reason","")} for j in filtered_out],
        }, f, indent=2, default=str)
    print(f"Raw JSON saved: {raw_file} ({len(all_jobs)} jobs)")

    # === Notion Sync ===
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from notion_sync import sync_new_jobs, sync_system_event, sync_scanner_run
        all_new = picks + leads
        if all_new:
            added = sync_new_jobs(all_new)
            print(f"\nNotion: {added} jobs synced to pipeline")
        sync_system_event(
            f"Scanner v4.0: {total_found} found, {len(picks)} priority, {len(leads)} leads",
            component="Scanner",
            details=f"Searches: {total_searches}, Filtered: {len(filtered_out)}, Warnings: {len(validation_warnings)}"
        )
        try:
            sync_scanner_run(scanner_meta, date_str)
        except Exception as e:
            print(f"Scanner sync error: {e}")
    except Exception as e:
        print(f"\nNotion sync skipped: {e}")

    # Close DB connection
    if _db_conn:
        _db_conn.commit()
        _db_conn.close()
        print(f"\nSQLite: committed and closed")

    print(f"\n=== DONE ({elapsed}s) ===")
    print(f"Searches:       {total_searches}/{expected_searches}")
    print(f"Jobs found:     {total_found}")
    print(f"Filtered out:   {len(filtered_out)}")
    print(f"Priority picks: {len(picks)}")
    print(f"Exec leads:     {len(leads)}")
    print(f"Errors:         {errors}")
    print(f"Output:         {out_file}")
    print(f"Audit log:      {FILTERED_LOG}")

    # Cost logging
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("cost_logger", "/root/.openclaw/workspace/scripts/cost_logger.py")
        cl = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cl)
        cl.log_cost(
            session_name=f"Scanner ({date_str})",
            model="Exa-API",
            agent="Scanner",
            duration=elapsed,
            status="success",
            notes=f"Found: {total_found}, Picks: {len(picks)}, Sources: {total_searches}/{expected_searches}"
        )
    except Exception as e:
        print(f"Cost logging failed (non-fatal): {e}")

if __name__ == "__main__":
    main()
