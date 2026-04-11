#!/usr/bin/env python3
"""
jobs-source-common.py — Shared configuration and utilities for all job source adapters.

Provides:
  - ALL_TITLES: 22 executive job titles to search
  - GCC_COUNTRIES: 6 GCC countries
  - PRIORITY_COUNTRIES: Top 3 high-priority countries
  - SKIP_WORDS, EXEC_WORDS, DOMAIN_WORDS: Filter word lists
  - ATS_KEYWORDS: Keyword scoring dictionary
  - is_relevant(): Seniority + domain filter
  - basic_keyword_score(): ATS-style keyword scoring
  - standard_job_dict(): Build standardized job record
"""

import json
import re
from pathlib import Path

# ===================== CONFIGURATION =====================

# All executive titles to search (22 titles)
ALL_TITLES = [
    # Digital Transformation (5)
    "VP Digital Transformation",
    "Director Digital Transformation",
    "Head of Digital Transformation",
    "Senior Director Digital Transformation",
    "Chief Digital Officer",
    # Technology Leadership (8)
    "Chief Technology Officer",
    "Chief Information Officer",
    "Head of Technology",
    "VP Technology",
    "Director of Technology",
    "Head of IT",
    "VP Engineering",
    "Director of Engineering",
    # Executive / C-Suite (3)
    "Chief Operating Officer",
    "Chief Strategy Officer",
    "Chief Product Officer",
    # PMO / Program (3)
    "PMO Director",
    "Program Director",
    "Head of PMO",
    # Transformation / Innovation (3)
    "Head of Transformation",
    "Director of Innovation",
    "VP Operations",
    # Added 2026-03-22 — gap titles
    "Transformation Lead",
    "Digital Director",
    "IT Director",
    "VP of Programs",
    "Head of Strategy",
    # Added 2026-04-05 — critical missing roles (SAYYAD data + LinkedIn gaps)
    "Delivery Director",
    "Programme Manager",
    "Project Director",
    "Head of Delivery",
    "Portfolio Director",
    "EPMO Director",

]

# GCC Countries (6)
GCC_COUNTRIES = [
    "United Arab Emirates",
    "Saudi Arabia",
    "Qatar",
    "Bahrain",
    "Kuwait",
    "Oman",
]

# Priority countries (high priority - first 3)
PRIORITY_COUNTRIES = GCC_COUNTRIES[:3]  # UAE, Saudi, Qatar

# Secondary countries (medium priority)
SECONDARY_COUNTRIES = GCC_COUNTRIES[3:]  # Bahrain, Kuwait, Oman

# Country search terms for building queries
COUNTRY_SEARCH_TERMS = {
    "United Arab Emirates": ["Dubai", "Abu Dhabi", "UAE"],
    "Saudi Arabia": ["Riyadh", "Saudi Arabia", "KSA"],
    "Qatar": ["Doha", "Qatar"],
    "Bahrain": ["Bahrain"],
    "Kuwait": ["Kuwait"],
    "Oman": ["Muscat", "Oman"],
}

# ===================== WATCHLIST =====================

WATCHLIST_FILE = Path('/root/.openclaw/workspace/data/sayyad-company-watchlist.json')

DEFAULT_COMPANY_WATCHLISTS = {
    "healthcare_gcc": [
        "Saudi German Hospital Group", "Cleveland Clinic Abu Dhabi", "Mediclinic Middle East",
        "NMC Healthcare", "Aster DM Healthcare", "King Faisal Specialist Hospital",
        "SEHA", "Abu Dhabi Health Services", "Hamad Medical Corporation",
        "Al Habib Medical Group", "Fakeeh Care"
    ],
    "fintech_gcc": [
        "Careem", "Tabby", "Tamara", "Lean Technologies", "Checkout.com",
        "Network International", "Talabat", "RAKBANK", "Qatar National Bank", "Mashreq Bank"
    ],
    "government_semi_gov_gcc": [
        "ADDA", "Abu Dhabi Digital Authority", "SDAIA", "Saudi Data & AI Authority",
        "Dubai Digital Authority", "Emirates Investment Authority", "NEOM", "Qiddiya",
        "PIF Portfolio Companies", "DEWA", "RTA Dubai", "Smart Dubai"
    ],
}

DEFAULT_DOMAIN_WATCHLISTS = {
    "healthcare_gcc": ["healthcare", "hospital", "medical", "clinic", "health"],
    "fintech_gcc": ["fintech", "bank", "banking", "payments", "wallet", "digital banking"],
    "government_semi_gov_gcc": ["government", "public sector", "authority", "smart city", "digital authority", "pif"]
}


