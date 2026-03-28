#!/usr/bin/env python3
"""
jobs-coverletter-autogen.py — Auto-generate targeted cover letters for SUBMIT jobs.

Rules:
- Only runs for jobs that have a CV generated (from jobs-cv-links.json)
- Max 20/day (shared with CV budget awareness — separate counter but same spirit)
- Output: plain text .txt + markdown .md per job
- Pushed to GitHub alongside CV
- Format: 3 paragraphs, email-ready, under 250 words
- Tone: executive, direct, no fluff
"""

import json
import os
import sys
import re
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
COVERS_DIR = WORKSPACE / "covers"
MEMORY_DIR = WORKSPACE / "memory"

GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"
OPUS_MODEL = "anthropic/claude-opus-4-6"

MAX_COVERS_PER_DAY = 20
COVER_LOG_FILE = DATA_DIR / "coverletter-autogen-log.jsonl"
COVER_LINKS_FILE = DATA_DIR / "jobs-cover-links.json"

GITHUB_BLOB_BASE = "https://github.com/ahmednasr999/openclaw-workspace/blob/master/covers"


def load_gateway_token() -> str:
    try:
        with open("/root/.openclaw/openclaw.json") as f:
            cfg = json.load(f)
        return cfg.get("gateway", {}).get("auth", {}).get("token", "")
    except Exception:
        return ""


