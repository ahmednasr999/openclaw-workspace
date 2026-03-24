#!/usr/bin/env python3
"""
ATS Scorer v2 — Calibrated scoring for Ahmed's job pipeline.
Replaces v1 which inflated every JD to 100/100.

Scoring model:
  Keyword Coverage  (0-40): % of weighted keywords found in JD
  Must-Have Match   (0-25): critical keywords (PMO, DT, program mgmt, etc.)
  Seniority Match   (0-15): VP/Director/Head/Chief level indicators
  Domain Specificity(0-20): healthcare, fintech, GCC, digital — Ahmed's sweet spots
  Total: 0-100

Design principle: A random Software Engineer JD should score 20-35.
A perfect-fit VP Digital Transformation PMO JD should score 85-95.
Nothing should ever score 100 — there's always some gap.
"""

import os, re, sys, json
from pathlib import Path

try:
    sys.path.insert(0, os.path.dirname(__file__))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

# ── Keyword tiers (weighted by relevance to Ahmed's CV) ──────────────────────

TIER1_CRITICAL = {
    "digital transformation": 5,
    "program management": 5,
    "pmo": 5,
    "project management": 4,
    "transformation": 4,
    "portfolio management": 4,
}

TIER2_STRONG = {
    "pmp": 3, "csm": 3, "cspo": 3, "lean six sigma": 3, "cbap": 3,
    "artificial intelligence": 3, "ai": 3, "machine learning": 3,
    "erp": 3, "sap": 3, "fintech": 3, "payment": 3,
    "healthcare": 3, "hospital": 3, "cost optimization": 3,
    "governance": 3, "operating model": 3, "change management": 3,
    "stakeholder management": 3, "vendor management": 3,
    "budget": 3, "p&l": 3, "revenue": 3,
}

TIER3_SUPPORTING = {
    "agile": 2, "scrum": 2, "waterfall": 2, "cloud": 2,
    "data": 2, "analytics": 2, "automation": 2, "digital": 2,
    "strategy": 2, "strategic": 2, "kpi": 2, "roi": 2,
    "cross-functional": 2, "stakeholder": 2,
    "scale": 1, "million": 1, "reduce": 1, "improve": 1,
    "team": 1, "leadership": 1, "communication": 1, "technology": 1,
}

ALL_KEYWORDS = {**TIER1_CRITICAL, **TIER2_STRONG, **TIER3_SUPPORTING}
MAX_KEYWORD_SCORE = sum(ALL_KEYWORDS.values())  # theoretical max

MUST_HAVE = [
    "digital transformation", "transformation",
    "project management", "program management", "pmo",
    "ai", "artificial intelligence",
]

SENIORITY_KEYWORDS = [
    "vp", "vice president", "director", "chief", "head of",
    "senior director", "executive director", "c-suite", "cxo",
    "cto", "cdo", "cio",
]

DOMAIN_KEYWORDS = {
    "healthcare": 4, "hospital": 4, "medical": 3,
    "fintech": 4, "payment": 3, "banking": 3, "financial services": 3,
    "gcc": 3, "saudi": 2, "uae": 2, "dubai": 2, "middle east": 2,
    "digital transformation": 4, "operating model": 3,
    "pmo": 3, "program office": 3,
}
MAX_DOMAIN_SCORE = sum(DOMAIN_KEYWORDS.values())

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s&]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_score(job_text: str) -> dict:
    text = clean_text(job_text)
    matched = []

    # ── Component 1: Keyword Coverage (0-40) ──
    raw_kw_score = 0
    for kw, weight in ALL_KEYWORDS.items():
        if kw in text:
            raw_kw_score += weight
            matched.append(kw)
    keyword_score = min(40, round(40 * raw_kw_score / MAX_KEYWORD_SCORE * 2))
    # * 2 factor: a good JD matching ~50% of keywords = full 40 pts

    # ── Component 2: Must-Have (0-25) ──
    must_found = sum(1 for req in MUST_HAVE if req in text)
    must_score = round(25 * must_found / len(MUST_HAVE))
    missing_must = [req for req in MUST_HAVE if req not in text]

    # ── Component 3: Seniority (0-15) ──
    sen_count = sum(1 for kw in SENIORITY_KEYWORDS if kw in text)
    if sen_count >= 3:
        sen_score = 15
    elif sen_count == 2:
        sen_score = 12
    elif sen_count == 1:
        sen_score = 8
    else:
        sen_score = 0

    # ── Component 4: Domain Specificity (0-20) ──
    raw_domain = sum(w for kw, w in DOMAIN_KEYWORDS.items() if kw in text)
    domain_score = min(20, round(20 * raw_domain / MAX_DOMAIN_SCORE * 2.5))

    # ── Total ──
    total = keyword_score + must_score + sen_score + domain_score

    # ── Red flags ──
    gaps = []
    if "intern" in text or "entry level" in text or "junior" in text:
        total = max(total - 30, 5)
        gaps.append("Entry/junior level")
    if missing_must:
        gaps.append(f"Missing: {', '.join(missing_must[:3])}")

    # Cap at 98 — nothing is perfect
    total = min(98, max(0, total))

    if total >= 75:
        verdict = "GO"
    elif total >= 55:
        verdict = "CONDITIONAL"
    else:
        verdict = "SKIP"

    return {
        "score": total,
        "verdict": verdict,
        "matched": matched[:10],
        "missing": missing_must,
        "gaps": gaps,
        "seniority_indicator": sen_count >= 2,
        "components": {
            "keyword": keyword_score,
            "must_have": must_score,
            "seniority": sen_score,
            "domain": domain_score,
        }
    }

def fetch_page(url: str) -> str:
    import urllib.request
    try:
        clean = url.replace("https://", "").replace("http://", "")
        req = urllib.request.Request(f"https://defuddle.md/{clean}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 200:
                return content
    except Exception:
        pass
    try:
        req = urllib.request.Request(f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 200:
                return content
    except Exception:
        pass
    return ""

def score_from_url(url: str) -> dict:
    jd = fetch_page(url)
    if not jd or len(jd) < 200:
        return {"score": 0, "verdict": "NEEDS_JD", "matched": [], "missing": [],
                "gaps": ["JD not extracted"], "seniority_indicator": False}
    return calculate_score(jd)

def score_and_save(job_id: str, jd_text: str, fit_score: int = None, verdict: str = None) -> dict:
    result = calculate_score(jd_text)
    if _pdb and job_id:
        try:
            _pdb.update_score(
                job_id=job_id, ats_score=result.get("score"),
                fit_score=fit_score, verdict=verdict or result.get("verdict"),
                notes=", ".join(result.get("matched", [])[:5]),
            )
        except Exception:
            pass
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: job-scorer.py <job_description_or_file>")
        sys.exit(1)
    jd_path = Path(sys.argv[1])
    jd = jd_path.read_text() if jd_path.exists() else sys.argv[1]
    result = calculate_score(jd)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
