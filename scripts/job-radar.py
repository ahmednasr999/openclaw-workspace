#!/usr/bin/env python3
"""
Job Radar v4: GCC Executive Job Search (Unified)
Replaces: job-radar v3 + linkedin-job-scout (killed)

Changes from v3:
- Triple dedup: applied-job-ids.txt + pipeline.md + dossiers/
- Expanded kill list (retail loyalty, beauty directors, founder associate, etc.)
- Stricter ATS proxy scoring with description-based sector penalties
- Dossier slug dedup (catches roles analyzed but not in applied-ids)
- Cleaner output: only genuinely new, properly scored roles
"""

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add jobspy venv to path
VENV_PATH = "/root/.openclaw/workspace/tools/jobspy-venv/lib/python3.13/site-packages"
if os.path.exists(VENV_PATH):
    sys.path.insert(0, VENV_PATH)

try:
    from jobspy import scrape_jobs
except ImportError:
    print("ERROR: jobspy not installed. Run: pip install python-jobspy")
    sys.exit(1)

DATE = datetime.now().strftime("%Y-%m-%d")
OUTPUT = "/root/.openclaw/workspace/memory/job-radar.md"
PIPELINE = "/root/.openclaw/workspace/jobs-bank/pipeline.md"
APPLIED_IDS_FILE = "/root/.openclaw/workspace/jobs-bank/applied-job-ids.txt"
DOSSIERS_DIR = "/root/.openclaw/workspace/jobs-bank/dossiers/"
SCANS_DIR = "/root/.openclaw/workspace/jobs-bank/scans/"

# Seniority keywords that signal executive-level roles
EXEC_KEYWORDS = [
    "vp", "vice president", "director", "head of", "chief",
    "cto", "coo", "ceo", "cio", "cdo", "cpo", "cfo",
    "svp", "evp", "managing director", "general manager",
    "transformation lead", "program director", "senior director",
]

# ============================================================
# KILL LIST v2: Expanded to eliminate all noise categories
# ============================================================
KILL_LIST = [
    # Sales & Revenue & Account Management
    "sales", "account executive", "business development", "revenue",
    "account director", "account manager", "commercial officer",
    "pre-sales", "sales director", "sales manager", "channel partner",
    "client partner", "partnership manager", "partnerships director",
    # HR & People
    "human resources", "hr manager", "recruiter", "talent acquisition",
    "employee relations", "people operations", "head of people",
    "hr director", "hr business partner", "total rewards",
    "compensation and benefits", "workforce planning",
    # Supply Chain & Operations (non-tech)
    "supply chain", "logistics", "procurement", "warehouse",
    "fleet manager", "distribution", "freight",
    # Admin & Support & Junior
    "admin", "office manager", "executive assistant", "receptionist",
    "coordinator", "founders associate",
    "personal assistant", "secretary",
    # Beauty, Fashion, Retail & FMCG (non-tech)
    "beauty", "cosmetics", "fashion", "retail operations",
    "crm and loyalty", "loyalty director", "merchandising",
    "store director", "store manager", "visual merchandiser",
    "retail director", "buying director", "category manager",
    "brand manager", "brand director", "marketing director",
    "head of marketing", "vp marketing",
    # Construction, Facilities, Real Estate & Engineering (non-tech)
    "construction", "facilities", "property", "real estate",
    "quantity survey", "leasing director", "commercial manager",
    "site manager", "site director", "building manager",
    "project director civil", "structural engineer",
    "mep", "hvac", "mechanical engineer", "electrical engineer",
    # Risk, Audit & Compliance (non-tech/non-cyber)
    "enterprise risk management", "erm director", "senior director of erm",
    "internal audit", "compliance officer", "anti-bribery",
    "crisis management", "risk appetite",
    # BPO & Document Management
    "bpo", "mailroom", "scanning", "data capture", "document management",
    # Transport, Rail & Non-tech Infrastructure
    "rail", "transport infrastructure", "railway",
    "aviation operations", "ground operations", "cabin crew",
    "flight operations", "pilot",
    # Finance & Banking (non-tech positions)
    "priority banking", "wealth management", "investment banking",
    "fund manager", "portfolio manager", "treasury", "controller",
    "financial controller", "cfo", "chief financial",
    # Legal & Policy
    "public policy", "government affairs", "legal counsel",
    "general counsel", "head of legal",
    # Non-tech other
    "teacher", "instructor", "professor", "lecturer",
    "culinary", "chef", "food and beverage director", "spa",
    "hotel director", "hotel manager", "resort",
    "medical director", "clinical director", "nursing director",
    "head nurse", "physician", "dentist", "pharmacist",
    # Content, Social, Creative (non-tech)
    "content writer", "social media manager", "creative director",
    "art director", "graphic designer", "copywriter",
    "head of content", "editorial director",
]