def call_opus(prompt: str, timeout: int = 180) -> str | None:
    token = load_gateway_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {
        "model": OPUS_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 600,
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


def load_master_cv_summary() -> str:
    """Load condensed profile — not full CV, just key facts for cover letter."""
    path = MEMORY_DIR / "master-cv-data.md"
    if not path.exists():
        return ""
    text = path.read_text()
    # Extract just summary + competencies (first ~1500 chars is enough for cover letter)
    return text[:2000]


def cover_filename(title: str, company: str) -> str:
    title_clean = re.sub(r'[^\w\s-]', '', title).strip()[:40]
    company_clean = re.sub(r'[^\w\s-]', '', company).strip()[:25]
    return f"Ahmed Nasr - Cover - {title_clean} - {company_clean}.md"


def generate_cover_letter(job: dict, profile_summary: str) -> str | None:
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    jd = job.get("jd_text", "") or job.get("raw_snippet", "") or job.get("snippet", "")
    sonnet_reason = job.get("sonnet_reason", "") or job.get("verdict_reason", "")

    prompt = f"""Write a concise, executive-level cover letter for Ahmed Nasr applying to:

ROLE: {title}
COMPANY: {company}
LOCATION: {location}
WHY THIS ROLE FITS: {sonnet_reason}

JOB DESCRIPTION (key points):
{jd[:2000]}

AHMED'S PROFILE:
{profile_summary}

REQUIREMENTS:
- Exactly 3 paragraphs, under 250 words total
- Paragraph 1: Why this specific role at this specific company (reference 1 company fact)
- Paragraph 2: Strongest 2 matching achievements with metrics from Ahmed's experience
- Paragraph 3: Clear ask + availability for conversation
- Tone: senior executive — confident, direct, no fluff, no "I am excited to apply"
- No salutation/sign-off needed (email body only)
- Mirror 2-3 exact keywords from the JD

Output the 3 paragraphs only. No explanation."""

    return call_opus(prompt)


def push_to_github(file_path: Path) -> str | None:
    try:
        subprocess.run(["git", "add", str(file_path)], cwd=str(WORKSPACE),
                       capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", f"cover: {file_path.stem}"],
                       cwd=str(WORKSPACE), capture_output=True, check=True)
        subprocess.run(["git", "push", "origin", "master"], cwd=str(WORKSPACE),
                       capture_output=True, timeout=30, check=True)
        encoded = requests.utils.quote(file_path.name)
        return f"{GITHUB_BLOB_BASE}/{encoded}"
    except subprocess.CalledProcessError as e:
        print(f"  Git push failed: {e}")
        return None


def count_today_covers() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    count = 0
    if not COVER_LOG_FILE.exists():
        return 0
    with open(COVER_LOG_FILE) as f:
        for line in f:
            try:
                e = json.loads(line)
                if e.get("date") == today:
                    count += 1
            except Exception:
                pass
    return count


def main():
    dry_run = "--dry-run" in sys.argv
    COVERS_DIR.mkdir(exist_ok=True)

    # Load CV links to know which jobs have CVs
    cv_links_file = DATA_DIR / "jobs-cv-links.json"
    if not cv_links_file.exists():
        print("No cv-links file found — run jobs-cv-autogen.py first")
        with open(COVER_LINKS_FILE, "w") as f:
            json.dump({}, f)
        return

    with open(cv_links_file) as f:
        cv_links = json.load(f)

    # Load jobs summary
    summary_file = DATA_DIR / "jobs-summary.json"
    if not summary_file.exists():
        print("No jobs-summary.json found")
        return

    with open(summary_file) as f:
        summary = json.load(f)

    data = summary.get("data", summary)
    submit_jobs = data.get("submit", [])

    # Only process jobs that have a CV (generated or reused — not fallback/skipped)
    jobs_with_cv = []
    for job in submit_jobs:
        job_id = job.get("id", "")
        cv_info = cv_links.get(job_id, {})
        if cv_info.get("cv_url") and not cv_info.get("fallback") and not cv_info.get("skipped"):
            jobs_with_cv.append(job)

    profile_summary = load_master_cv_summary()
    today_count = count_today_covers()
    cover_links = {}

    print(f"\njobs-coverletter-autogen")
    print(f"Jobs with CV: {len(jobs_with_cv)} | Cover budget: {today_count}/{MAX_COVERS_PER_DAY}")
    if dry_run:
        print("[DRY RUN]")

    for rank, job in enumerate(jobs_with_cv, 1):
        title = job.get("title", "Unknown")
        company = job.get("company", "Unknown")
        job_id = job.get("id", f"rank_{rank}")

        print(f"\n  #{rank} {title} @ {company}")

        if today_count >= MAX_COVERS_PER_DAY:
            print(f"  SKIP: daily cap {MAX_COVERS_PER_DAY} reached")
            cover_links[job_id] = {"cover_url": None, "skipped": True, "skip_reason": "daily cap"}
            continue

        filename = cover_filename(title, company)
        cover_path = COVERS_DIR / filename

        # Check if already generated recently
        if cover_path.exists():
            age = time.time() - cover_path.stat().st_mtime
            if age < 7 * 86400:
                encoded = requests.utils.quote(filename)
                url = f"{GITHUB_BLOB_BASE}/{encoded}"
                cover_links[job_id] = {"cover_url": url, "reused": True}
                print(f"  REUSE: {filename}")
                continue

        if dry_run:
            print(f"  DRY RUN: Would generate cover letter")
            cover_links[job_id] = {"cover_url": None, "skipped": True, "skip_reason": "dry_run"}
            continue

        letter = generate_cover_letter(job, profile_summary)
        if not letter or len(letter) < 100:
            print(f"  ERROR: Empty/short response from Opus")
            cover_links[job_id] = {"cover_url": None, "skipped": True, "skip_reason": "generation failed"}
            continue

        # Save as markdown
        md_content = f"# Cover Letter — {title} @ {company}\n\n_{datetime.now().strftime('%Y-%m-%d')}_\n\n---\n\n{letter}\n"
        cover_path.write_text(md_content, encoding="utf-8")
        print(f"  Generated: {filename} ({len(letter)} chars)")

        cover_url = push_to_github(cover_path)

        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "job_id": job_id,
            "title": title,
            "company": company,
            "cover_url": cover_url or "",
        }
        with open(COVER_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

        cover_links[job_id] = {"cover_url": cover_url, "generated": True}
        today_count += 1
        time.sleep(2)

    with open(COVER_LINKS_FILE, "w") as f:
        json.dump(cover_links, f, indent=2)

    generated = sum(1 for v in cover_links.values() if v.get("generated"))
    reused = sum(1 for v in cover_links.values() if v.get("reused"))
    print(f"\nDone — {generated} generated | {reused} reused | output: {COVER_LINKS_FILE}")


if __name__ == "__main__":
    main()