def load_watchlists() -> dict:
    default = {
        "company_watchlists": DEFAULT_COMPANY_WATCHLISTS,
        "domain_watchlists": DEFAULT_DOMAIN_WATCHLISTS,
        "priority_companies": sorted({c for vals in DEFAULT_COMPANY_WATCHLISTS.values() for c in vals}),
        "priority_domains": sorted({d for vals in DEFAULT_DOMAIN_WATCHLISTS.values() for d in vals}),
    }
    try:
        if not WATCHLIST_FILE.exists():
            return default
        data = json.loads(WATCHLIST_FILE.read_text())
        company_watchlists = data.get("company_watchlists") or DEFAULT_COMPANY_WATCHLISTS
        domain_watchlists = data.get("domain_watchlists") or DEFAULT_DOMAIN_WATCHLISTS
        priority_companies = data.get("priority_companies") or sorted({c for vals in company_watchlists.values() for c in vals})
        priority_domains = data.get("priority_domains") or sorted({d for vals in domain_watchlists.values() for d in vals})
        return {
            "company_watchlists": company_watchlists,
            "domain_watchlists": domain_watchlists,
            "priority_companies": priority_companies,
            "priority_domains": priority_domains,
        }
    except Exception:
        return default


def get_watchlist_matches(company: str = "", text: str = "") -> dict:
    wl = load_watchlists()
    company_lower = (company or "").lower()
    text_lower = (text or "").lower()
    company_hits = []
    domain_hits = []
    categories = set()

    for category, companies in wl["company_watchlists"].items():
        for c in companies:
            if c.lower() in company_lower:
                company_hits.append(c)
                categories.add(category)
    for category, domains in wl["domain_watchlists"].items():
        for d in domains:
            if d.lower() in text_lower or d.lower() in company_lower:
                domain_hits.append(d)
                categories.add(category)
    return {
        "company_hits": sorted(set(company_hits)),
        "domain_hits": sorted(set(domain_hits)),
        "categories": sorted(categories),
    }

# ===================== FILTER WORDS =====================

# Executive keywords - must have at least one
EXEC_WORDS = [
    "chief", "ceo", "cto", "cio", "cdo", "coo", "cso", "cfo", "cmo", "cro",
    "vp ", "vp,", "vp-", "vp/", "avp", "vice president",
    "director", "head", "svp", "senior director", "managing director",
    "executive director", "program director", "principal",
    "senior manager",
]

# Domain keywords - must relate to DT/Tech/PMO
DOMAIN_WORDS = [
    "digital", "technology", "it ", "information", "pmo", "program", "project",
    "transformation", "innovation", "ai", "data", "strategy", "cyber",
    "cloud", "operations", "infrastructure", "engineering", "tech",
    "ict ", "software", "systems"
]

# Strategic role families - strong title alignment for Ahmed's target roles
STRATEGIC_ROLE_WORDS = [
    "digital transformation", "transformation", "pmo", "program", "programme",
    "portfolio", "delivery", "business excellence", "operational excellence",
    "technology", "head of it", "it director", "head of technology",
    "vp technology", "director of technology", "cio", "cto", "operations"
]

# Hard skip words - clearly irrelevant roles
SKIP_WORDS = [
    "sales", "marketing", "hr ", "human resources", "recruit", "account executive",
    "accountant", "beauty", "fashion", "restaurant", "hospitality", "nurse",
    "doctor", "physician", "clinical", "dental", "chef", "food", "beverage",
    "real estate", "broker", "supply chain", "logistics", "secretary",
    "coordinator", "specialist", "intern", "trainee", "assistant", "admin",
    "recruiter", "talent acquisition", "web3", "crypto", "blockchain",
    "fundraising", "cfo ", "budget", "residences",
    "housing", "construction", "facility", "procurement", "legal",
    "risk ", "audit", "education", "academic",
    "medical", "patient", "hospital",
    "pr ", "public relations", "social media",
    "teacher", "headteacher", "mathematics", "nursery",
    # Added 2026-04-05 — GTM, staffing, agriculture, pure sales/recruitment
    "go to market", "gtm ", "staffing", "staff augmentation",
    "agricultur", "farming", "recruiting agency",
    "headhunter", "search firm", "recruitment consultant",
    "business developer", "business development executive",
    "sales engineer", "sales manager", "sales director",
    "account manager", "account director",
    "revenue operations", "revenue manager",
    "oil and gas", "petroleum", "drilling",  # Not a target sector
    "retail", "store manager", "merchandising",
    "call center", "customer service", "data entry",
    # Tightened 2026-04-08 - off-target senior roles creating false REVIEWs
    "chief of staff", "market expansion", "demand planning", "s&op",
    "risk management", "risk advisory", "forensics", "cyber security",
    "digital trust", "equity-only", "co-founder", "paid media",
    "alliances", "product management",
]

