#!/usr/bin/env python3
"""
push-to-nocodb.py — Push merged+enriched jobs to NocoDB and send Telegram status alerts.

Reads: data/jobs-merged.json (after enrich step fills jd_text)
       data/jobs-summary.json (after review step scores jobs)
Writes: NocoDB Jobs table (insert new, update scored)

Sends Telegram alerts after each phase:
  - Source scrape results (reads pipeline-phase-status.json)
  - NocoDB push summary (new/dupes/updated)
  - Top SUBMIT jobs with scores

Run: python3 scripts/push-to-nocodb.py [--dry-run]
Cron: Wired as Phase 3 in run-briefing-pipeline.sh (after review, before telegram)
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
CONFIG_DIR = WORKSPACE / "config"
NOCODB_CONFIG = CONFIG_DIR / "nocodb.json"
MERGED_FILE = DATA_DIR / "jobs-merged.json"
SUMMARY_FILE = DATA_DIR / "jobs-summary.json"
PHASE_STATUS_FILE = DATA_DIR / "pipeline-phase-status.json"

# Telegram config
TG_GROUP = "-1003882622947"
TG_TOPIC_CEO = "10"  # CEO General
TG_TOPIC_HR = "9"    # HR Desk

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, str(WORKSPACE / "scripts"))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

import requests


def load_nocodb_auth():
    """Load NocoDB config and authenticate."""
    cfg = json.loads(NOCODB_CONFIG.read_text())
    resp = requests.post(
        f"{cfg['url']}/api/v1/auth/user/signin",
        json={"email": cfg["email"], "password": cfg["password"]},
        timeout=10
    )
    resp.raise_for_status()
    token = resp.json()["token"]
    return {
        "url": cfg["url"],
        "table_id": cfg["table_id"],
        "headers": {"xc-auth": token, "Content-Type": "application/json"},
    }


def get_existing_urls(noco):
    """Get all existing URLs from NocoDB to dedup."""
    table_url = f"{noco['url']}/api/v2/tables/{noco['table_id']}/records"
    existing = set()
    offset = 0
    while True:
        r = requests.get(
            f"{table_url}?fields=Id,URL&limit=200&offset={offset}",
            headers=noco["headers"], timeout=15
        ).json()
        for row in r.get("list", []):
            if row.get("URL"):
                existing.add(row["URL"])
        if len(r.get("list", [])) < 200:
            break
        offset += 200
    return existing


def send_telegram(message, topic=None):
    """Send message to Telegram via openclaw CLI."""
    target = TG_GROUP
    if topic:
        target = f"{TG_GROUP}:{topic}"
    try:
        subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--to", target, "--message", message],
            capture_output=True, timeout=15
        )
    except Exception as e:
        print(f"  Telegram send failed: {e}")


def format_source_status():
    """Read pipeline phase status and format source scrape results."""
    if not PHASE_STATUS_FILE.exists():
        return None

    try:
        status = json.loads(PHASE_STATUS_FILE.read_text())
        phases = status.get("phases", {})
    except Exception:
        return None

    # Read raw source files for counts
    sources = {}
    for name, fname in [("LinkedIn", "linkedin.json"), ("Indeed", "indeed.json"), ("Google", "google-jobs.json")]:
        path = DATA_DIR / "jobs-raw" / fname
        if path.exists():
            try:
                data = json.loads(path.read_text())
                jobs = data.get("data", data) if isinstance(data, dict) else data
                ts = data.get("generated_at", "") if isinstance(data, dict) else ""
                sources[name] = {"count": len(jobs) if isinstance(jobs, list) else 0, "ts": ts}
            except Exception:
                sources[name] = {"count": 0, "ts": "error"}
        else:
            sources[name] = {"count": 0, "ts": "missing"}

    # Read merged count
    merged_count = 0
    if MERGED_FILE.exists():
        try:
            merged = json.loads(MERGED_FILE.read_text())
            jobs = merged.get("data", merged) if isinstance(merged, dict) else merged
            merged_count = len(jobs) if isinstance(jobs, list) else 0
        except Exception:
            pass

    lines = ["📡 Job Source Scrape Complete\n"]
    total_raw = 0
    for name, info in sources.items():
        status_icon = "✅" if info["count"] > 0 else "❌"
        lines.append(f"{status_icon} {name}: {info['count']} jobs")
        total_raw += info["count"]

    lines.append(f"\n📊 Raw: {total_raw} - After dedup & filters: {merged_count}")

    return "\n".join(lines)


def push_new_jobs(noco, dry_run=False):
    """Push new merged jobs to NocoDB. Returns stats dict."""
    if not MERGED_FILE.exists():
        return {"new": 0, "dupes": 0, "errors": 0, "total_merged": 0}

    merged = json.loads(MERGED_FILE.read_text())
    jobs = merged.get("data", merged) if isinstance(merged, dict) else merged
    if not isinstance(jobs, list):
        return {"new": 0, "dupes": 0, "errors": 0, "total_merged": 0}

    existing_urls = get_existing_urls(noco)
    table_url = f"{noco['url']}/api/v2/tables/{noco['table_id']}/records"

    # Source capitalization map
    source_cap = {"linkedin": "LinkedIn", "indeed": "Indeed", "google": "Google"}

    new_jobs = []
    dupes = 0
    for j in jobs:
        url = j.get("url", "")
        if url in existing_urls:
            dupes += 1
            continue
        new_jobs.append(j)

    if dry_run:
        return {"new": len(new_jobs), "dupes": dupes, "errors": 0, "total_merged": len(jobs)}

    created = 0
    errors = 0

    for i in range(0, len(new_jobs), 10):
        batch = []
        for j in new_jobs[i:i + 10]:
            row = {
                "Title": (j.get("title", "") or "Unknown")[:200],
                "Company": (j.get("company", "") or "Unknown")[:200],
                "Location": (j.get("location", "") or "")[:200],
                "URL": j.get("url", ""),
                "Source": source_cap.get(j.get("source", ""), j.get("source", "Other")),
                "Status": "New",
                "Keyword Score": j.get("keyword_score", 0),
                "Matched Keywords": (j.get("match_keywords", "") or "")[:500],
                "Seniority": (j.get("seniority", "") or "")[:50],
                "Domain Match": bool(j.get("domain_match")),
            }

            # JD from enrich step
            if j.get("jd_text") and len(j["jd_text"]) > 100:
                row["Full Description"] = j["jd_text"][:50000]

            # Raw snippet as fallback
            if j.get("raw_snippet") and not row.get("Full Description"):
                row["Raw Snippet"] = j["raw_snippet"][:2000]

            # Date
            posted = j.get("posted") or j.get("first_seen", "")[:10]
            if posted and len(posted) >= 10:
                row["Posted"] = posted[:10]

            batch.append(row)

        try:
            resp = requests.post(table_url, json=batch, headers=noco["headers"], timeout=30)
            if resp.status_code == 200:
                created += len(batch)
            else:
                errors += len(batch)
        except Exception:
            errors += len(batch)

    return {"new": created, "dupes": dupes, "errors": errors, "total_merged": len(jobs)}


def update_scored_jobs(noco, dry_run=False):
    """Update NocoDB rows with review scores (Verdict, ATS, Fit, AI Reasoning)."""
    if not SUMMARY_FILE.exists():
        return {"updated": 0, "submit": 0, "review": 0}

    summary = json.loads(SUMMARY_FILE.read_text())
    submit_jobs = summary.get("data", {}).get("submit", [])
    review_jobs = summary.get("data", {}).get("review", [])

    # Build score map by URL
    score_map = {}
    for j in submit_jobs:
        if j.get("url"):
            score_map[j["url"]] = {
                "Verdict": "SUBMIT",
                "ATS Score": j.get("ats_score", 0),
                "Fit Score": j.get("career_fit_score", 0),
                "AI Reasoning": (j.get("verdict_reason", "") or "")[:5000],
                "Status": "Interested",
            }
            if j.get("jd_text") and len(j["jd_text"]) > 100:
                score_map[j["url"]]["Full Description"] = j["jd_text"][:50000]

    for j in review_jobs:
        if j.get("url"):
            score_map[j["url"]] = {
                "Verdict": "REVIEW",
                "ATS Score": j.get("ats_score", 0),
                "Fit Score": j.get("career_fit_score", 0),
                "AI Reasoning": (j.get("verdict_reason", "") or "")[:5000],
            }
            if j.get("jd_text") and len(j["jd_text"]) > 100:
                score_map[j["url"]]["Full Description"] = j["jd_text"][:50000]

    if not score_map:
        return {"updated": 0, "submit": len(submit_jobs), "review": len(review_jobs)}

    if dry_run:
        return {"updated": len(score_map), "submit": len(submit_jobs), "review": len(review_jobs)}

    # Get NocoDB rows by URL
    table_url = f"{noco['url']}/api/v2/tables/{noco['table_id']}/records"
    url_to_id = {}
    offset = 0
    while True:
        r = requests.get(
            f"{table_url}?fields=Id,URL&limit=200&offset={offset}",
            headers=noco["headers"], timeout=15
        ).json()
        for row in r.get("list", []):
            if row.get("URL"):
                url_to_id[row["URL"]] = row["Id"]
        if len(r.get("list", [])) < 200:
            break
        offset += 200

    # Build update batches
    updates = []
    for url, scores in score_map.items():
        row_id = url_to_id.get(url)
        if row_id:
            patch = {"Id": row_id}
            patch.update(scores)
            updates.append(patch)

    updated = 0
    for i in range(0, len(updates), 10):
        batch = updates[i:i + 10]
        try:
            resp = requests.patch(table_url, json=batch, headers=noco["headers"], timeout=30)
            if resp.status_code == 200:
                updated += len(batch)
        except Exception:
            pass

    return {"updated": updated, "submit": len(submit_jobs), "review": len(review_jobs)}


def format_push_summary(push_stats, score_stats):
    """Format NocoDB push summary for Telegram."""
    lines = ["📋 NocoDB Pipeline Update\n"]

    # Push stats
    lines.append(f"🆕 New jobs added: {push_stats['new']}")
    lines.append(f"🔄 Already existed: {push_stats['dupes']}")
    if push_stats["errors"]:
        lines.append(f"❌ Errors: {push_stats['errors']}")
    lines.append(f"📊 Total merged: {push_stats['total_merged']}")

    # Score stats
    if score_stats["submit"] or score_stats["review"]:
        lines.append(f"\n🎯 AI Review: {score_stats['submit']} SUBMIT / {score_stats['review']} REVIEW")
        lines.append(f"✅ Scores synced: {score_stats['updated']}")

    return "\n".join(lines)


def format_top_jobs():
    """Format top SUBMIT jobs for Telegram alert."""
    if not SUMMARY_FILE.exists():
        return None

    summary = json.loads(SUMMARY_FILE.read_text())
    submit_jobs = summary.get("data", {}).get("submit", [])

    if not submit_jobs:
        return None

    # Sort by ATS desc
    submit_jobs.sort(key=lambda j: j.get("ats_score", 0), reverse=True)

    lines = [f"🎯 Top {min(len(submit_jobs), 10)} SUBMIT Jobs\n"]
    for i, j in enumerate(submit_jobs[:10], 1):
        fit = j.get("career_fit_score", 0)
        ats = j.get("ats_score", 0)
        title = j.get("title", "?")[:50]
        company = j.get("company", "?")[:30]
        location = j.get("location", "")[:20]
        url = j.get("url", "")

        lines.append(f"#{i} [Fit:{fit} ATS:{ats}] {title}")
        lines.append(f"   {company} ({location})")
        if url:
            lines.append(f"   {url}")
        lines.append("")

    lines.append(f"📊 View all: http://100.99.230.14:8080 - Kanban Pipeline view")

    return "\n".join(lines)


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN MODE - no writes")

    print("=" * 60)
    print(f"push-to-nocodb.py — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Phase 1: Source status alert
    print("\n--- Phase 1: Source Status ---")
    source_msg = format_source_status()
    if source_msg:
        print(source_msg)
        if not dry_run:
            send_telegram(source_msg, topic=TG_TOPIC_HR)
    else:
        print("  No phase status file found, skipping source alert")

    # Phase 2: NocoDB auth
    print("\n--- Phase 2: NocoDB Push ---")
    try:
        noco = load_nocodb_auth()
        print(f"  NocoDB connected: {noco['url']}")
    except Exception as e:
        print(f"  ERROR: NocoDB auth failed: {e}")
        if not dry_run:
            send_telegram(f"❌ NocoDB Push FAILED: Auth error - {e}", topic=TG_TOPIC_CEO)
        sys.exit(1)

    # Phase 3: Push new jobs
    push_stats = push_new_jobs(noco, dry_run=dry_run)
    print(f"  New: {push_stats['new']}, Dupes: {push_stats['dupes']}, Errors: {push_stats['errors']}")

    # Phase 4: Update scored jobs
    print("\n--- Phase 3: Score Sync ---")
    score_stats = update_scored_jobs(noco, dry_run=dry_run)
    print(f"  Updated: {score_stats['updated']}, SUBMIT: {score_stats['submit']}, REVIEW: {score_stats['review']}")

    # Phase 5: Send summary to Telegram
    print("\n--- Phase 4: Telegram Alerts ---")
    push_msg = format_push_summary(push_stats, score_stats)
    print(push_msg)
    if not dry_run:
        send_telegram(push_msg, topic=TG_TOPIC_HR)

    # Phase 6: Top jobs alert
    top_msg = format_top_jobs()
    if top_msg:
        print(top_msg)
        if not dry_run:
            send_telegram(top_msg, topic=TG_TOPIC_HR)

    print("\n✅ Done")


if __name__ == "__main__":
    main()
