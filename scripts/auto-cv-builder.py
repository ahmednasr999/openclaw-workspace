#!/usr/bin/env python3
"""
Auto CV Builder
===============
Reads trigger files from jobs-bank/handoff/, calls Opus 4.6 to tailor CV,
generates PDF via WeasyPrint, pushes to GitHub.

Usage:
    python3 auto-cv-builder.py                    # Process all pending triggers
    python3 auto-cv-builder.py --trigger FILE     # Process one specific trigger
    python3 auto-cv-builder.py --dry-run          # Show what would be built, no API calls

Returns JSON list of built CVs (for orchestrator integration).
"""

import json, os, sys, re, subprocess, argparse, glob, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

# ── Cluster definitions ──────────────────────────────────────────────────────
CLUSTERS = {
    "PMO & Program Management": ["pmo", "program manager", "project director", "project management", "project controls", "project execution", "program director", "project manager", "delivery manager", "delivery lead", "service delivery", "project excellence"],
    "Digital Transformation & Strategy": ["transformation", "strategy", "strategic", "chief strategy", "business excellence", "innovation", "change management", "chief of staff"],
    "CTO & Technology Leadership": ["cto", "chief technology", "head of engineering", "head of it", "director of it", "director of engineering", "it director", "vp technology", "director technology", "head of tech", "head of software", "head of solutions", "group cio", "enterprise architecture"],
    "Data & AI Leadership": ["data", "analytics", "ai ", "artificial intelligence", "machine learning", "data science", "business intelligence", "head of data"],
    "Product & E-Commerce": ["product", "e-commerce", "ecommerce", "head of product", "director of product", "product management"],
    "FinTech & Financial Services": ["fintech", "financial", "banking", "payments", "credit", "fund", "treasury", "revenue operations"],
    "Operations & COO": ["coo", "chief operating", "operations", "facilities", "supply chain", "logistics", "quality control"],
}

WORKSPACE   = "/root/.openclaw/workspace"
HANDOFF_DIR = f"{WORKSPACE}/jobs-bank/handoff"
CVS_DIR     = f"{WORKSPACE}/cvs"
MASTER_CV   = f"{WORKSPACE}/memory/master-cv-data.md"
PENDING_CV  = f"{WORKSPACE}/memory/cv-pending-updates.md"
OPENCLAW_JSON = "/root/.openclaw/openclaw.json"

ANTHROPIC_API_KEY = ""
ANTHROPIC_BASE_URL = "https://api.anthropic.com"
GATEWAY_TOKEN = ""
GATEWAY_PORT = 18789
USE_GATEWAY = False

