#!/usr/bin/env python3
"""
jobs-cv-autogen.py — Auto-generate tailored CVs for SUBMIT jobs after Sonnet verify.

Rules (NON-NEGOTIABLE):
- Max 20 CVs per day (Opus 4.6 budget cap)
- Only SUBMIT jobs with ATS >= 70
- No regeneration if same company+role already has CV from last 7 days
- REVIEW jobs: never auto-generate (SUBMIT only)
- Jobs ranked by sonnet_rank → #1 gets CV first
- If cap hit: fallback link to closest existing CV from cvs/
- Generated CVs pushed to GitHub → URL verified (no 404s) before inclusion

Output: data/jobs-cv-links.json  — {job_id: {cv_url, cv_path, generated, fallback}}
"""

import json
import os
import sys
import re
import time
import hashlib
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
os.environ["PYTHONUNBUFFERED"] = "1"

WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPTS_DIR = WORKSPACE / "scripts"
CVS_DIR = WORKSPACE / "cvs"
DATA_DIR = WORKSPACE / "data"
MEMORY_DIR = WORKSPACE / "memory"

GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"
OPUS_MODEL = "anthropic/claude-opus-4-6"

# Budget rules
MAX_CVS_PER_DAY = 20
ATS_FLOOR = 55
CV_REUSE_WINDOW_DAYS = 7

# GitHub raw URL base
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/ahmednasr999/openclaw-workspace/master/cvs"
GITHUB_BLOB_BASE = "https://github.com/ahmednasr999/openclaw-workspace/blob/master/cvs"

CV_LINKS_FILE = DATA_DIR / "jobs-cv-links.json"
CV_LOG_FILE = DATA_DIR / "cv-autogen-log.jsonl"


def load_gateway_token() -> str:
    try:
        with open("/root/.openclaw/openclaw.json") as f:
            cfg = json.load(f)
        return cfg.get("gateway", {}).get("auth", {}).get("token", "")
    except Exception:
        return ""


def call_opus(prompt: str, timeout: int = 300) -> str | None:
    token = load_gateway_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {
        "model": OPUS_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 8000,
    }
    try:
        resp = requests.post(GATEWAY_URL, json=payload, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            print(f"  Opus error {resp.status_code}: {resp.text[:200]}")
            return None
        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"  Opus call failed: {e}")
        return None


def load_master_cv() -> str:
    master_path = MEMORY_DIR / "master-cv-data.md"
    if master_path.exists():
        return master_path.read_text()
    return ""


def load_ats_rules() -> str:
    ats_path = MEMORY_DIR / "ats-best-practices.md"
    if ats_path.exists():
        return ats_path.read_text()[:3000]  # Top 3k chars sufficient
    return ""


def cv_filename(title: str, company: str) -> str:
    """Generate ATS-safe filename."""
    title_clean = re.sub(r'[^\w\s-]', '', title).strip()[:40]
    company_clean = re.sub(r'[^\w\s-]', '', company).strip()[:25]
    return f"Ahmed Nasr - {title_clean} - {company_clean}.pdf"


def job_fingerprint(job: dict) -> str:
    key = f"{job.get('company','').lower().strip()}|{job.get('title','').lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def find_existing_cv(title: str, company: str) -> Path | None:
    """Check if a recent CV already exists for this role."""
    CVS_DIR.mkdir(exist_ok=True)
    filename = cv_filename(title, company)
    exact = CVS_DIR / filename
    if exact.exists():
        age = time.time() - exact.stat().st_mtime
        if age < CV_REUSE_WINDOW_DAYS * 86400:
            return exact

    # Fuzzy match — same company, similar title
    company_lower = company.lower()
    title_words = set(title.lower().split())
    best = None
    best_score = 0
    for f in CVS_DIR.glob("*.pdf"):
        fname = f.name.lower()
        if company_lower[:8] in fname:
            age = time.time() - f.stat().st_mtime
            if age < CV_REUSE_WINDOW_DAYS * 86400:
                overlap = sum(1 for w in title_words if w in fname)
                if overlap > best_score:
                    best_score = overlap
                    best = f
    if best and best_score >= 2:
        return best
    return None


def find_closest_cv(title: str) -> Path | None:
    """Fallback: find closest existing CV by title keywords."""
    title_words = set(title.lower().split())
    best, best_score = None, 0
    for f in CVS_DIR.glob("*.pdf"):
        overlap = sum(1 for w in title_words if w in f.name.lower())
        if overlap > best_score:
            best_score = overlap
            best = f
    return best if best_score >= 1 else None


