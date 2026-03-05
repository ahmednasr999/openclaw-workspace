#!/usr/bin/env python3
"""
LinkedIn Job Scout ATS Scorer v2
Composite scoring: keyword match + seniority + sector + location + dealbreakers
Usage: scout-ats.py <jd_text_or_file> [--location LOCATION]
"""

import re
import sys
import json
from pathlib import Path

# === KEYWORD WEIGHTS (40% of total) ===
CV_KEYWORDS = {
    # Core strengths (high weight)
    "digital transformation": 12, "pmo": 12, "program management": 12,
    "portfolio management": 10, "project management": 10,
    "artificial intelligence": 12, "ai strategy": 14, "ai governance": 12,
    "healthcare ai": 15, "clinical ai": 15, "health tech": 14, "healthtech": 14,
    "enterprise ai": 12, "genai": 10, "generative ai": 10, "llm": 8,
    # Certifications
    "pmp": 10, "csm": 8, "cspo": 8, "lean six sigma": 10, "cbap": 8,
    # Domain
    "healthcare": 10, "hospital": 9, "clinical": 8, "medical": 8,
    "fintech": 10, "payments": 8, "banking": 7,
    "ecommerce": 8, "e-commerce": 8,
    # Skills
    "agile": 6, "scrum": 6, "waterfall": 4,
    "stakeholder": 6, "vendor management": 6,
    "budget": 6, "cost optimization": 7, "roi": 6,
    "cloud": 5, "aws": 4, "azure": 4, "gcp": 4,
    "erp": 5, "sap": 5, "salesforce": 5,
    "data analytics": 6, "business intelligence": 6,
    "change management": 7, "organizational transformation": 8,
    "team leadership": 6, "cross-functional": 6,
    "product management": 7, "product strategy": 8, "product roadmap": 7,
    "b2b saas": 8, "enterprise": 5,
}

# === SENIORITY SCORING (20% of total) ===
SENIORITY_TIERS = {
    # Tier 1: Perfect level (20 pts)
    "chief": 20, "cto": 20, "cdo": 20, "cio": 20, "cpo": 20,
    "vice president": 20, "vp ": 20,
    # Tier 2: Strong fit (16 pts)
    "senior director": 16, "executive director": 16,
    "head of": 16, "director": 14,
    # Tier 3: Acceptable (10 pts)
    "senior manager": 10, "principal": 10,
    # Tier 4: Below target (5 pts)
    "manager": 5, "lead": 5,
    # Tier 5: Too junior (0 pts)
    "analyst": 0, "coordinator": 0, "associate": 0, "specialist": 0,
}

# === SECTOR SCORING (20% of total) ===
SECTOR_TIERS = {
    # Tier 1: Sweet spot (20 pts)
    "healthcare": 20, "health tech": 20, "healthtech": 20, "hospital": 20,
    "clinical": 18, "medical": 18,
    "fintech": 20, "financial technology": 20,
    "digital transformation": 18,
    # Tier 2: Strong fit (14 pts)
    "e-commerce": 14, "ecommerce": 14, "technology": 12,
    "saas": 14, "software": 12, "ai company": 16,
    "consulting": 12, "advisory": 14,
    # Tier 3: Neutral (8 pts)
    "telecom": 8, "banking": 10, "insurance": 8,
    "real estate": 8, "hospitality": 8, "retail": 8,
    # Tier 4: Poor fit (3 pts)
    "defense": 3, "military": 3, "aerospace": 3,
    "oil and gas": 3, "mining": 3, "construction": 3,
    "manufacturing": 5, "logistics": 5,
}

# === LOCATION SCORING (10% of total) ===
LOCATION_SCORES = {
    "dubai": 10, "abu dhabi": 9, "uae": 9, "united arab emirates": 9,
    "riyadh": 8, "jeddah": 8, "saudi arabia": 8, "ksa": 8,
    "doha": 7, "qatar": 7,
    "bahrain": 7, "manama": 7,
    "kuwait": 7, "kuwait city": 7,
    "oman": 7, "muscat": 7,
    "cairo": 5, "egypt": 5,
    "remote": 6, "hybrid": 7,
}

# === DEALBREAKERS (auto-skip) ===
DEALBREAKERS = [
    "security clearance",
    "secret clearance",
    "ts/sci",
    "top secret",
    "us citizen",
    "citizenship required",
    "native arabic speaker only",  # Ahmed speaks Arabic, but "only" signals exclusion
]

# === YELLOW FLAGS (penalty) ===
YELLOW_FLAGS = {
    "travel 50%": -5, "50% travel": -5, "travel up to 50": -5,
    "relocation not provided": -3,
    "entry level": -15, "junior": -10, "internship": -20,
    "on-call 24/7": -5,
}


def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s/]', ' ', text)
    return ' '.join(text.split())