# Fintech/banking override - these are RELEVANT domains
FINTECH_OVERRIDE_WORDS = [
    "fintech", "digital banking", "payment", "superapp",
    "digital financial", "network international", "emp ",
    "neobank", "digital wallet", "mobile money"
]

# ===================== INDUSTRY TARGETING =====================

# Target industries — positive boost for ATS scoring
# Added 2026-04-05 — Ahmed's preferred sectors
TARGET_INDUSTRY_WORDS = [
    # Healthcare/HealthTech
    "healthcare", "healthtech", "hospital network", "health system",
    "patient care", "clinical technology", "medical device",
    # Fintech/Banking
    "fintech", "digital banking", "neobank", "payment", "payment gateway",
    "digital wallet", "mobile money", "open banking",
    # Tech/Software
    "saas", "platform", "software", "cloud native", "microservices",
    "ai", "machine learning", "data analytics", "cybersecurity",
    # Government/Public Sector
    "smart city", "digital government", "government technology",
    "public sector", "sovereign wealth fund",
    # Consulting/Professional Services
    "management consulting", "advisory", "professional services",
    "big four", "strategy consulting",
]

# Excluded industries — hard deny even with exec keywords
# Added 2026-04-05
EXCLUDED_INDUSTRY_WORDS = [
    "oil and gas", "petroleum", "drilling",  # Energy sector (not target)
    "construction", "contracting", "building materials",  # Construction
    "staffing", "recruitment agency", "headhunting",  # Staffing firms
    "agriculture", "farming", "livestock",  # Agriculture
    "retail", "store manager", "merchandising",  # Pure retail
    "real estate development", "property developer",  # Real estate dev
]

# ===================== ATS KEYWORDS =====================

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

# ===================== FILTER FUNCTIONS =====================

def is_relevant(title: str, location: str = "") -> tuple[bool, str]:
    """
    Tight relevance filter: executive + strategic role/domain + no off-target title.
    Geography is a boost signal, not a substitute for role fit.
    Returns: (is_relevant, reason)
    """
    t = title.lower()

    # 1. Must have executive keyword
    if not any(w in t for w in EXEC_WORDS):
        return False, "not-exec"

    # 2. Hard skip off-target senior roles (with narrow fintech override only)
    fintech_match = any(w in t for w in FINTECH_OVERRIDE_WORDS)
    for skip in SKIP_WORDS:
        if skip in t:
            strong_exec = any(w in t for w in ["chief", "vp ", "vice president", "cto", "cio", "cdo"])
            strong_transform = any(w in t for w in ["digital transformation", "pmo", "program", "portfolio", "delivery", "head of it", "it director"])
            if fintech_match and strong_exec and strong_transform:
                continue
            return False, f"skip-word:{skip}"

    # 3. Must have real domain/role-family alignment. GCC location alone is not enough.
    domain_match = any(w in t for w in DOMAIN_WORDS)
    strategic_role_match = any(w in t for w in STRATEGIC_ROLE_WORDS)
    if not domain_match and not strategic_role_match:
        return False, "no-role-family"

    return True, "ok"


def basic_keyword_score(text: str) -> tuple[int, list[str]]:
    """
    Score text against ATS_KEYWORDS.
    Returns: (score 0-100, list of matched keywords)
    """
    if not text:
        return 0, []

    text_lower = text.lower()
    matched = []
    total_weight = 0

    for keyword, weight in ATS_KEYWORDS.items():
        if keyword in text_lower:
            matched.append(keyword)
            total_weight += weight

    # Scale to 0-100 (30 weight points = 100%)
    score = min(100, int(total_weight / 30 * 100))
    return score, matched


def has_exec_seniority(title: str) -> bool:
    """Check if title indicates executive seniority."""
    t = title.lower()
    return any(w in t for w in EXEC_WORDS)


def has_domain_match(title: str) -> bool:
    """Check if title matches relevant domain."""
    t = title.lower()
    return any(w in t for w in DOMAIN_WORDS)