ATS_THRESHOLD = 65  # Proxy relevance score, not real ATS. Real ATS done by NASR after surfacing.
BORDERLINE_MIN = 55

# Ghost job detection
GHOST_INDICATORS = [
    "fast-paced", "rockstar", "ninja", "wear many hats",
    "must love dogs", "work hard play hard",
]
STALE_DAYS = 14

# ============================================================
# SEARCH CONFIGURATION: Focused on Ahmed's target roles
# ============================================================
# ============================================================
# SEARCH TERMS: Simple, focused queries (LinkedIn hates multi-keyword OR)
# Each search = one focused query. More searches > smarter searches.
# ============================================================
SEARCHES = [
    # PMO / Program Leadership
    {"label": "Director PMO (Dubai)", "search_term": "Director PMO", "location": "Dubai"},
    {"label": "Head PMO (Dubai)", "search_term": "Head PMO", "location": "Dubai"},
    {"label": "Program Director (Dubai)", "search_term": "Program Director", "location": "Dubai"},
    {"label": "Director PMO (Riyadh)", "search_term": "Director PMO", "location": "Riyadh"},
    {"label": "Head PMO (Riyadh)", "search_term": "Head PMO", "location": "Riyadh"},
    # Digital Transformation
    {"label": "Digital Transformation Director (Dubai)", "search_term": "Digital Transformation Director", "location": "Dubai"},
    {"label": "VP Digital Transformation (Dubai)", "search_term": "VP Digital Transformation", "location": "Dubai"},
    {"label": "Head Digital Transformation (Dubai)", "search_term": "Head Digital Transformation", "location": "Dubai"},
    {"label": "Digital Transformation Director (Riyadh)", "search_term": "Digital Transformation Director", "location": "Riyadh"},
    {"label": "Digital Transformation Director (Doha)", "search_term": "Digital Transformation Director", "location": "Doha"},
    # CTO / Tech Leadership
    {"label": "CTO (Dubai)", "search_term": "CTO", "location": "Dubai"},
    {"label": "CTO (Riyadh)", "search_term": "CTO", "location": "Riyadh"},
    {"label": "VP Technology (Dubai)", "search_term": "VP Technology", "location": "Dubai"},
    # IT Leadership
    {"label": "Director IT (Dubai)", "search_term": "Director IT", "location": "Dubai"},
    {"label": "Director IT (Riyadh)", "search_term": "Director IT", "location": "Riyadh"},
    {"label": "Head of IT (Dubai)", "search_term": "Head of IT", "location": "Dubai"},
    # HealthTech / AI
    {"label": "Director AI (Dubai)", "search_term": "Director AI", "location": "Dubai"},
    {"label": "Head of AI (Dubai)", "search_term": "Head of AI", "location": "Dubai"},
    {"label": "HealthTech Director (Dubai)", "search_term": "HealthTech Director", "location": "Dubai"},
    # FinTech / Payments
    {"label": "FinTech Director (Dubai)", "search_term": "FinTech Director", "location": "Dubai"},
    {"label": "Head Payments (Dubai)", "search_term": "Head of Payments", "location": "Dubai"},
    # Additional GCC
    {"label": "Director IT (Kuwait)", "search_term": "Director IT", "location": "Kuwait City"},
    {"label": "CTO (Doha)", "search_term": "CTO", "location": "Doha"},
    {"label": "Digital Transformation (Manama)", "search_term": "Digital Transformation Director", "location": "Manama"},
]


