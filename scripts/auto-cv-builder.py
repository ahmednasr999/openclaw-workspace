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

WORKSPACE   = "/root/.openclaw/workspace"
HANDOFF_DIR = f"{WORKSPACE}/jobs-bank/handoff"
CVS_DIR     = f"{WORKSPACE}/cvs"
MASTER_CV   = f"{WORKSPACE}/memory/master-cv-data.md"
PENDING_CV  = f"{WORKSPACE}/memory/cv-pending-updates.md"
OPENCLAW_JSON = "/root/.openclaw/openclaw.json"

ANTHROPIC_API_KEY = ""
ANTHROPIC_BASE_URL = "https://api.anthropic.com"

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
    global ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL
    try:
        with open(OPENCLAW_JSON) as f:
            cfg = json.load(f)
        p = cfg.get("models", {}).get("providers", {}).get("anthropic", {})
        ANTHROPIC_API_KEY = p.get("apiKey", "")
        ANTHROPIC_BASE_URL = p.get("baseUrl", "https://api.anthropic.com")
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
    """Call Opus 4.6 via Anthropic API."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("No Anthropic API key")

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


def generate_pdf(html_body, company, role):
    """Generate PDF from HTML body via WeasyPrint."""
    safe_role = re.sub(r'[^\w\s-]', '', role).strip()[:50]
    safe_company = re.sub(r'[^\w\s-]', '', company).strip()[:30]
    filename = f"Ahmed Nasr - {safe_role} - {safe_company}"

    html_path = f"{CVS_DIR}/{filename}.html"
    pdf_path = f"{CVS_DIR}/{filename}.pdf"

    full_html = HTML_TEMPLATE.format(
        role_title=f"{safe_role} - {safe_company}",
        body_html=html_body
    )

    os.makedirs(CVS_DIR, exist_ok=True)

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

    if dry_run:
        log(f"  DRY RUN: Would tailor CV for {role} @ {company}")
        return {"company": company, "role": role, "status": "dry_run", "ats_estimate": ats}

    # Tailor CV via Opus 4.6
    try:
        html_body = tailor_cv(master_cv, pending_updates, data)
        log(f"  CV body: {len(html_body)} chars")
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
        "github_link": github_link
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

                if job_id and cv_path:
                    _pdb.attach_cv(job_id=job_id, cv_path=cv_path, cv_html_path=html_path or None)
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