def get_seniority_level(title: str) -> str:
    """Categorize seniority level from title."""
    t = title.lower()
    if any(w in t for w in ["chief", "ceo", "cto", "cio", "cdo", "coo", "cso"]):
        return "C-Suite"
    elif any(w in t for w in ["vp ", "vice president", "svp"]):
        return "VP"
    elif any(w in t for w in ["senior director", "managing director", "executive director"]):
        return "Senior Director"
    elif "director" in t or "head of" in t:
        return "Director"
    elif "principal" in t:
        return "Principal"
    else:
        return "Other"


# ===================== STANDARD JOB DICT =====================

def standard_job_dict(
    job_id: str,
    source: str,
    title: str,
    company: str,
    location: str,
    url: str,
    posted: str = "",
    raw_snippet: str = ""
) -> dict:
    """
    Build a standardized job dictionary matching the source adapter output schema.
    Also calculates keyword score and relevance.
    """
    # Calculate keyword score
    combined_text = f"{title} {raw_snippet}"
    keyword_score, match_keywords = basic_keyword_score(combined_text)

    # Check relevance
    relevant, relevance_reason = is_relevant(title, location)

    # Get seniority
    seniority = get_seniority_level(title)

    # Domain match
    domain_match = has_domain_match(title)

    return {
        "id": f"{source}-{job_id}",
        "source": source,
        "title": title,
        "company": company,
        "location": location,
        "url": url,
        "posted": posted,
        "seniority": seniority,
        "domain_match": domain_match,
        "keyword_score": keyword_score,
        "match_keywords": match_keywords[:10],  # Limit to top 10
        "raw_snippet": raw_snippet[:500] if raw_snippet else "",
        "relevant": relevant,
        "filter_reason": relevance_reason if not relevant else None,
    }


# ===================== OUTPUT SCHEMA BUILDER =====================

def build_source_output(
    agent_name: str,
    source: str,
    jobs: list[dict],
    searches_run: int,
    jobs_found_raw: int,
    jobs_after_filter: int,
    duration_ms: int,
    status: str = "success",
    error: str = None,
    retries_used: int = 0
) -> dict:
    """
    Build the standard source adapter output JSON structure.
    """
    from datetime import datetime, timezone, timedelta
    CAIRO_TZ = timezone(timedelta(hours=2))
    
    return {
        "meta": {
            "agent": agent_name,
            "source": source,
            "generated_at": datetime.now(CAIRO_TZ).isoformat(),
            "ttl_hours": 6,
            "status": status,
            "searches_run": searches_run,
            "jobs_found_raw": jobs_found_raw,
            "jobs_after_filter": jobs_after_filter,
            "duration_ms": duration_ms,
            "retries_used": retries_used,
            "error": error,
        },
        "jobs": jobs,
        "kpi": {
            "searches_run": searches_run,
            "results_per_search": round(jobs_found_raw / max(1, searches_run), 2),
            "unique_jobs": len(jobs),
        }
    }


if __name__ == "__main__":
    # Test the module
    print("=== jobs-source-common.py Test ===")
    print(f"ALL_TITLES: {len(ALL_TITLES)} titles")
    print(f"GCC_COUNTRIES: {len(GCC_COUNTRIES)} countries")
    print(f"PRIORITY_COUNTRIES: {PRIORITY_COUNTRIES}")
    print(f"ATS_KEYWORDS: {len(ATS_KEYWORDS)} keywords")
    
    # Test is_relevant
    test_cases = [
        ("VP Digital Transformation", "Dubai"),
        ("Director of Engineering", "Saudi Arabia"),
        ("Sales Manager", "UAE"),
        ("Software Engineer", "Qatar"),
        ("Chief Technology Officer", "Riyadh"),
    ]
    
    print("\n--- is_relevant() tests ---")
    for title, loc in test_cases:
        relevant, reason = is_relevant(title, loc)
        status = "✅" if relevant else "❌"
        print(f"{status} '{title}' in {loc}: {reason}")
    
    # Test keyword scoring
    print("\n--- basic_keyword_score() tests ---")
    texts = [
        "VP Digital Transformation leading PMO and strategic planning",
        "Software Developer with Python experience",
        "Director of Technology with P&L responsibility in fintech",
    ]
    for text in texts:
        score, keywords = basic_keyword_score(text)
        print(f"Score {score}: {text[:50]}... -> {keywords[:5]}")
    
    # Test standard_job_dict
    print("\n--- standard_job_dict() test ---")
    job = standard_job_dict(
        job_id="12345",
        source="test",
        title="VP Digital Transformation",
        company="Test Corp",
        location="Dubai, UAE",
        url="https://example.com/job/12345",
        posted="2026-03-20",
        raw_snippet="Leading digital transformation initiatives across enterprise"
    )
    import json
    print(json.dumps(job, indent=2))