def generate_cv_html(job: dict, master_cv: str, ats_rules: str) -> str | None:
    """Call Opus to generate tailored CV HTML."""
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    jd = job.get("jd_text", "") or job.get("raw_snippet", "") or job.get("snippet", "")
    ats_score = job.get("ats_score", 0)
    sonnet_reason = job.get("sonnet_reason", "") or job.get("verdict_reason", "")

    prompt = f"""You are an expert executive CV writer. Create a tailored, ATS-optimized CV for Ahmed Nasr.

TARGET ROLE: {title} at {company}, {location}
ATS SCORE: {ats_score}/100
WHY THIS ROLE: {sonnet_reason}

JOB DESCRIPTION:
{jd[:3000]}

AHMED'S MASTER CV DATA:
{master_cv}

ATS RULES (FOLLOW STRICTLY):
{ats_rules}

REQUIREMENTS:
1. Single-column HTML with inline CSS only
2. Mirror exact keywords from JD (not synonyms)
3. Every bullet: Action Verb + Value + Result/Metric

4. PROFESSIONAL SUMMARY (CRITICAL - THIS IS THE MOST IMPORTANT SECTION):
   - This summary MUST be unique and specific to THIS role at {company}.
   - FIRST SENTENCE: Open with the exact job title "{title}" and what {company} needs most based on the JD. Do NOT open with "Senior Operations Executive" or any generic phrase.
   - Example structure: "[Title] with X years [specific domain from JD]..." or "Executive [domain] leader with proven [specific JD requirement]..."
   - SECOND SENTENCE: Most relevant quantified achievement that directly maps to the top requirement in THIS JD.
   - THIRD SENTENCE: Reference {company} industry/context if known, or the specific challenge mentioned in the JD.
   - Length: 3-4 lines. Every word must earn its place.
   - NEVER reuse the same summary opening across different CVs.

5. CORE COMPETENCIES: Reorder to lead with skills most emphasized in THIS JD. Include exact JD phrases.
6. EXPERIENCE BULLETS: Reorder bullets within each role to lead with the most relevant achievement for THIS position. Do not just copy all bullets in the same order every time.
7. NO tables, NO multi-column body, NO graphics, NO icons
8. Font: Arial/Helvetica, 10-11pt body, 13pt name
9. Margins: 0.75in equivalent padding
10. Sections: Professional Summary, Core Competencies, Professional Experience, Education, Certifications
11. Target: 1.5-2 pages when rendered as PDF

SELF-CHECK BEFORE OUTPUT: Read back your Professional Summary first line. If it could apply to any other job, rewrite it until it cannot.

OUTPUT: Complete HTML document only. No explanation. No markdown wrapper. Start with <!DOCTYPE html>"""

    return call_opus(prompt)


def html_to_pdf(html_content: str, pdf_path: Path) -> bool:
    """Convert HTML to PDF via WeasyPrint."""
    html_tmp = pdf_path.with_suffix(".html")
    try:
        html_tmp.write_text(html_content, encoding="utf-8")
        result = subprocess.run(
            ["weasyprint", str(html_tmp), str(pdf_path)],
            capture_output=True, text=True, timeout=60
        )
        html_tmp.unlink(missing_ok=True)
        if result.returncode != 0:
            print(f"  WeasyPrint error: {result.stderr[:200]}")
            return False
        size = pdf_path.stat().st_size
        if size < 5000:
            print(f"  PDF too small ({size}b) — likely empty")
            return False
        if size > 200000:
            print(f"  PDF too large ({size}b) — check for embedded images")
        print(f"  PDF generated: {pdf_path.name} ({size//1024}KB)")
        return True
    except Exception as e:
        print(f"  PDF generation failed: {e}")
        html_tmp.unlink(missing_ok=True)
        return False


def push_to_github(pdf_path: Path) -> str | None:
    """Git add + commit + push CV. Return GitHub blob URL or None."""
    try:
        subprocess.run(["git", "add", str(pdf_path)], cwd=str(WORKSPACE),
                       capture_output=True, check=True)
        commit_msg = f"cv: {pdf_path.stem}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(WORKSPACE),
                       capture_output=True, check=True)
        subprocess.run(["git", "push", "origin", "master"], cwd=str(WORKSPACE),
                       capture_output=True, timeout=30, check=True)

        encoded = requests.utils.quote(pdf_path.name)
        url = f"{GITHUB_BLOB_BASE}/{encoded}"
        print(f"  Pushed to GitHub: {url}")
        return url
    except subprocess.CalledProcessError as e:
        print(f"  Git push failed: {e}")
        return None