def score_keywords(jd):
    """Score keyword matches (0-100, will be weighted to 40%)"""
    score = 0
    max_possible = sum(sorted(CV_KEYWORDS.values(), reverse=True)[:15])  # top 15 matches cap
    matched = []

    for kw, weight in CV_KEYWORDS.items():
        if kw in jd:
            score += weight
            matched.append(kw)

    normalized = min(100, int((score / max_possible) * 100)) if max_possible > 0 else 0
    return normalized, matched


def score_seniority(jd):
    """Score seniority level (0-20)"""
    best = 0
    matched_level = "unknown"
    for title, pts in SENIORITY_TIERS.items():
        if title in jd and pts > best:
            best = pts
            matched_level = title
    return best, matched_level


def score_sector(jd):
    """Score sector fit (0-20) - uses word boundary matching"""
    best = 0
    matched_sector = "unknown"
    for sector, pts in SECTOR_TIERS.items():
        # Use word boundary to avoid false matches
        pattern = r'\b' + re.escape(sector) + r'\b'
        if re.search(pattern, jd) and pts > best:
            best = pts
            matched_sector = sector
    # Override: if "real estate" or "land" is primary context, cap sector at 8
    if re.search(r'\b(real estate|land estate|land acquisition|zoning)\b', jd):
        land_count = len(re.findall(r'\b(real estate|land|estate|zoning)\b', jd))
        health_count = len(re.findall(r'\b(healthcare|hospital|clinical|medical)\b', jd))
        if land_count > health_count:
            best = min(best, 8)
            matched_sector = "real estate (capped)"
    return best, matched_sector


def score_location(jd, location_hint=""):
    """Score location (0-10)"""
    text = jd + " " + location_hint.lower()
    best = 0
    matched_loc = "unknown"
    for loc, pts in LOCATION_SCORES.items():
        if loc in text and pts > best:
            best = pts
            matched_loc = loc
    return best, matched_loc


def check_dealbreakers(jd):
    """Check for auto-skip dealbreakers"""
    found = []
    for db in DEALBREAKERS:
        if db in jd:
            found.append(db)
    return found


def check_yellow_flags(jd):
    """Check for penalty flags"""
    penalty = 0
    found = []
    for flag, pts in YELLOW_FLAGS.items():
        if flag in jd:
            penalty += pts
            found.append(flag)
    return penalty, found


def score_jd(jd_text, location_hint=""):
    jd = clean_text(jd_text)

    # Dealbreakers first
    dealbreakers = check_dealbreakers(jd)
    if dealbreakers:
        return {
            "score": 0,
            "verdict": "SKIP",
            "reason": f"Dealbreaker: {', '.join(dealbreakers)}",
            "breakdown": {},
            "matched_keywords": [],
        }

    # Component scores
    kw_score, kw_matched = score_keywords(jd)
    sen_score, sen_level = score_seniority(jd)
    sec_score, sec_match = score_sector(jd)
    loc_score, loc_match = score_location(jd, location_hint)
    penalty, flags = check_yellow_flags(jd)

    # Composite: 40% keywords + 20% seniority + 20% sector + 10% location + 10% base
    composite = int(
        (kw_score * 0.40) +
        (sen_score * 5 * 0.20) +  # sen_score is 0-20, normalize to 0-100
        (sec_score * 5 * 0.20) +  # sec_score is 0-20, normalize to 0-100
        (loc_score * 10 * 0.10) + # loc_score is 0-10, normalize to 0-100
        10  # base points
    )
    composite = max(0, min(100, composite + penalty))

    # Verdict
    if composite >= 80:
        verdict = "GO"
    elif composite >= 65:
        verdict = "REVIEW"
    elif composite >= 50:
        verdict = "CONDITIONAL"
    else:
        verdict = "SKIP"

    return {
        "score": composite,
        "verdict": verdict,
        "reason": "",
        "breakdown": {
            "keywords": f"{kw_score}% ({len(kw_matched)} matched)",
            "seniority": f"{sen_level} ({sen_score}/20)",
            "sector": f"{sec_match} ({sec_score}/20)",
            "location": f"{loc_match} ({loc_score}/10)",
            "flags": flags if flags else "none",
        },
        "matched_keywords": kw_matched[:10],
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: scout-ats.py <jd_text_or_file> [--location LOCATION]")
        sys.exit(1)

    jd = sys.argv[1]
    location = ""

    if "--location" in sys.argv:
        idx = sys.argv.index("--location")
        if idx + 1 < len(sys.argv):
            location = sys.argv[idx + 1]

    if len(jd) < 200 and Path(jd).exists():
        jd = Path(jd).read_text()

    result = score_jd(jd, location)

    print(f"📊 ATS Score: {result['score']}%")
    print(f"✅ Verdict: {result['verdict']}")
    if result['reason']:
        print(f"⛔ Reason: {result['reason']}")
    if result['breakdown']:
        print(f"📋 Breakdown:")
        for k, v in result['breakdown'].items():
            print(f"   {k}: {v}")
    print(f"🎯 Keywords: {', '.join(result['matched_keywords'])}")

    # Also output JSON for programmatic use
    print(f"\n__JSON__:{json.dumps(result)}")


if __name__ == "__main__":
    main()