# ============================================================
# TRIPLE DEDUP: applied-ids + pipeline + dossiers
# ============================================================
def get_existing_urls():
    """Read pipeline.md and extract all existing job URLs/IDs."""
    try:
        with open(PIPELINE, "r") as f:
            content = f.read()
        urls = set(re.findall(r'linkedin\.com/jobs/view/(\d+)', content))
        return urls
    except FileNotFoundError:
        return set()


def get_applied_job_ids():
    """Read applied-job-ids.txt and extract all IDs."""
    applied = set()
    try:
        with open(APPLIED_IDS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Extract LinkedIn job IDs (plain numbers or pipe-delimited format)
                parts = line.split("|")
                for part in parts:
                    part = part.strip()
                    if part.startswith("linkedin:"):
                        applied.add(part.replace("linkedin:", ""))
                    elif part.startswith("indeed:"):
                        applied.add(part.replace("indeed:", ""))
                    elif re.match(r'^\d{8,}$', part):
                        applied.add(part)
                # Also extract IDs from URLs in the line
                li_ids = re.findall(r'linkedin\.com/jobs/view/(\d+)', line)
                applied.update(li_ids)
                indeed_ids = re.findall(r'indeed\.com/viewjob\?jk=([a-f0-9]+)', line)
                applied.update(indeed_ids)
    except FileNotFoundError:
        pass
    return applied


def get_dossier_slugs():
    """Read dossier filenames to catch previously analyzed roles."""
    slugs = set()
    try:
        for f in Path(DOSSIERS_DIR).glob("*.md"):
            if f.name != "README.md":
                slugs.add(f.stem.lower())
    except FileNotFoundError:
        pass
    return slugs


def make_slug(company, title):
    """Create a slug from company+title for dossier dedup."""
    text = f"{company}-{title}".lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


APPLICATIONS_DIR = "/root/.openclaw/workspace/jobs-bank/applications/"


def get_applied_company_tokens():
    """Build a set of (company_tokens, title_tokens) from applications/ folder names.
    Folder names follow: company-role-slug format (e.g. 'talabat-cpto', 'fab-vp-technology-data').
    Returns list of (company_word, frozenset_of_all_tokens) for fuzzy matching.
    """
    applied_pairs = []
    try:
        for d in Path(APPLICATIONS_DIR).iterdir():
            if d.is_dir():
                # Folder name is the slug: split into tokens
                tokens = set(d.name.lower().replace("-", " ").split())
                # First token is typically the company
                parts = d.name.lower().split("-")
                company_token = parts[0] if parts else ""
                if company_token and len(tokens) >= 2:
                    applied_pairs.append((company_token, tokens))
    except FileNotFoundError:
        pass
    return applied_pairs


def is_fuzzy_applied(company, title, applied_pairs):
    """Check if a job fuzzy-matches an already-applied role.
    Match criteria: same company root word AND >= 60% token overlap on role words.
    Returns True if it looks like a repost of an applied role.
    """
    if not applied_pairs:
        return False

    company_lower = company.lower().strip()
    title_lower = title.lower().strip()

    # Normalize: extract meaningful tokens
    job_tokens = set(re.sub(r'[^a-z0-9\s]', '', f"{company_lower} {title_lower}").split())
    company_words = set(re.sub(r'[^a-z0-9\s]', '', company_lower).split())

    # Remove noise words
    noise = {"the", "a", "an", "of", "and", "in", "at", "for", "to", "is", "on", "with", "by"}
    job_tokens -= noise
    company_words -= noise

    for app_company, app_tokens in applied_pairs:
        # Company must match: any company word contains/matches the applied company token
        # Allow 2-char matches only for exact equality (e.g. "dp" == "dp")
        company_match = any(
            (w == app_company) or
            (len(w) >= 3 and len(app_company) >= 3 and (app_company in w or w in app_company))
            for w in company_words
        )
        if not company_match:
            continue

        # Token overlap: how much do the ROLE tokens overlap with applied tokens?
        # Exclude company name tokens from overlap (company match already confirmed above)
        # Also count abbreviation matches (e.g. "cpto" matches initials of "chief product technology officer")
        role_app_tokens = app_tokens - {app_company}  # Remove company token from comparison
        overlap = job_tokens & role_app_tokens
        # Check for abbreviation matches: applied token is initials of consecutive job title words
        title_words = re.sub(r'[^a-z0-9\s]', '', title_lower).split()
        for app_tok in role_app_tokens:
            if app_tok in overlap:
                continue
            # Check if app_tok could be an acronym of title words
            if len(app_tok) >= 2 and all(c.isalpha() for c in app_tok):
                initials = ''.join(w[0] for w in title_words if w and w not in noise)
                if app_tok in initials:
                    overlap.add(app_tok)

        if len(role_app_tokens) > 0:
            overlap_ratio = len(overlap) / len(role_app_tokens)
            if overlap_ratio >= 0.6:
                return True

    return False


# ============================================================
# ENHANCED KILL LIST + SENIORITY FILTER
# ============================================================
def should_skip(title, description="", company=""):
    """Check if job should be skipped. Returns (skip: bool, reason: str)."""
    title_lower = title.lower()
    desc_lower = description.lower() if description else ""
    company_lower = company.lower() if company else ""
    combined = title_lower + " " + company_lower

    # Title-based kill (strict: any kill keyword in title = skip)
    for kw in KILL_LIST:
        if kw in title_lower:
            return True, f"kill:{kw}"

    # Description-based sector kill
    if desc_lower:
        sector_kills = [
            "quantity surveyor", "chartered surveyor", "mailroom",
            "scanning operations", "beauty retail", "cosmetics retail",
            "luxury beauty", "fashion retail", "risk appetite",
            "risk tolerance", "anti-bribery", "whistleblower",
            "rail operations", "railway", "transport infrastructure",
            "food and beverage", "hospitality management",
            "interior design", "architecture firm",
        ]
        for kw in sector_kills:
            if kw in desc_lower:
                return True, f"sector:{kw}"

    # Seniority floor: skip obviously junior roles
    junior_signals = [
        "intern", "junior", "coordinator",
        "analyst", "specialist", "trainee", "graduate", "entry level",
    ]
    for j in junior_signals:
        if title_lower.startswith(j) or f" {j} " in f" {title_lower} ":
            # Exceptions for senior titles containing these words
            exceptions = [
                "associate director", "chief", "senior", "head",
                "director", "lead", "principal", "manager",
            ]
            if not any(exc in title_lower for exc in exceptions):
                return True, f"junior:{j}"

    # UAE/Saudi National only indicators
    national_only = ["uae national", "emirati only", "saudi national", "gcc national"]
    for kw in national_only:
        if kw in combined or kw in desc_lower:
            return True, f"national:{kw}"

    return False, ""


# ============================================================
# IMPROVED ATS PROXY SCORING
# ============================================================
def proxy_ats_score(title, description=""):
    """
    Proxy ATS scoring based on keyword matching with Ahmed's profile.
    Stricter: requires BOTH seniority AND sector alignment.
    No description = capped at 70.
    Returns: (score, factors)
    """
    title_lower = title.lower()
    desc_lower = description.lower() if description else ""
    combined = title_lower + " " + desc_lower
    has_description = bool(desc_lower.strip())

    score = 45
    factors = []

    # === SENIORITY (max 15 pts) ===
    exec_strong = [
        "vice president", "svp", "evp", "chief",
        "cto", "cio", "cdo", "cpo",
    ]
    # Check exec_strong with word-boundary awareness for short keywords
    is_exec = False
    for kw in exec_strong:
        if len(kw) <= 3:  # Short keywords: check word boundaries
            if re.search(r'\b' + re.escape(kw) + r'\b', title_lower):
                is_exec = True
                break
        else:
            if kw in title_lower:
                is_exec = True
                break
    # Also check "vp" with word boundary (avoid matching "svp" substring issues)
    if not is_exec and re.search(r'\bvp\b', title_lower):
        is_exec = True

    if is_exec:
        score += 15
        factors.append("executive")
    elif "director" in title_lower or "head of" in title_lower or "head," in title_lower:
        score += 15  # Directors/Heads are Ahmed's target level, same weight as exec
        factors.append("director")
    elif "general manager" in title_lower:
        score += 12
        factors.append("gm")
    elif "senior manager" in title_lower:
        score += 8
        factors.append("sr-manager")
    else:
        score -= 5
        factors.append("non-exec-title")

    # === SECTOR FIT (max 20 pts) - CRITICAL ===
    sector_strong = [
        "digital transformation", "healthtech", "health tech",
        "digital health", "fintech", "fin tech", "payments",
        "e-commerce", "ecommerce", "hospital", "clinical",
        "healthcare it", "healthcare technology",
    ]
    sector_medium = [
        "digital", "technology", "it operations", "it infrastructure",
        "information technology", "software", "ai ", "artificial intelligence",
        "pmo", "project management", "program management", "programme",
        "cloud", "cybersecurity", "data analytics", "machine learning",
        "enterprise", "platform", "saas",
    ]

    sector_strong_count = sum(1 for kw in sector_strong if kw in combined)
    sector_medium_count = sum(1 for kw in sector_medium if kw in combined)

    if sector_strong_count > 0:
        score += min(12 + sector_strong_count * 5, 25)
        factors.append(f"sector-strong({sector_strong_count})")
    elif sector_medium_count > 0:
        score += min(8 + sector_medium_count * 4, 20)
        factors.append(f"sector-medium({sector_medium_count})")
    else:
        score -= 8
        factors.append("no-sector-fit")

    # === AHMED-SPECIFIC KEYWORDS (max 10 pts) ===
    ahmed_keywords = [
        "transformation", "agile", "scrum", "enterprise", "governance",
        "stakeholder", "vendor management", "change management",
        "vision 2030", "erp", "crm implementation", "salesforce",
        "portfolio management", "kpi", "operational excellence",
        "cross-functional", "multi-country", "regional",
    ]
    ahmed_count = sum(1 for kw in ahmed_keywords if kw in combined)
    score += min(ahmed_count * 3, 15)
    if ahmed_count > 0:
        factors.append(f"profile-match({ahmed_count})")

    # === GCC LOCATION BONUS (max 5 pts) ===
    gcc_keywords = ["dubai", "abu dhabi", "riyadh", "jeddah", "doha", "manama", "kuwait", "muscat", "uae", "saudi"]
    if any(kw in combined for kw in gcc_keywords):
        score += 5
        factors.append("gcc-location")

    # === NEGATIVE INDICATORS ===
    if any(kw in combined for kw in [
        "hands-on coding", "docker", "kubernetes", "terraform",
        "full-stack developer", "senior engineer", "staff engineer",
        "ph.d. required", "phd required", "cs degree required",
    ]):
        score -= 15
        factors.append("too-technical")

    if any(kw in combined for kw in ["web3", "crypto", "blockchain", "defi"]):
        score -= 15
        factors.append("crypto")

    # Contract role penalty
    if any(kw in combined for kw in ["contract", "fixed term", "fixed-term", "temporary"]):
        score -= 5
        factors.append("contract")

    # === NO DESCRIPTION PENALTY ===
    if not has_description:
        score = min(score, 70)
        factors.append("no-jd-cap")

    score = max(0, min(100, score))
    return score, factors


# ============================================================
# GHOST JOB DETECTION
# ============================================================
def is_ghost_job(row):
    """Check if job is likely a ghost job or stale posting."""
    title = str(row.get("title", "")).lower()
    description = str(row.get("description", "")).lower() if "description" in row else ""
    date_posted = str(row.get("date_posted", ""))

    try:
        if date_posted and date_posted != "nan" and date_posted != "":
            if "day" in date_posted.lower():
                match = re.search(r'(\d+)', date_posted)
                if match and int(match.group(1)) > STALE_DAYS:
                    return "stale"
            elif "hour" in date_posted.lower() or "yesterday" in date_posted.lower():
                pass
            else:
                try:
                    parsed = datetime.strptime(date_posted[:10], "%Y-%m-%d")
                    if (datetime.now() - parsed) > timedelta(days=STALE_DAYS):
                        return "stale"
                except:
                    pass
    except:
        pass

    ghost_score = sum(1 for ind in GHOST_INDICATORS if ind in title or ind in description)
    if ghost_score >= 2:
        return "vague"

    return None


def extract_job_id(url):
    """Extract LinkedIn job ID from URL."""
    match = re.search(r'linkedin\.com/jobs/view/(\d+)', str(url))
    return match.group(1) if match else None


def extract_indeed_id(url):
    """Extract Indeed job key from URL."""
    match = re.search(r'indeed\.com/viewjob\?jk=([a-f0-9]+)', str(url))
    return match.group(1) if match else None


# ============================================================
# SEARCH EXECUTION
# ============================================================
def run_search(search_config):
    """Run a single search and return results. LinkedIn only (Indeed/Google broken)."""
    try:
        kwargs = {
            "site_name": ["linkedin"],
            "search_term": search_config["search_term"],
            "location": search_config.get("location", "Dubai"),
            "results_wanted": 20,
            "hours_old": 168,  # 7 days
            "verbose": 0,
        }
        jobs = scrape_jobs(**kwargs)
        count = len(jobs) if jobs is not None else 0
        print(f"    -> {count} results from LinkedIn")
        return jobs
    except Exception as e:
        print(f"    -> ERROR: {e}")
        return f"ERROR: {e}"


# ============================================================
# RESULT FORMATTING WITH FULL DEDUP
# ============================================================
def format_jobs(df, label, all_known_ids, dossier_slugs, applied_pairs=None):
    """Format job results with ATS proxy scoring and quad dedup."""
    lines = [f"### {label}\n"]
    if isinstance(df, str):
        lines.append(f"  {df}\n")
        return "\n".join(lines), [], []
    if df is None or len(df) == 0:
        lines.append("No results found.\n")
        return "\n".join(lines), [], []

    qualified = []
    borderline = []
    stats = {"skipped_kill": 0, "skipped_dedup": 0, "skipped_ats": 0, "ghost": 0, "skipped_fuzzy": 0}

    for _, row in df.iterrows():
        title = str(row.get("title", "N/A"))
        company = str(row.get("company", "N/A"))
        location_val = str(row.get("location", "N/A"))
        url = str(row.get("job_url", ""))
        date_posted = str(row.get("date_posted", ""))
        description = str(row.get("description", "")) if "description" in row else ""

        # Salary info
        salary_min = row.get("min_amount", "")
        salary_max = row.get("max_amount", "")
        salary_str = ""
        if salary_min and salary_max:
            salary_str = f" | Salary: {salary_min}-{salary_max}"
        elif salary_min:
            salary_str = f" | Salary: {salary_min}+"

        # === DEDUP CHECK (triple) ===
        job_id = extract_job_id(url)
        indeed_id = extract_indeed_id(url)
        is_already_known = (
            (job_id and job_id in all_known_ids) or
            (indeed_id and indeed_id in all_known_ids)
        )

        # Dossier slug dedup
        slug = make_slug(company, title)
        is_in_dossiers = slug in dossier_slugs

        if is_already_known or is_in_dossiers:
            stats["skipped_dedup"] += 1
            continue  # Skip silently, don't even show

        # === FUZZY APPLIED CHECK (catches reposts with new IDs) ===
        if applied_pairs and is_fuzzy_applied(company, title, applied_pairs):
            stats["skipped_fuzzy"] += 1
            continue  # Skip: fuzzy match to already-applied role

        # === GHOST CHECK ===
        ghost_status = is_ghost_job(row)
        if ghost_status:
            stats["ghost"] += 1
            continue  # Skip silently

        # === KILL LIST CHECK ===
        skip, reason = should_skip(title, description, company)
        if skip:
            stats["skipped_kill"] += 1
            continue  # Skip silently

        # === ATS PROXY SCORING ===
        ats_score, factors = proxy_ats_score(title, description)

        if ats_score >= ATS_THRESHOLD:
            qualified.append({
                "title": title,
                "company": company,
                "location": location_val,
                "url": url,
                "date_posted": date_posted,
                "ats_score": ats_score,
                "factors": factors,
                "salary": salary_str,
            })
        elif ats_score >= BORDERLINE_MIN:
            borderline.append({
                "title": title,
                "company": company,
                "location": location_val,
                "url": url,
                "ats_score": ats_score,
                "factors": factors,
            })
        else:
            stats["skipped_ats"] += 1

    # Only show qualified and borderline in output
    for job in qualified:
        lines.append(f"- :dart: **{job['title']}** at {job['company']} (ATS:{job['ats_score']})")
        lines.append(f"  Location: {job['location']} | Posted: {job['date_posted']}{job['salary']}")
        if job['url'] and job['url'] != "nan":
            lines.append(f"  Link: {job['url']}")
        lines.append("")

    for job in borderline:
        lines.append(f"- :warning: **{job['title']}** at {job['company']} (ATS:{job['ats_score']}, borderline)")
        lines.append(f"  Location: {job['location']}")
        if job['url'] and job['url'] != "nan":
            lines.append(f"  Link: {job['url']}")
        lines.append("")

    total_filtered = stats["skipped_kill"] + stats["skipped_dedup"] + stats["skipped_ats"] + stats["ghost"] + stats["skipped_fuzzy"]
    lines.append(f"*{len(qualified)} qualified, {len(borderline)} borderline, {total_filtered} filtered (dedup:{stats['skipped_dedup']}, fuzzy:{stats['skipped_fuzzy']}, kill:{stats['skipped_kill']}, ats:{stats['skipped_ats']}, ghost:{stats['ghost']})*\n")

    return "\n".join(lines), qualified, borderline


# ============================================================
# PIPELINE UPDATE
# ============================================================
def add_to_pipeline(new_jobs, existing_ids):
    """Append new qualified jobs to pipeline.md as Discovered."""
    if not new_jobs:
        return 0

    added = 0
    lines_to_add = []

    try:
        with open(PIPELINE, "r") as f:
            content = f.read()
        row_nums = re.findall(r'\|\s*(\d+)\s*\|', content)
        next_num = max(int(n) for n in row_nums) + 1 if row_nums else 1
    except Exception:
        next_num = 1
        content = ""

    for job in new_jobs:
        job_id = extract_job_id(job["url"])
        if job_id and job_id in existing_ids:
            continue

        loc = job["location"].split(",")[0].strip() if job["location"] else "GCC"
        line = f"| {next_num} | New | {job['company']} | {job['title']} | {loc} | -- | Discovered | Radar | {DATE} | -- | [Link]({job['url']}) | ATS:{job['ats_score']} |"
        lines_to_add.append(line)
        next_num += 1
        added += 1

    if lines_to_add:
        insert_text = "\n".join(lines_to_add) + "\n"
        table_rows = list(re.finditer(r'\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|.*\|', content))
        if table_rows:
            last_row_end = table_rows[-1].end()
            content = content[:last_row_end] + "\n" + insert_text + content[last_row_end:]
        else:
            content += "\n" + insert_text

        with open(PIPELINE, "w") as f:
            f.write(content)

    return added


# ============================================================
# CSV ARCHIVE
# ============================================================
def save_scan_csv(all_jobs_data):
    """Save raw scan data to CSV for audit trail."""
    os.makedirs(SCANS_DIR, exist_ok=True)
    csv_path = os.path.join(SCANS_DIR, f"scan-{DATE}.csv")
    try:
        import csv
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["title", "company", "location", "url", "ats_score", "date_posted"])
            for job in all_jobs_data:
                writer.writerow([
                    job.get("title", ""),
                    job.get("company", ""),
                    job.get("location", ""),
                    job.get("url", ""),
                    job.get("ats_score", ""),
                    job.get("date_posted", ""),
                ])
        print(f"  Scan archived to {csv_path}")
    except Exception as e:
        print(f"  Warning: Could not save CSV: {e}")


