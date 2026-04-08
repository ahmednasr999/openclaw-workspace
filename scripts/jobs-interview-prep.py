#!/usr/bin/env python3
"""
jobs-interview-prep.py — Auto-generate interview prep kit when a job status flips to Interview.

Triggered by: morning-briefing-orchestrator.py or manually.

What it generates (Opus 4.6):
  1. Company dossier (2-3 key facts, recent news, culture signals)
  2. Role intelligence (what they really want vs what's written)
  3. 5 likely interview questions with Ahmed's best answer angles
  4. 5 questions Ahmed should ask them
  5. Ahmed's top 3 achievement stories mapped to this role
  6. Red flags / watch-outs

Output: docs/interview-prep/{company}-{title}.md + pushed to GitHub
Telegram: summary + link sent to CMO Desk thread (topic_id=7)
"""

import sys
import os
import json
import re
import requests
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
PREP_DIR = WORKSPACE / "docs" / "interview-prep"
MEMORY_DIR = WORKSPACE / "memory"
DATA_DIR = WORKSPACE / "data"
NOTION_CFG = WORKSPACE / "config" / "notion.json"

PIPELINE_DB_ID = "3268d599-a162-81b4-b768-f162adfa4971"
NOTION_VERSION = "2022-06-28"

GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"
OPUS_MODEL = "anthropic/claude-opus-4-6"

TELEGRAM_CHAT_ID = "-1003882622947"
TELEGRAM_TOPIC_ID = "10"

GITHUB_BLOB_BASE = "https://github.com/ahmednasr999/openclaw-workspace/blob/master/docs/interview-prep"


def load_notion_token() -> str:
    with open(NOTION_CFG) as f:
        return json.load(f)["token"]


def load_gateway_token() -> str:
    try:
        with open("/root/.openclaw/openclaw.json") as f:
            cfg = json.load(f)
        return cfg.get("gateway", {}).get("auth", {}).get("token", "")
    except Exception:
        return ""


def notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def call_opus(prompt: str, timeout: int = 180) -> str | None:
    token = load_gateway_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {
        "model": OPUS_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 2000,
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


def load_profile_summary() -> str:
    path = MEMORY_DIR / "master-cv-data.md"
    if path.exists():
        return path.read_text()[:3000]
    return ""


def get_interview_jobs(notion_token: str) -> list[dict]:
    """Get all jobs with Status=Interview from Notion."""
    url = f"https://api.notion.com/v1/databases/{PIPELINE_DB_ID}/query"
    payload = {
        "filter": {"property": "Status", "select": {"equals": "Interview"}},
        "page_size": 20,
    }
    resp = requests.post(url, json=payload, headers=notion_headers(notion_token), timeout=30)
    if resp.status_code != 200:
        print(f"Notion error: {resp.status_code}")
        return []

    results = []
    for page in resp.json().get("results", []):
        props = page.get("properties", {})
        def get_text(k):
            v = props.get(k, {})
            if v.get("type") == "title":
                return "".join(r.get("plain_text", "") for r in v.get("title", []))
            if v.get("type") == "rich_text":
                return "".join(r.get("plain_text", "") for r in v.get("rich_text", []))
            return ""
        def get_url(k):
            return (props.get(k) or {}).get("url", "") or ""
        def get_date(k):
            d = (props.get(k) or {}).get("date")
            return d.get("start", "") if d else ""

        results.append({
            "id": page["id"],
            "title": get_text("Name") or get_text("Title") or get_text("Role"),
            "company": get_text("Company"),
            "url": get_url("URL") or get_url("Job URL"),
            "interview_date": get_date("Interview Date") or get_date("Next Step Date"),
        })
    return results


def generate_prep_kit(company: str, title: str, jd_text: str, profile: str) -> str | None:
    prompt = f"""Generate a focused interview prep kit for Ahmed Nasr.

COMPANY: {company}
ROLE: {title}
JD HIGHLIGHTS: {jd_text[:2000] if jd_text else "Not available"}

AHMED'S PROFILE (condensed):
{profile}

Generate EXACTLY this structure (markdown format):

## 🏢 Company Intel
3 bullet points: what they actually care about, culture signals, recent news/initiatives. Be specific.

## 🎯 Role Intelligence
2 bullet points: what the job ad says vs what they actually need. What pain are they hiring to solve?

## ❓ Likely Interview Questions (Top 5)
For each: question + Ahmed's 2-sentence answer angle using his real experience.

## 💬 Questions Ahmed Should Ask (Top 5)
Sharp executive questions that signal seniority. Not generic. Specific to this company/role.

## 🏆 Ahmed's 3 Best Stories for This Role
Map 3 of Ahmed's strongest achievements to this JD. Format: Situation → Action → Result (1 sentence each).

## ⚠️ Watch-Outs
2-3 potential gaps or red flags Ahmed should be ready to address. With deflection strategy.

Keep it sharp. No fluff. This is for a C-suite/VP level candidate."""

    return call_opus(prompt)


def prep_filename(title: str, company: str) -> str:
    title_clean = re.sub(r'[^\w\s-]', '', title).strip()[:35]
    company_clean = re.sub(r'[^\w\s-]', '', company).strip()[:20]
    return f"{company_clean} - {title_clean}.md"


def push_to_github(file_path: Path) -> str | None:
    try:
        subprocess.run(["git", "add", str(file_path)], cwd=str(WORKSPACE),
                       capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", f"prep: {file_path.stem}"],
                       cwd=str(WORKSPACE), capture_output=True, check=True)
        subprocess.run(["git", "push", "origin", "master"], cwd=str(WORKSPACE),
                       capture_output=True, timeout=30, check=True)
        encoded = requests.utils.quote(file_path.name)
        return f"{GITHUB_BLOB_BASE}/{encoded}"
    except subprocess.CalledProcessError as e:
        print(f"  Git push failed: {e}")
        return None


def send_telegram(company: str, title: str, interview_date: str, kit_url: str):
    try:
        token = load_gateway_token()
        if not token:
            return
        date_str = f" on {interview_date}" if interview_date else ""
        msg = (f"🎯 Interview Prep Kit Ready\n\n"
               f"**{title}** @ {company}{date_str}\n\n"
               f"→ 📋 Prep Kit: {kit_url or 'see docs/interview-prep/'}\n\n"
               f"Kit includes: company intel, role analysis, 5 likely Qs + answer angles, 5 Qs to ask them, "
               f"3 mapped achievement stories, watch-outs.")
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "message_thread_id": TELEGRAM_TOPIC_ID,
            "text": msg,
        }
        requests.post(
            "http://127.0.0.1:18789/v1/telegram/send",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except Exception as e:
        print(f"  Telegram send failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Generate interview prep kit")
    parser.add_argument("--company", help="Specific company (skip Notion query)")
    parser.add_argument("--title", help="Job title")
    parser.add_argument("--jd", help="Path to JD text file or JD as string")
    parser.add_argument("--interview-date", help="Interview date (YYYY-MM-DD)")
    parser.add_argument("--all-interviews", action="store_true",
                        help="Generate for all Interview-status jobs in Notion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    PREP_DIR.mkdir(parents=True, exist_ok=True)
    profile = load_profile_summary()
    notion_token = load_notion_token()

    if args.all_interviews:
        jobs = get_interview_jobs(notion_token)
        if not jobs:
            print("No jobs with Interview status in Notion")
            return
        print(f"Found {len(jobs)} interview-status job(s)")
    elif args.company:
        jobs = [{
            "title": args.title or "Unknown Role",
            "company": args.company,
            "url": "",
            "interview_date": args.interview_date or "",
            "id": "",
        }]
    else:
        # Default: run for all Interview jobs
        jobs = get_interview_jobs(notion_token)
        if not jobs:
            print("No interview-status jobs found. Use --company to specify one.")
            return

    for job in jobs:
        company = job["company"]
        title = job["title"]
        interview_date = job.get("interview_date", "")

        print(f"\nPreparing: {title} @ {company}")
        if interview_date:
            print(f"  Interview: {interview_date}")

        filename = prep_filename(title, company)
        prep_path = PREP_DIR / filename

        # Skip if recent (< 3 days old)
        if prep_path.exists():
            import time
            age_days = (time.time() - prep_path.stat().st_mtime) / 86400
            if age_days < 3:
                print(f"  SKIP: Prep kit already exists ({age_days:.1f} days old)")
                continue

        # Load JD if provided
        jd_text = ""
        if args.jd:
            if os.path.exists(args.jd):
                jd_text = Path(args.jd).read_text()[:3000]
            else:
                jd_text = args.jd[:3000]

        if args.dry_run:
            print(f"  [DRY RUN] Would generate prep kit → {filename}")
            continue

        kit = generate_prep_kit(company, title, jd_text, profile)
        if not kit or len(kit) < 200:
            print(f"  ERROR: Empty/short kit from Opus")
            continue

        header = f"# Interview Prep: {title} @ {company}\n\n_Generated {datetime.now().strftime('%Y-%m-%d')}_"
        if interview_date:
            header += f" | Interview: {interview_date}"
        header += "\n\n---\n\n"

        prep_path.write_text(header + kit, encoding="utf-8")
        print(f"  Saved: {filename} ({len(kit)} chars)")

        kit_url = push_to_github(prep_path)
        send_telegram(company, title, interview_date, kit_url or "")
        print(f"  URL: {kit_url}")


if __name__ == "__main__":
    main()
