#!/usr/bin/env python3
"""
pam-telegram.py — Sends morning briefing summary to Telegram.
Reads FRESH pipeline data files directly (not stale newsletter).
Runs AFTER briefing-agent.py so it can include the Notion URL.

Output format (agreed 2026-03-28):
  - 🟢 SUBMIT section with per-job lines (ATS%, 🆕 flag, URL, CV link)
  - 🟡 REVIEW count
  - Pipeline snapshot, email, calendar
  - Budget rules block
  - Notion link

Usage:
  python3 pam-telegram.py              # Send full digest
  python3 pam-telegram.py --dry-run    # Preview without sending
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
CHAT_ID = "-1003882622947:10"
CAIRO = timezone(timedelta(hours=2))

# Budget rules (mirrored from jobs-cv-autogen.py)
MAX_CVS_PER_DAY = 20
ATS_FLOOR = 55
CV_REUSE_DAYS = 7


def load_json(path, default=None):
    try:
        return json.load(open(path))
    except Exception:
        return default if default is not None else {}


def build_message():
    today = datetime.now(CAIRO)
    today_iso = today.strftime("%Y-%m-%d")
    short_date = today.strftime("%a %b %d")

    # Load data
    jobs_raw = load_json(DATA_DIR / "jobs-summary.json")
    jobs_data = jobs_raw.get("data", {})
    kpi = jobs_data.get("kpi", jobs_raw.get("kpi", {}))
    email_raw = load_json(DATA_DIR / "email-summary.json")
    email_data = email_raw.get("data", email_raw)
    system_raw = load_json(DATA_DIR / "system-health.json")
    sys_data = system_raw.get("data", {})

    # Calendar
    cal_path = Path(f"/tmp/calendar-events-{today_iso}.json")
    cal_events = []
    if cal_path.exists():
        try:
            raw = json.load(open(cal_path))
            cal_events = raw if isinstance(raw, list) else raw.get("events", raw.get("data", []))
        except Exception:
            pass

    # CV links (from jobs-cv-autogen.py)
    cv_links = load_json(DATA_DIR / "jobs-cv-links.json", {})

    # Pipeline DB
    try:
        sys.path.insert(0, str(WORKSPACE / "scripts"))
        import pipeline_db as _pdb
        db_funnel = _pdb.get_funnel()
        db_total = db_funnel.get("_total", 0)
        db_applied = db_funnel.get("applied", 0)
        db_interview = db_funnel.get("interview", 0)
    except Exception:
        db_total = db_applied = db_interview = 0

    # ── JOBS ──────────────────────────────────────────────────────────────────
    submit_jobs = jobs_data.get("submit", [])
    review_jobs = jobs_data.get("review", [])

    # Split by freshness
    fresh_submit = [j for j in submit_jobs if j.get("first_seen") == today_iso]
    old_submit = [j for j in submit_jobs if j.get("first_seen") != today_iso]

    # Sort each group by ATS score desc
    fresh_submit.sort(key=lambda x: x.get("ats_score", 0), reverse=True)
    old_submit.sort(key=lambda x: x.get("ats_score", 0), reverse=True)
    ordered_submit = fresh_submit + old_submit

    # Critical alert
    cats = email_data.get("categories", email_data.get("by_category", {}))
    interviews_cat = cats.get("interview_invite", 0)
    n_int = len(interviews_cat) if isinstance(interviews_cat, list) else (interviews_cat or 0)

    lines = []
    lines.append(f"☀️ AM Brief - {short_date}")

    # Urgent
    if n_int > 0:
        lines.append(f"🔴 {n_int} INTERVIEW INVITE(S) - check email NOW")

    lines.append("")

    # ── SUBMIT block ──────────────────────────────────────────────────────────
    lines.append(f"🟢 SUBMIT ({len(submit_jobs)} jobs)")

    if fresh_submit:
        lines.append(f"🆕 {len(fresh_submit)} fresh:")

    shown = 0
    for idx, j in enumerate(ordered_submit, 1):  # Show ALL submit jobs
        title = j.get("title", "?")[:35]
        company = j.get("company", "?")[:20]
        location = j.get("location", "")
        ats = j.get("ats_score", 0)
        url = j.get("url", "")
        is_new = j.get("first_seen") == today_iso
        reason = (j.get("verdict_reason") or j.get("sonnet_reason") or "")[:70]

        # Location short form
        loc_short = ""
        if location:
            for city in ["Dubai", "Abu Dhabi", "Riyadh", "Jeddah", "Doha", "Muscat", "Cairo"]:
                if city.lower() in location.lower():
                    loc_short = f" | {city}"
                    break
            if not loc_short and location:
                loc_short = f" | {location[:15]}"

        # CV link
        job_id = j.get("id", "")
        cv_entry = cv_links.get(job_id, {}) if cv_links else {}
        cv_url = cv_entry.get("cv_url") or cv_entry.get("github_url") or ""

        new_flag = "🆕 " if is_new else "📌 "
        lines.append(f"\n#{idx} {new_flag}ATS:{ats}% | {title} @ {company}{loc_short}")
        if reason:
            lines.append(f"   └ {reason}")
        if url:
            lines.append(f"   → 🔗 Apply: {url}")
        if cv_url:
            lines.append(f"   → 📄 CV: {cv_url}")
        shown += 1

    # Remaining not shown
    remaining = len(submit_jobs) - shown
    if remaining > 0:
        lines.append(f"\n📌 {remaining} more - see Notion")

    lines.append("")

    # ── REVIEW block ──────────────────────────────────────────────────────────
    fresh_review = [j for j in review_jobs if j.get("first_seen") == today_iso]
    lines.append(f"🟡 REVIEW ({len(review_jobs)} jobs | {len(fresh_review)} fresh)")

    lines.append("")

    # ── PIPELINE SNAPSHOT ─────────────────────────────────────────────────────
    if db_total > 0:
        lines.append(f"📊 Pipeline: {db_total} total | {db_applied} applied | {db_interview} interviews")
    else:
        total_cands = jobs_data.get("total_candidates", "?")
        reviewed = jobs_data.get("reviewed", "?")
        lines.append(f"🔍 Scanned: {total_cands} | Reviewed: {reviewed}")

    # ── EMAIL ─────────────────────────────────────────────────────────────────
    scanned = email_data.get("total_scanned", email_data.get("scanned_count", 0))
    recruiters_cat = cats.get("recruiter_reach", 0)
    n_rec = len(recruiters_cat) if isinstance(recruiters_cat, list) else (recruiters_cat or 0)
    email_parts = []
    if n_int:
        email_parts.append(f"{n_int} interview")
    if n_rec:
        email_parts.append(f"{n_rec} recruiter")
    email_note = f" ({', '.join(email_parts)})" if email_parts else ""
    lines.append(f"📧 Email: {scanned} scanned{email_note}")

    # ── CALENDAR ──────────────────────────────────────────────────────────────
    if cal_events:
        lines.append(f"📅 {len(cal_events)} events today")
        for ev in cal_events[:3]:
            title = ev.get("title", ev.get("summary", "?"))[:35]
            start = ev.get("start", "")
            t = start.split("T")[-1][:5] if "T" in str(start) else ""
            lines.append(f"   {t} {title}".strip())
    else:
        lines.append("📅 No events today")

    lines.append("")

    # ── BUDGET RULES ──────────────────────────────────────────────────────────
    cv_gen_today = _count_cv_gens_today()
    lines.append("💰 Budget rules locked:")
    lines.append(f"   Max {MAX_CVS_PER_DAY} Opus CVs/day ({cv_gen_today} used today)")
    lines.append(f"   ATS >= {ATS_FLOOR} only | same role {CV_REUSE_DAYS}d reuse")
    lines.append("   404-verified before inclusion")

    lines.append("")

    # ── NOTION LINK ──────────────────────────────────────────────────────────
    notion_url = find_briefing_url(today_iso)
    if notion_url:
        lines.append(f"📋 Full briefing: {notion_url}")
    else:
        lines.append("📋 Full briefing: check Notion")

    return "\n".join(lines)


def _count_cv_gens_today():
    """Count CVs generated today (not reused/fallback)."""
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    log_file = DATA_DIR / "cv-autogen-log.jsonl"
    if not log_file.exists():
        return 0
    count = 0
    with open(log_file) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("date") == today and entry.get("generated"):
                    count += 1
            except Exception:
                pass
    return count


def find_briefing_url(today_iso):
    """Query Notion for today's briefing page URL."""
    import urllib.request, ssl
    try:
        token = load_json(WORKSPACE / "config/notion.json").get("token", "")
        if not token:
            return ""
        db_id = "3268d599-a162-812d-a59e-e5496dec80e7"
        payload = json.dumps({
            "filter": {"property": "Name", "title": {"contains": today_iso}},
            "page_size": 1
        }).encode()
        req = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            results = json.loads(resp.read()).get("results", [])
            if results:
                return results[0].get("url", "")
    except Exception:
        pass
    return ""


def send_via_openclaw(text):
    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "-t", CHAT_ID, "--message", text],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return True, "sent"
        else:
            return False, result.stderr[:200]
    except Exception as e:
        return False, str(e)[:200]


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    text = build_message()

    print("=" * 60)
    print("TELEGRAM BRIEFING SUMMARY")
    print("=" * 60)
    print(text)
    print("=" * 60)
    print(f"Length: {len(text)} chars")

    if dry_run:
        print("\n[DRY RUN - not sent]")
    else:
        ok, msg = send_via_openclaw(text)
        if ok:
            print(f"\n✅ Sent to Telegram via OpenClaw")
        else:
            print(f"\n❌ Failed: {msg}")