# CV HTML template (from proven working CVs)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Ahmed Nasr - {role_title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10.5pt;
    line-height: 1.45;
    color: #111;
    background: #fff;
    padding: 18mm 18mm 16mm 18mm;
  }}
  .header-name {{ font-size: 20pt; font-weight: bold; color: #111; margin-bottom: 4pt; }}
  .header-contact {{ font-size: 9.5pt; color: #444; margin-bottom: 10pt; }}
  .header-divider {{ border: none; border-top: 2px solid #111; margin-bottom: 10pt; }}
  h2 {{
    font-size: 10.5pt; font-weight: bold; text-transform: uppercase;
    letter-spacing: 0.6pt; color: #111; border-bottom: 1pt solid #aaa;
    padding-bottom: 2pt; margin-top: 12pt; margin-bottom: 6pt;
  }}
  .summary {{ margin-bottom: 4pt; font-size: 10.5pt; }}
  .skills-list {{ font-size: 10pt; margin-bottom: 4pt; }}
  .job {{ margin-bottom: 9pt; }}
  .job-row-inner {{ display: table; width: 100%; }}
  .job-title-cell {{
    display: table-cell; font-weight: bold; font-size: 10.5pt;
    vertical-align: top; width: 75%;
  }}
  .job-date-cell {{
    display: table-cell; font-size: 9.5pt; color: #555;
    text-align: right; vertical-align: top; width: 25%; white-space: nowrap;
  }}
  .job-company {{ font-size: 9.5pt; color: #444; margin-bottom: 4pt; font-style: italic; }}
  ul {{ margin-left: 15pt; margin-bottom: 0; }}
  ul li {{ margin-bottom: 2.5pt; font-size: 10.5pt; }}
  .education {{ margin-bottom: 3pt; }}
  .edu-title {{ font-weight: bold; font-size: 10.5pt; }}
  .edu-detail {{ font-size: 9.5pt; color: #444; }}
  .certs {{ font-size: 10pt; }}
  @media print {{ body {{ padding: 15mm; }} }}
</style>
</head>
<body>
{body_html}
</body>
</html>"""


def log(msg):
    cairo = timezone(timedelta(hours=2))
    ts = datetime.now(cairo).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def load_config():
    global ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, GATEWAY_TOKEN, GATEWAY_PORT, USE_GATEWAY
    try:
        with open(OPENCLAW_JSON) as f:
            cfg = json.load(f)
        p = cfg.get("models", {}).get("providers", {}).get("anthropic", {})
        ANTHROPIC_API_KEY = p.get("apiKey", "")
        ANTHROPIC_BASE_URL = p.get("baseUrl", "https://api.anthropic.com")
        # Gateway config (preferred over direct API)
        gw = cfg.get("gateway", {})
        gw_auth = gw.get("auth", {})
        GATEWAY_TOKEN = gw_auth.get("token", "")
        GATEWAY_PORT = gw.get("port", 18789)
        if GATEWAY_TOKEN:
            USE_GATEWAY = True
            log(f"  Using OpenClaw Gateway on port {GATEWAY_PORT}")
    except Exception as e:
        log(f"WARNING: Could not load config: {e}")


def load_master_cv():
    with open(MASTER_CV) as f:
        return f.read()


def load_pending_updates():
    if os.path.exists(PENDING_CV):
        with open(PENDING_CV) as f:
            return f.read()
    return ""


def find_pending_triggers():
    """Find trigger files that haven't been processed yet."""
    triggers = []
    for f in glob.glob(f"{HANDOFF_DIR}/*.trigger"):
        # Skip already-processed triggers
        if f.endswith(".dropped") or f.endswith(".done"):
            continue
        with open(f) as fh:
            content = fh.read()
        if "NASR_REVIEW_NEEDED" in content and "---JD---" in content:
            triggers.append(f)
    return triggers


def parse_trigger(filepath):
    """Parse a trigger file into structured data."""
    with open(filepath) as f:
        content = f.read()

    data = {"file": filepath}
    for line in content.split("\n"):
        if line.startswith("Title:"):
            data["title"] = line.split(":", 1)[1].strip()
        elif line.startswith("Company:"):
            data["company"] = line.split(":", 1)[1].strip()
        elif line.startswith("Location:"):
            data["location"] = line.split(":", 1)[1].strip()
        elif line.startswith("Score:"):
            data["score"] = line.split(":", 1)[1].strip()
        elif line.startswith("URL:"):
            data["url"] = line.split(":", 1)[1].strip()

    # Extract JD
    if "---JD---" in content:
        data["jd"] = content.split("---JD---", 1)[1].strip()
    else:
        data["jd"] = ""

    return data


def cv_already_exists(company, role):
    """Check if a CV already exists for this company/role."""
    pattern = f"Ahmed Nasr*{company}*"
    matches = glob.glob(f"{CVS_DIR}/{pattern}.pdf")
    if matches:
        return matches[0]
    # Also check by role
    pattern2 = f"Ahmed Nasr*{role}*"
    matches2 = glob.glob(f"{CVS_DIR}/{pattern2}.pdf")
    return matches2[0] if matches2 else None


def call_opus(prompt, max_tokens=8000):
    """Call Opus 4.6 via OpenClaw Gateway (preferred) or direct Anthropic API."""
    if USE_GATEWAY and GATEWAY_TOKEN:
        payload = json.dumps({
            "model": "anthropic/claude-opus-4-6",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()

        req = urllib.request.Request(
            f"http://localhost:{GATEWAY_PORT}/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GATEWAY_TOKEN}"
            },
            method="POST"
        )

        # Retry up to 3 times on timeout
        last_err = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=360) as resp:
                    result = json.loads(resp.read())
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            except Exception as e:
                last_err = e
                log(f"  Opus attempt {attempt+1}/3 failed: {e}")
                import time; time.sleep(5)
        raise last_err

    # Fallback: direct Anthropic API
    if not ANTHROPIC_API_KEY:
        raise ValueError("No Anthropic API key and no gateway token")

    payload = json.dumps({
        "model": "claude-opus-4-6",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        f"{ANTHROPIC_BASE_URL}/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
        return result.get("content", [{}])[0].get("text", "").strip()


def tailor_cv(master_cv, pending_updates, job_data):
    """Call Opus 4.6 to tailor CV body HTML for a specific role."""
    log(f"  Calling Opus 4.6 for CV tailoring...")

    prompt = f"""You are an expert executive CV writer. Tailor Ahmed Nasr's CV for this specific role.

## JOB DESCRIPTION
Company: {job_data.get('company', 'Unknown')}
Role: {job_data.get('title', 'Unknown')}
Location: {job_data.get('location', 'GCC')}

{job_data.get('jd', 'No JD available')}

## MASTER CV DATA (source of truth, never fabricate beyond this)
{master_cv}

## PENDING UPDATES TO APPLY
{pending_updates if pending_updates else 'None'}

## OUTPUT REQUIREMENTS
Generate ONLY the HTML body content (everything between <body> and </body>). Do NOT include <html>, <head>, <style>, or <body> tags.

Structure:
1. Header: name + contact line (phone | email | LinkedIn | location)
2. <hr class="header-divider">
3. Executive Summary (h2): 3-4 sentences, tailored to THIS role. Lead with most relevant achievement.
4. Core Competencies (h2): 12-16 most relevant skills as comma-separated list in <p class="skills-list">
5. Professional Experience (h2): All roles from master CV. Reorder bullets within each role to lead with most JD-relevant. Use <div class="job"> wrapper.
6. Education (h2)
7. Certifications (h2)

## HARD RULES
- NEVER use em dashes. Use commas, periods, or colons.
- NEVER fabricate metrics or roles not in the master CV data.
- NEVER put role/company name in the header (only "Ahmed Nasr" and contact).
- Position as Digital Transformation Executive, never consultant.
- Quantify everything: $50M, 15 hospitals, 233x, 300+ projects.
- For KSA roles: mention Saudi Vision 2030 explicitly.
- For healthcare roles: mention JCI, HIMSS, MOH, clinical AI.
- Reorder bullets to lead with most relevant to THIS JD.
- Keep to 2 pages max.

Output ONLY raw HTML. No markdown, no explanation, no ```html blocks."""

    html_body = call_opus(prompt)

    # Clean up any stray markdown
    html_body = html_body.replace("```html", "").replace("```", "").strip()
    # Remove em dashes
    html_body = html_body.replace("\u2014", ",").replace("\u2013", ",")

    return html_body


def generate_pdf(html_body, company, role, html_path_override=None):
    """Generate PDF from HTML body via WeasyPrint."""
    safe_role = re.sub(r'[^\w\s-]', '', role).strip()[:50]
    safe_company = re.sub(r'[^\w\s-]', '', company).strip()[:30]
    filename = f"Ahmed Nasr - {safe_role} - {safe_company}"

    html_path = html_path_override or f"{CVS_DIR}/{filename}.html"
    pdf_path = f"{CVS_DIR}/{filename}.pdf"

    os.makedirs(CVS_DIR, exist_ok=True)

    if not html_path_override:
        full_html = HTML_TEMPLATE.format(
            role_title=f"{safe_role} - {safe_company}",
            body_html=html_body
        )
        with open(html_path, "w") as f:
            f.write(full_html)

    log(f"  Running WeasyPrint...")
    result = subprocess.run(
        ["weasyprint", html_path, pdf_path],
        capture_output=True, text=True, timeout=60
    )

    if result.returncode != 0:
        log(f"  WeasyPrint error: {result.stderr[:200]}")
        return None, None

    # Quality checks
    size = os.path.getsize(pdf_path)
    log(f"  PDF size: {size} bytes")

    if size < 5000:
        log(f"  WARNING: PDF too small ({size}B), might be empty")
    elif size > 100000:
        log(f"  WARNING: PDF too large ({size}B), might have embedded fonts")

    # Check for em dashes
    try:
        r = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True, text=True, timeout=10)
        text = r.stdout
        em_count = text.count("\u2014") + text.count("\u2013")
        if em_count > 0:
            log(f"  WARNING: {em_count} em dashes found in PDF text")
        chars = len(text)
        log(f"  Extractable chars: {chars}")
    except:
        pass

    return html_path, pdf_path


def validate_cv(html_path):
    """Post-build quality gate. Returns (pass: bool, issues: list[str])."""
    issues = []
    try:
        with open(html_path) as f:
            html = f.read()
    except Exception as e:
        return False, [f"Cannot read HTML: {e}"]

    html_lower = html.lower()

    # 1. Education section exists
    if "<h2>education</h2>" not in html_lower:
        issues.append("MISSING: Education section")

    # 2. Certifications section exists
    if "<h2>certifications</h2>" not in html_lower and "<h2>professional certifications</h2>" not in html_lower:
        issues.append("MISSING: Certifications section")

    # 3. Check for em dashes and en dashes in content
    em_count = html.count("\u2014") + html.count("&mdash;")
    en_count = html.count("\u2013") + html.count("&ndash;")
    if em_count > 0:
        issues.append(f"STYLE: {em_count} em dashes found")
    if en_count > 0:
        issues.append(f"STYLE: {en_count} en dashes found")

    # 4. Check for broken entities (ATandT, etc.)
    broken = ["ATandT", "AT and T", "at and t"]
    for b in broken:
        if b in html:
            issues.append(f"ENTITY: '{b}' should be 'AT&amp;T'")

    # 5. Reverse chronological order check
    import re
    date_pattern = re.compile(r'class="job-date"[^>]*>([^<]+)<')
    dates_found = date_pattern.findall(html)
    if not dates_found:
        # Try alternate: <span class="job-date">
        date_pattern2 = re.compile(r'<span[^>]*job.date[^>]*>([^<]+)<', re.IGNORECASE)
        dates_found = date_pattern2.findall(html)

    if dates_found:
        year_pattern = re.compile(r'(\d{4})')
        years = []
        for d in dates_found:
            m = year_pattern.search(d)
            if m:
                yr = int(m.group(1))
                if "present" in d.lower():
                    yr = 9999
                years.append(yr)
        # Check descending
        for i in range(len(years) - 1):
            if years[i] < years[i + 1]:
                issues.append(f"ORDER: Roles not in reverse chronological order (found {dates_found[i]} before {dates_found[i+1]})")
                break

    # 6. Contact info present
    if "ahmednasr999@gmail.com" not in html:
        issues.append("MISSING: Email address")
    if "+971 50 281 4490" not in html:
        issues.append("MISSING: Phone number")

    # 7. Minimum content check
    if len(html) < 3000:
        issues.append(f"THIN: HTML only {len(html)} chars, likely incomplete")

    passed = len(issues) == 0
    return passed, issues


def auto_fix_cv(html_path, issues):
    """Attempt automatic fixes for common issues. Returns count of fixes applied."""
    try:
        with open(html_path) as f:
            html = f.read()
    except:
        return 0

    fixes = 0

    # Fix em dashes
    if any("em dash" in i.lower() for i in issues):
        html = html.replace("\u2014", "-").replace("&mdash;", "-")
        fixes += 1

    # Fix en dashes
    if any("en dash" in i.lower() for i in issues):
        html = html.replace("\u2013", "-").replace("&ndash;", "-")
        fixes += 1

    # Fix broken entities
    if any("ATandT" in i for i in issues):
        html = html.replace("ATandT", "AT&amp;T").replace("AT and T", "AT&amp;T")
        fixes += 1

    # Inject MISSING Certifications section from master CV
    import re as _re
    if any("MISSING: Certifications" in _i for _i in issues):
        _certs = (
            "<h2>Professional Certifications</h2>"
            "<ul>"
            "<li><strong>PMP</strong> &#8212; Project Management Professional, PMI, 2008</li>"
            "<li><strong>CSM</strong> &#8212; Certified Scrum Master, Scrum Alliance, 2014</li>"
            "<li><strong>CSPO</strong> &#8212; Certified Scrum Product Owner, Scrum Alliance, 2014</li>"
            "<li><strong>CBAP</strong> &#8212; Certified Business Analysis Professional, IIBA, 2014</li>"
            "<li><strong>Lean Six Sigma</strong> &#8212; SUNY, 2010</li>"
            "<li><strong>ITIL Foundations</strong> &#8212; LinkedIn, 2016</li>"
            "</ul>"
        )
        _m = _re.search(r'(<h2>education</h2>.+?)(?=<h2>)', html, _re.DOTALL | _re.IGNORECASE)
        if _m:
            html = html[:_m.end()] + _certs + html[_m.end():]
        else:
            html = _certs + html
        fixes += 1

    if fixes > 0:
        with open(html_path, "w") as f:
            f.write(html)

    return fixes


def classify_job(title):
    """Return the cluster name for a job title, or None if no match."""
    if not title:
        return None
    title_lower = title.lower()
    for cluster, keywords in CLUSTERS.items():
        for kw in keywords:
            if kw in title_lower:
                return cluster
    return None


def find_cluster_template(cluster, company):
    """
    Query the DB for the most recent completed CV in the same cluster (different company).
    Returns (html_body_content, source_description) or (None, None).
    """
    if not _pdb or not cluster:
        return None, None
    try:
        import sqlite3
        db_path = "/root/.openclaw/workspace/data/nasr-pipeline.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT company, title, cv_html_path, cv_built_at
               FROM jobs
               WHERE cv_cluster = ?
                 AND cv_html_path IS NOT NULL
                 AND cv_html_path != ''
                 AND LOWER(company) != LOWER(?)
               ORDER BY cv_built_at DESC
               LIMIT 5""",
            (cluster, company)
        ).fetchall()
        conn.close()

        for row in rows:
            html_path = row["cv_html_path"]
            if html_path and os.path.exists(html_path):
                with open(html_path) as f:
                    full_html = f.read()
                # Extract body content only
                body_match = re.search(r'<body[^>]*>(.*?)</body>', full_html, re.DOTALL | re.IGNORECASE)
                body_content = body_match.group(1).strip() if body_match else full_html
                source_desc = f"{row['title']} @ {row['company']}"
                log(f"  Cluster template found: {source_desc} ({html_path})")
                return body_content, source_desc

    except Exception as e:
        log(f"  find_cluster_template error (non-fatal): {e}")

    return None, None


def adapt_cv(template_html, master_cv, pending_updates, job_data):
    """
    Lighter Opus call: adapt an existing cluster-matched CV template for a new role.
    Uses ~40% of the tokens vs a full tailor_cv() build.
    """
    log(f"  Calling Opus 4.6 for CV ADAPTATION (cluster reuse)...")

    prompt = f"""You are an expert executive CV writer. Below is an existing CV (HTML body) built for a similar role. Adapt it for the new job below.

## NEW JOB
Company: {job_data.get('company', 'Unknown')}
Role: {job_data.get('title', 'Unknown')}
Location: {job_data.get('location', 'GCC')}

{job_data.get('jd', 'No JD available')[:3000]}

## EXISTING CV TEMPLATE (same cluster, similar role)
{template_html[:6000]}

## MASTER CV DATA (authoritative — never fabricate beyond this)
{master_cv[:3000]}

## PENDING UPDATES
{pending_updates if pending_updates else 'None'}

## TASK
Adapt the existing CV template for the new role. Make targeted changes:
1. Update the Professional Summary for this specific role/company.
2. Rewrite bullet points within each job to lead with the most JD-relevant achievements.
3. Update Core Competencies to match this JD's key terms.
4. Do NOT change dates, job titles, company names, or metrics (unless instructed by pending updates).

## MANDATORY STRUCTURE (non-negotiable)
The CV MUST contain ALL of these sections in this exact order:
1. **Header**: Name, contact info (Dubai, UAE | +971 50 281 4490 | ahmednasr999@gmail.com | linkedin.com/in/ahmednasr)
2. **Professional Summary**: 3-4 lines tailored to the JD
3. **Core Competencies**: 10-12 items in a list, keyword-matched to JD
4. **Professional Experience**: ALL roles in REVERSE CHRONOLOGICAL ORDER:
   - PMO & Regional Engagement Lead | Saudi German Hospital Group | Jun 2024 - Present
   - Country Manager | PaySky, Inc. | Apr 2021 - Jan 2022
   - Head of E-Commerce Product & IT Strategy | Al Araby Group | Jan 2020 - Jan 2021
   - Product Development Manager | Delivery Hero SE (Talabat) | Jun 2017 - May 2018
   - PMO Section Head | Network International | Sep 2014 - Jun 2017
   - Engagement Manager | Revamp Consulting | Mar 2013 - Sep 2014
   - Earlier Career (2004-2013): Intel Corporation, BlueCloud, SySDSoft (1-2 lines)
5. **Education**:
   - MBA, International Business Administration - Paris ESLSCA Business School (2025 - 2027, In Progress)
   - BSc Computer Science - Ain Shams University (2004)
6. **Certifications**: PMP, CSM, CSPO, CBAP, Lean Six Sigma, ITIL Foundations

You may omit a role ONLY if space requires it AND it is not relevant to the JD. Never omit Education or Certifications.

## DATE FORMAT
Always use: "Mon YYYY - Mon YYYY" with a hyphen surrounded by spaces. Example: "Jun 2024 - Present". Never use commas, en dashes, or other separators for date ranges.

## OUTPUT REQUIREMENTS
Output ONLY the HTML body content (between <body> and </body>). No <html>, <head>, <style>, or <body> tags.

## HARD RULES
- NEVER use em dashes (—) or en dashes (–). Use commas, periods, hyphens, or colons.
- NEVER fabricate metrics or roles not in master CV data.
- Keep to 2 pages max.
- Use &amp; for ampersands in HTML (e.g., AT&amp;T not ATandT).

Output ONLY raw HTML. No markdown, no explanation, no ```html blocks."""

    html_body = call_opus(prompt, max_tokens=5000)

    # Clean up
    html_body = html_body.replace("```html", "").replace("```", "").strip()
    html_body = html_body.replace("\u2014", ",").replace("\u2013", ",")

    return html_body


def ats_score_check(jd_text, master_cv):
    """Quick ATS scoring via keyword matching (no LLM needed)."""
    jd_lower = jd_text.lower()
    cv_lower = master_cv.lower()

    # Key terms to check
    matches = 0
    total = 0
    for term in [
        "digital transformation", "pmo", "program management", "project management",
        "ai", "machine learning", "cloud", "aws", "azure", "agile", "scrum",
        "healthcare", "fintech", "e-commerce", "vision 2030",
        "leadership", "strategy", "p&l", "budget", "stakeholder",
        "director", "vp", "head of", "chief", "executive",
        "gcc", "uae", "saudi", "dubai", "abu dhabi", "ksa"
    ]:
        if term in jd_lower:
            total += 1
            if term in cv_lower:
                matches += 1

    if total == 0:
        return 50
    return int((matches / total) * 100)


def process_trigger(trigger_path, master_cv, pending_updates, dry_run=False):
    """Process a single trigger file: tailor CV, generate PDF."""
    data = parse_trigger(trigger_path)
    company = data.get("company", "Unknown")
    role = data.get("title", "Unknown")
    jd = data.get("jd", "")

    log(f"Processing: {role} @ {company}")
    log(f"  Score: {data.get('score', 'N/A')}")
    log(f"  JD length: {len(jd)} chars")

    if not jd or len(jd) < 100:
        log(f"  SKIP: JD too short ({len(jd)} chars)")
        return None

    # Check if CV already exists
    existing = cv_already_exists(company, role)
    if existing:
        log(f"  SKIP: CV already exists: {os.path.basename(existing)}")
        return {
            "company": company,
            "role": role,
            "pdf_path": existing,
            "status": "existing",
            "github_link": f"https://github.com/ahmednasr999/openclaw-workspace/blob/master/cvs/{os.path.basename(existing).replace(' ', '%20')}"
        }

    # Quick ATS pre-check
    ats = ats_score_check(jd, master_cv)
    log(f"  Quick ATS estimate: {ats}%")
    if ats < 50:
        log(f"  SKIP: ATS too low ({ats}%)")
        return None

    # Classify job into cluster
    cluster = classify_job(role)
    if cluster:
        log(f"  Cluster: {cluster}")
    else:
        log(f"  Cluster: none (will build from scratch)")

    if dry_run:
        log(f"  DRY RUN: Would tailor CV for {role} @ {company}")
        return {"company": company, "role": role, "status": "dry_run", "ats_estimate": ats, "cluster": cluster}

    # Attempt cluster reuse: find a template CV from same cluster
    template_html = None
    template_source = None
    build_path = "NEW"

    if cluster:
        template_html, template_source = find_cluster_template(cluster, company)

    # Tailor CV via Opus 4.6 — reuse path or full build
    try:
        if template_html:
            log(f"  REUSE: adapting {template_source}")
            build_path = f"REUSE ({template_source})"
            html_body = adapt_cv(template_html, master_cv, pending_updates, data)
        else:
            log(f"  NEW: building from scratch")
            html_body = tailor_cv(master_cv, pending_updates, data)
        log(f"  CV body: {len(html_body)} chars [{build_path}]")
    except Exception as e:
        log(f"  ERROR calling Opus: {e}")
        return None

    # Generate PDF
    try:
        html_path, pdf_path = generate_pdf(html_body, company, role)
        if not pdf_path:
            return None
    except Exception as e:
        log(f"  ERROR generating PDF: {e}")
        return None

    # Post-build validation
    passed, issues = validate_cv(html_path)
    if not passed:
        fixable = [i for i in issues if i.startswith("STYLE:") or i.startswith("ENTITY:")]
        blockers = [i for i in issues if i not in fixable]

        if fixable:
            fix_count = auto_fix_cv(html_path, issues)
            log(f"  AUTO-FIX: {fix_count} issue(s) patched")
            # Regenerate PDF after fixes
            try:
                html_path, pdf_path = generate_pdf(None, company, role, html_path_override=html_path)
                log(f"  PDF regenerated after auto-fix")
            except:
                pass

        if blockers:
            log(f"  ⚠️ VALIDATION FAILED ({len(blockers)} blocker(s)):")
            for b in blockers:
                log(f"    - {b}")
            log(f"  CV built but flagged for manual review.")
        else:
            log(f"  ✅ Validation PASSED (after {len(fixable)} auto-fix(es))")
    else:
        log(f"  ✅ Validation PASSED")

    # Mark trigger as done
    done_path = trigger_path + ".done"
    os.rename(trigger_path, done_path)
    log(f"  Trigger marked as done.")

    github_link = f"https://github.com/ahmednasr999/openclaw-workspace/blob/master/cvs/{os.path.basename(pdf_path).replace(' ', '%20')}"

    return {
        "company": company,
        "role": role,
        "pdf_path": pdf_path,
        "html_path": html_path,
        "ats_estimate": ats,
        "status": "built",
        "github_link": github_link,
        "cluster": cluster,
        "build_path": build_path,
        "trigger": data,
    }


def git_push_cvs():
    """Git add, commit, push new CVs."""
    log("Pushing CVs to GitHub...")
    try:
        subprocess.run(
            "cd /root/.openclaw/workspace && git add cvs/ jobs-bank/handoff/ && "
            'git commit -m "auto-cv: tailored CVs for qualified roles" && git push',
            shell=True, capture_output=True, text=True, timeout=60
        )
        log("  Pushed to GitHub.")
    except Exception as e:
        log(f"  Git push failed: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", help="Process one specific trigger file")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    load_config()
    master_cv = load_master_cv()
    pending = load_pending_updates()

    if args.trigger:
        triggers = [args.trigger]
    else:
        triggers = find_pending_triggers()

    if not triggers:
        log("No pending trigger files found.")
        if args.json:
            print(json.dumps([]))
        return

    log(f"Found {len(triggers)} pending trigger(s)")
    results = []

    for t in triggers:
        result = process_trigger(t, master_cv, pending, dry_run=args.dry_run)
        if result:
            results.append(result)

    # Git push if any CVs were built
    built = [r for r in results if r.get("status") == "built"]
    if built and not args.dry_run:
        git_push_cvs()

    # ── DB writes for built CVs (dual-write, non-blocking) ───────────────────
    if _pdb and built:
        try:
            db_count = 0
            for r in built:
                trigger_data = r.get("trigger", {}) if isinstance(r.get("trigger"), dict) else {}
                job_id = str(trigger_data.get("job_id", trigger_data.get("id", ""))).strip()
                cv_path = r.get("pdf_path", r.get("cv_path", ""))
                html_path = r.get("html_path", "")
                company = trigger_data.get("company", r.get("company", ""))
                title = trigger_data.get("role", r.get("role", ""))

                if not job_id and company and title:
                    import hashlib
                    job_id = f"cv-{hashlib.md5(f'{company}|{title}'.encode()).hexdigest()[:10]}"

                cluster = r.get("cluster", None)
                if job_id and cv_path:
                    _pdb.attach_cv(job_id=job_id, cv_path=cv_path, cv_html_path=html_path or None, cluster=cluster)
                    db_count += 1

            log(f"  DB: {db_count} CVs linked")
        except Exception as _e:
            log(f"  DB write failed (non-fatal): {_e}")
    # ─────────────────────────────────────────────────────────────────────────

    # ── DB query: report unbuilt CVs ─────────────────────────────────────────
    if _pdb:
        try:
            # Jobs with SUBMIT verdict but no CV yet
            submit_jobs = _pdb.search(verdict="SUBMIT")
            unbuilt = [j for j in submit_jobs if not j.get("cv_path")]
            if unbuilt:
                log(f"\n  Unbuilt CVs needed: {len(unbuilt)} SUBMIT jobs without CV")
                for j in unbuilt[:5]:
                    log(f"    - {j['company']} | {j['title'][:50]}")
        except Exception:
            pass
    # ─────────────────────────────────────────────────────────────────────────

    log(f"Done: {len(built)} CVs built, {len(results)} total processed")

    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