# ============================================================
# MAIN
# ============================================================
def main():
    print(f"Job Radar v4 running: {DATE}")
    print(f"   ATS Threshold: {ATS_THRESHOLD}+ | Borderline: {BORDERLINE_MIN}-{ATS_THRESHOLD-1}")

    # Quad dedup sources
    existing_ids = get_existing_urls()
    applied_ids = get_applied_job_ids()
    dossier_slugs = get_dossier_slugs()
    applied_pairs = get_applied_company_tokens()
    all_known_ids = existing_ids | applied_ids

    print(f"   Pipeline IDs: {len(existing_ids)}")
    print(f"   Applied IDs: {len(applied_ids)}")
    print(f"   Dossier slugs: {len(dossier_slugs)}")
    print(f"   Fuzzy applied pairs: {len(applied_pairs)}")
    print(f"   Total dedup pool: {len(all_known_ids)} IDs + {len(dossier_slugs)} slugs + {len(applied_pairs)} fuzzy")

    report = []
    report.append(f"# Job Radar v4: {DATE}\n")
    report.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*")
    report.append(f"*Engine: JobSpy (LinkedIn, Indeed, Google Jobs)*")
    report.append(f"*Dedup: {len(all_known_ids)} known IDs + {len(dossier_slugs)} dossier slugs + {len(applied_pairs)} fuzzy pairs*")
    report.append(f"*Filter: ATS {ATS_THRESHOLD}+ required | Borderline {BORDERLINE_MIN}-{ATS_THRESHOLD-1} in buffer*\n")
    report.append("---\n")

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

        formatted, qualified, borderline = format_jobs(df, search["label"], all_known_ids, dossier_slugs, applied_pairs)
        report.append(formatted)
        all_qualified.extend(qualified)
        all_borderline.extend(borderline)
        print(f"    -> After filtering: {len(qualified)} qualified, {len(borderline)} borderline")

    # Deduplicate qualified across searches
    seen_qualified = set()
    unique_qualified = []
    for job in all_qualified:
        job_id = extract_job_id(job["url"])
        key = job_id or f"{job['company']}-{job['title']}"
        if key not in seen_qualified:
            seen_qualified.add(key)
            unique_qualified.append(job)

    # Deduplicate borderline
    seen_borderline = set()
    unique_borderline = []
    for job in all_borderline:
        job_id = extract_job_id(job["url"])
        key = job_id or f"{job['company']}-{job['title']}"
        if key not in seen_borderline and key not in seen_qualified:
            seen_borderline.add(key)
            unique_borderline.append(job)

    # Sort by ATS score descending
    unique_qualified.sort(key=lambda x: x["ats_score"], reverse=True)
    unique_borderline.sort(key=lambda x: x["ats_score"], reverse=True)

    # Add to pipeline
    added = add_to_pipeline(unique_qualified, all_known_ids)

    # Save CSV archive
    save_scan_csv(unique_qualified + unique_borderline)

    # Summary
    report.append("---\n")
    report.append("## Summary\n")
    report.append(f"- Total raw jobs scanned: {len(seen_urls)}")
    report.append(f"- **Qualified (ATS {ATS_THRESHOLD}+): {len(unique_qualified)}**")
    report.append(f"- Borderline (ATS {BORDERLINE_MIN}-{ATS_THRESHOLD-1}): {len(unique_borderline)}")
    report.append(f"- **New jobs added to pipeline: {added}**\n")

    if unique_qualified:
        report.append("## Top Matches\n")
        for i, job in enumerate(unique_qualified[:10], 1):
            report.append(f"{i}. **{job['title']}** at {job['company']} (ATS:{job['ats_score']})")
            report.append(f"   Location: {job['location']} | Posted: {job.get('date_posted', 'N/A')}")
            if job['url']:
                report.append(f"   Link: {job['url']}")
            report.append("")

    # Write output
    with open(OUTPUT, "w") as f:
        f.write("\n".join(report))

    print(f"\nResults written to {OUTPUT}")
    print(f"   Total raw scanned: {len(seen_urls)}")
    print(f"   Qualified (ATS {ATS_THRESHOLD}+): {len(unique_qualified)}")
    print(f"   Borderline: {len(unique_borderline)}")
    print(f"   New added to pipeline: {added}")

    return unique_qualified, unique_borderline


if __name__ == "__main__":
    main()
