#!/usr/bin/env python3
"""
Automated ATS Scorer
Scores job descriptions against Ahmed's CV
"""

import re
import json
from pathlib import Path

# Ahmed's keyword profile (from his CV)
CV_KEYWORDS = {
    # Core transformation keywords
    "digital transformation": 10,
    "pmp": 10,
    "csm": 8,
    "cspo": 8,
    "lean six sigma": 10,
    "cbap": 8,
    "project management": 8,
    "program management": 10,
    "pmo": 10,
    "portfolio management": 9,
    
    # Leadership
    "lead": 5,
    "director": 8,
    "vp": 10,
    "cto": 10,
    "chief": 10,
    "head": 8,
    "executive": 7,
    "senior manager": 8,
    "manager": 5,
    
    # Technical
    "ai": 8,
    "artificial intelligence": 10,
    "ml": 7,
    "machine learning": 8,
    "data": 6,
    "data science": 8,
    "erp": 7,
    "sap": 7,
    "cloud": 6,
    "automation": 7,
    "digital": 6,
    "technology": 5,
    
    # Healthcare
    "healthcare": 10,
    "hospital": 9,
    "medical": 8,
    "topmed": 10,
    "sgh": 9,
    "patient care": 7,
    
    # Finance/FinTech
    "fintech": 8,
    "payment": 7,
    "talabat": 8,
    "delivery": 5,
    "ecommerce": 7,
    "retail": 6,
    
    # Delivery/Operations
    "delivery": 6,
    "agile": 7,
    "scrum": 7,
    "waterfall": 5,
    "stakeholder": 6,
    "vendor": 5,
    "budget": 7,
    "cost optimization": 8,
    
    # Metrics
    "roi": 7,
    "kpi": 6,
    "metrics": 5,
    "reduce": 5,
    "increase": 5,
    "improve": 5,
    "scale": 6,
    "million": 5,
    "billion": 5,
    "percent": 5,
    
    # Soft skills
    "communication": 4,
    "leadership": 6,
    "strategy": 7,
    "strategic": 7,
    "team": 4,
    "cross-functional": 6,
    "stakeholder management": 7,
}

# Must-have requirements (knockout factors)
MUST_HAVE = [
    "digital transformation",
    "project management",
    "pmo",
    "program management",
    "ai",
    "artificial intelligence",
]

# Seniority indicators
SENIORITY_KEYWORDS = [
    "vp", "vice president", "director", "chief", "head", "senior director",
    "executive", "c-suite", "cxo", "cto", "cdo", "cio", "cfo"
]

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_keywords(text: str) -> list:
    """Extract meaningful keywords from text"""
    text = clean_text(text)
    words = text.split()
    
    # Find multi-word phrases first
    phrases = []
    for keyword in CV_KEYWORDS.keys():
        if keyword in text:
            phrases.append(keyword)
    
    return phrases

def calculate_score(job_text: str) -> dict:
    """Calculate ATS score for a job description"""
    job_text = clean_text(job_text)
    
    # Start with 50 base score
    score = 50
    matched_keywords = []
    missing_must_have = []
    
    # Score keyword matches
    for keyword, weight in CV_KEYWORDS.items():
        if keyword in job_text:
            score += weight
            matched_keywords.append(keyword)
    
    # Check must-have requirements
    for req in MUST_HAVE:
        if req not in job_text:
            missing_must_have.append(req)
            score -= 10  # Penalty for missing must-haves
    
    # Seniority check (bonus for senior roles)
    seniority_count = sum(1 for kw in SENIORITY_KEYWORDS if kw in job_text)
    if seniority_count >= 2:
        score += 15  # Strong senior indicator
    elif seniority_count == 1:
        score += 8
    
    # Cap score at 100
    score = min(100, score)
    
    # Determine verdict
    if score >= 80 and not missing_must_have:
        verdict = "GO"
    elif score >= 65:
        verdict = "CONDITIONAL"
    else:
        verdict = "SKIP"
    
    # Calculate gaps
    gaps = []
    if missing_must_have:
        gaps.append(f"Missing: {', '.join(missing_must_have[:3])}")
    
    # Check for red flags
    if "intern" in job_text or "entry level" in job_text:
        gaps.append("Entry-level role")
        verdict = "SKIP"
    
    if "contract" in job_text and "12 month" in job_text:
        gaps.append("Short-term contract")
    
    return {
        "score": score,
        "verdict": verdict,
        "matched": matched_keywords[:10],
        "missing": missing_must_have,
        "gaps": gaps,
        "seniority_indicator": seniority_count >= 2
    }

def score_from_url(url: str) -> dict:
    """Score a job from LinkedIn URL using web_fetch"""
    import subprocess
    
    # For now, return placeholder - would need JD extraction
    return {
        "score": 0,
        "verdict": "NEEDS_JD",
        "matched": [],
        "missing": [],
        "gaps": ["JD not extracted yet"],
        "seniority_indicator": False
    }

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: ats-scorer.py <job_description_or_file>")
        sys.exit(1)
    
    # Read job description
    jd_path = Path(sys.argv[1])
    if jd_path.exists():
        jd = jd_path.read_text()
    else:
        jd = sys.argv[1]
    
    result = calculate_score(jd)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