def verify_github_url(url: str, retries: int = 3) -> bool:
    """Verify GitHub URL is accessible (not 404). Retries for propagation delay."""
    for attempt in range(retries):
        try:
            # Use raw URL for verification (faster than blob)
            raw_url = url.replace(
                "github.com/ahmednasr999/openclaw-workspace/blob/master",
                "raw.githubusercontent.com/ahmednasr999/openclaw-workspace/master"
            )
            r = requests.head(raw_url, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                return True
            print(f"  URL check attempt {attempt+1}: status {r.status_code}")
            time.sleep(5)  # Wait for GitHub propagation
        except Exception as e:
            print(f"  URL verify error: {e}")
            time.sleep(3)
    return False


def log_cv_generation(job: dict, cv_path: str, cv_url: str, generated: bool, fallback: bool):
    """Append to cv-autogen-log.jsonl."""
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "job_id": job.get("id", ""),
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "ats_score": job.get("ats_score", 0),
        "cv_path": cv_path,
        "cv_url": cv_url,
        "generated": generated,
        "fallback": fallback,
    }
    CV_LOG_FILE.parent.mkdir(exist_ok=True)
    with open(CV_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def count_today_generations() -> int:
    """Count CVs generated today (not reused/fallback)."""
    today = datetime.now().strftime("%Y-%m-%d")
    count = 0
    if not CV_LOG_FILE.exists():
        return 0
    with open(CV_LOG_FILE) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("date") == today and entry.get("generated"):
                    count += 1
            except Exception:
                pass
    return count


def process_job(job: dict, rank: int, today_count: int, dry_run: bool = False) -> dict:
    """Process one job. Returns cv_link record."""
    title = job.get("title", "Unknown Role")
    company = job.get("company", "Unknown")
    ats = job.get("ats_score", 0)
    job_id = job.get("id", f"job_{rank}")

    print(f"\n  #{rank} {title} @ {company} (ATS:{ats})")

    result = {
        "job_id": job_id,
        "rank": rank,
        "title": title,
        "company": company,
        "ats_score": ats,
        "cv_url": None,
        "cv_path": None,
        "generated": False,
        "fallback": False,
        "reused": False,
        "skipped": False,
        "skip_reason": "",
    }

    # ATS floor check
    if ats < ATS_FLOOR:
        result["skipped"] = True
        result["skip_reason"] = f"ATS {ats} < floor {ATS_FLOOR}"
        print(f"  SKIP: ATS {ats} below floor {ATS_FLOOR}")
        return result

    # Check for existing CV
    existing = find_existing_cv(title, company)
    if existing:
        encoded = requests.utils.quote(existing.name)
        url = f"{GITHUB_BLOB_BASE}/{encoded}"
        result.update({
            "cv_url": url,
            "cv_path": str(existing),
            "reused": True,
        })
        print(f"  REUSE: {existing.name}")
        return result

    # Budget check
    if today_count >= MAX_CVS_PER_DAY:
        # Fallback to closest existing CV
        closest = find_closest_cv(title)
        if closest:
            encoded = requests.utils.quote(closest.name)
            url = f"{GITHUB_BLOB_BASE}/{encoded}"
            result.update({
                "cv_url": url,
                "cv_path": str(closest),
                "fallback": True,
                "skip_reason": f"Daily cap {MAX_CVS_PER_DAY} reached — closest match used",
            })
            print(f"  FALLBACK (cap): {closest.name}")
        else:
            result["skipped"] = True
            result["skip_reason"] = f"Daily cap reached, no fallback found"
            print(f"  SKIP: cap reached, no fallback")
        return result

    if dry_run:
        print(f"  DRY RUN: Would generate CV for #{rank} {title} @ {company}")
        result["skipped"] = True
        result["skip_reason"] = "dry_run"
        return result

    # Generate CV via Opus
    print(f"  Generating with Opus 4.6... (budget: {today_count}/{MAX_CVS_PER_DAY})")
    master_cv = load_master_cv()
    ats_rules = load_ats_rules()

    html_content = generate_cv_html(job, master_cv, ats_rules)
    if not html_content or len(html_content) < 500:
        print(f"  ERROR: Opus returned empty/short response")
        result["skipped"] = True
        result["skip_reason"] = "Opus generation failed"
        return result

    # Strip markdown code fences that Opus sometimes wraps around HTML
    html_content = html_content.strip()
    if html_content.startswith("```"):
        # Remove opening fence (e.g. ```html or just ```)
        first_newline = html_content.find("\n")
        if first_newline != -1:
            html_content = html_content[first_newline + 1:]
    if html_content.endswith("```"):
        html_content = html_content[:html_content.rfind("```")].rstrip()
    html_content = html_content.strip()

    # Ensure HTML starts correctly
    if "<!DOCTYPE" not in html_content[:50]:
        idx = html_content.find("<!DOCTYPE")
        if idx > 0:
            html_content = html_content[idx:]
        else:
            print(f"  ERROR: No valid HTML in Opus response")
            result["skipped"] = True
            result["skip_reason"] = "Invalid HTML from Opus"
            return result

    # Generate PDF
    pdf_filename = cv_filename(title, company)
    pdf_path = CVS_DIR / pdf_filename
    CVS_DIR.mkdir(exist_ok=True)

    if not html_to_pdf(html_content, pdf_path):
        result["skipped"] = True
        result["skip_reason"] = "PDF generation failed"
        return result

    # Push to GitHub
    cv_url = push_to_github(pdf_path)
    if not cv_url:
        # Still usable locally, just no GitHub URL
        result.update({
            "cv_path": str(pdf_path),
            "generated": True,
            "skip_reason": "GitHub push failed — CV local only",
        })
        print(f"  WARNING: CV generated but not pushed to GitHub")
        log_cv_generation(job, str(pdf_path), "", True, False)
        return result

    # Verify URL is live
    print(f"  Verifying GitHub URL...", end=" ", flush=True)
    if verify_github_url(cv_url):
        print("✅ live")
    else:
        print("⚠️ not yet accessible — including anyway (propagation delay)")

    result.update({
        "cv_url": cv_url,
        "cv_path": str(pdf_path),
        "generated": True,
    })
    log_cv_generation(job, str(pdf_path), cv_url, True, False)
    return result


def main():
    dry_run = "--dry-run" in sys.argv
    summary_file = DATA_DIR / "jobs-summary.json"

    if not summary_file.exists():
        print("ERROR: jobs-summary.json not found — run pipeline first")
        sys.exit(1)

    with open(summary_file) as f:
        summary = json.load(f)

    data = summary.get("data", summary)
    submit_jobs = data.get("submit", [])

    if not submit_jobs:
        print("No SUBMIT jobs — nothing to generate CVs for")
        with open(CV_LINKS_FILE, "w") as f:
            json.dump({}, f)
        return

    # Sort by sonnet_rank, then ats_score
    submit_sorted = sorted(
        submit_jobs,
        key=lambda x: (x.get("sonnet_rank") or 99, -(x.get("ats_score") or 0))
    )

    # Filter by ATS floor
    eligible = [j for j in submit_sorted if j.get("ats_score", 0) >= ATS_FLOOR]
    ineligible = [j for j in submit_sorted if j.get("ats_score", 0) < ATS_FLOOR]

    today_count = count_today_generations()
    print(f"\njobs-cv-autogen")
    print(f"SUBMIT jobs: {len(submit_jobs)} total | {len(eligible)} eligible (ATS≥{ATS_FLOOR}) | {len(ineligible)} below floor")
    print(f"Opus budget: {today_count}/{MAX_CVS_PER_DAY} used today")
    if dry_run:
        print("[DRY RUN]")

    cv_links = {}

    for rank, job in enumerate(eligible, 1):
        result = process_job(job, rank, today_count, dry_run=dry_run)
        job_id = job.get("id", f"rank_{rank}")
        cv_links[job_id] = result
        if result.get("generated"):
            today_count += 1
        # Brief pause between Opus calls
        if not dry_run and not result.get("skipped") and not result.get("reused"):
            time.sleep(2)

    # Mark ineligible jobs (ATS too low)
    for job in ineligible:
        job_id = job.get("id", "")
        cv_links[job_id] = {
            "job_id": job_id,
            "title": job.get("title"),
            "company": job.get("company"),
            "ats_score": job.get("ats_score", 0),
            "cv_url": None,
            "skipped": True,
            "skip_reason": f"ATS {job.get('ats_score',0)} < floor {ATS_FLOOR}",
        }

    # Save links file
    with open(CV_LINKS_FILE, "w") as f:
        json.dump(cv_links, f, indent=2)

    # Summary
    generated = sum(1 for v in cv_links.values() if v.get("generated"))
    reused = sum(1 for v in cv_links.values() if v.get("reused"))
    fallback = sum(1 for v in cv_links.values() if v.get("fallback"))
    skipped = sum(1 for v in cv_links.values() if v.get("skipped"))

    print(f"\n{'='*50}")
    print(f"CV Autogen Summary:")
    print(f"  Generated (Opus): {generated}")
    print(f"  Reused existing:  {reused}")
    print(f"  Fallback (cap):   {fallback}")
    print(f"  Skipped:          {skipped}")
    print(f"  Total budget used today: {today_count}/{MAX_CVS_PER_DAY}")
    print(f"  Output: {CV_LINKS_FILE}")


if __name__ == "__main__":
    main()
