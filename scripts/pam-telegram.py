#!/usr/bin/env python3
"""
pam-telegram.py — Sends morning briefing summary to Telegram.
Reads FRESH pipeline data files directly (not stale newsletter).
Runs AFTER briefing-agent.py so it can include the Notion URL.

Usage:
  python3 pam-telegram.py              # Send full digest
  python3 pam-telegram.py --dry-run    # Preview without sending
"""

import os
import sys
import json, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
CHAT_ID = "-1003882622947:10"  # Briefings thread (was 866838380 DM)
CAIRO = timezone(timedelta(hours=2))


def load_json(path, default=None):
    try:
        return json.load(open(path))
    except Exception:
        return default or {}


def build_message():
    """Build Telegram summary from fresh pipeline data."""
    today = datetime.now(CAIRO)
    date_str = today.strftime("%A, %B %d %Y")
    today_iso = today.strftime("%Y-%m-%d")

    # Load fresh data
    system = load_json(DATA_DIR / "system-health.json")
    jobs = load_json(DATA_DIR / "jobs-summary.json")
    email = load_json(DATA_DIR / "email-summary.json")
    content = load_json(DATA_DIR / "content-schedule.json")
    radar = load_json(DATA_DIR / "comment-radar.json")
    outreach = load_json(DATA_DIR / "outreach-summary.json")

    # Calendar
    cal_path = Path(f"/tmp/calendar-events-{today_iso}.json")
    cal_events = []
    if cal_path.exists():
        try:
            raw = json.load(open(cal_path))
            cal_events = raw if isinstance(raw, list) else raw.get("events", raw.get("data", []))
        except Exception:
            pass

    parts = []
    parts.append(f"Good Morning, {date_str}")
    parts.append("")

    # ── CALLOUT (critical items first) ──
    critical = []
    email_data = email.get("data", {})
    cats = email_data.get("categories", email_data.get("by_category", {}))
    interviews = cats.get("interview_invite", 0)
    recruiters = cats.get("recruiter_reach", 0)
    if interviews and (isinstance(interviews, int) and interviews > 0 or isinstance(interviews, list) and len(interviews) > 0):
        n_int = interviews if isinstance(interviews, int) else len(interviews)
        critical.append(f"INTERVIEW: {n_int} invite(s) - check email NOW")
    sys_data = system.get("data", {})
    infra = sys_data.get("system", {})
    gw = sys_data.get("gateway", sys_data.get("system", {}).get("gateway", {}))
    if isinstance(gw, dict) and gw.get("status") == "down":
        critical.append("Gateway DOWN")
    if critical:
        parts.append("🔴 " + " | ".join(critical))
        parts.append("")

    # ── CALENDAR ──
    if cal_events:
        parts.append(f"📅 Calendar ({len(cal_events)})")
        for ev in cal_events[:4]:
            title = ev.get("title", ev.get("summary", "?"))[:40]
            start = ev.get("start", "")
            is_all_day = ev.get("is_all_day", "T" not in str(start))
            if is_all_day:
                parts.append(f"  🗓 {title} (all day)")
            else:
                t = start.split("T")[-1][:5] if "T" in start else start
                parts.append(f"  🕐 {t} {title}")
        parts.append("")

    # ── JOBS ──
    jobs_data = jobs.get("data", {})
    kpi = jobs_data.get("kpi", jobs.get("kpi", {}))
    submit_count = kpi.get("submit_count", len(jobs_data.get("submit", [])))
    review_count = kpi.get("review_count", len(jobs_data.get("review", [])))
    reviewed = jobs_data.get("reviewed", "?")
    total = jobs_data.get("total_candidates", "?")
    parts.append(f"💼 Jobs: {total} scanned, {reviewed} reviewed -> {submit_count} SUBMIT | {review_count} REVIEW")

    # Top SUBMIT picks (up to 3)
    for j in jobs_data.get("submit", [])[:3]:
        score = j.get("career_fit_score", "?")
        title = j.get("title", "?")[:30]
        company = j.get("company", "?")[:20]
        parts.append(f"  #{submit_count}. [{score}/10] {title} @ {company}")

    # If no SUBMIT, show top REVIEW
    if not jobs_data.get("submit") and jobs_data.get("review"):
        parts.append("  No SUBMIT - top REVIEW:")
        for j in jobs_data.get("review", [])[:2]:
            score = j.get("career_fit_score", "?")
            title = j.get("title", "?")[:30]
            company = j.get("company", "?")[:20]
            parts.append(f"  [{score}/10] {title} @ {company}")
    parts.append("")

    # ── PIPELINE DB SUMMARY (sourced from SQLite) ────────────────────────────
    if _pdb:
        try:
            db_funnel = _pdb.get_funnel()
            db_stale = _pdb.get_stale(days=7)
            db_total = db_funnel.get("_total", 0)
            db_applied = db_funnel.get("applied", 0)
            db_interview = db_funnel.get("interview", 0)
            if db_total > 0:
                parts.append(
                    f"🗄 Pipeline DB: {db_total} total | {db_applied} applied | "
                    f"{db_interview} interview | {len(db_stale)} stale"
                )
                parts.append("")
        except Exception:
            pass  # DB read failed, silent skip
    # ─────────────────────────────────────────────────────────────────────────

    # ── EMAIL ──
    n_int = len(interviews) if isinstance(interviews, list) else interviews
    n_rec = len(recruiters) if isinstance(recruiters, list) else recruiters
    scanned = email_data.get("total_scanned", email_data.get("scanned_count", 0))
    if n_int or n_rec:
        parts.append(f"📧 Email: {scanned} scanned | {n_int} interview | {n_rec} recruiter")
    else:
        parts.append(f"📧 Email: {scanned} scanned, no urgent items")
    parts.append("")

    # ── LINKEDIN ──
    li_post = load_json(DATA_DIR / "linkedin-post.json")
    if li_post.get("has_post"):
        topic = li_post.get("post", {}).get("topic", li_post.get("topic", "?"))[:50]
        parts.append(f"✍️ LinkedIn: Today - {topic}")
    elif li_post.get("next_scheduled"):
        ns = li_post.get("next_scheduled", {})
        parts.append(f"✍️ LinkedIn: Scheduled - {ns.get('title', '?')[:50]}")
    else:
        parts.append("✍️ LinkedIn: No post today")

    # Comment radar
    cr_posts = radar.get("top_posts", radar.get("data", {}).get("top_posts", []))
    drafted = sum(1 for p in cr_posts if p.get("draft_comment"))
    if drafted:
        parts.append(f"💬 Comment Radar: {drafted} drafts ready")
    parts.append("")

    # ── OUTREACH ──
    out_data = outreach.get("data", {})
    suggestions = out_data.get("suggestions", [])
    if suggestions:
        parts.append(f"🤝 Outreach: {len(suggestions)} new suggestions")
    parts.append("")

    # ── SYSTEM ──
    disk = infra.get("disk_usage_pct", "?")
    ram = infra.get("memory", {}).get("used_pct", "?")
    agents = sys_data.get("agents", {})
    healthy = agents.get("healthy_count", "?")
    total_a = agents.get("total", "?")
    parts.append(f"📊 System: Disk {disk}% | RAM {ram}% | Agents {healthy}/{total_a}")

    # ── BRIEFING LINK ──
    parts.append("")
    parts.append("─────────────────")

    # Find today's briefing URL
    briefing_url = find_briefing_url(today_iso)
    if briefing_url:
        parts.append(f"📋 Full briefing: {briefing_url}")
    else:
        parts.append("📋 Full briefing: check Notion")

    return "\n".join(parts)


def find_briefing_url(today_iso):
    """Query Notion for today's briefing page URL."""
    import urllib.request
    token = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
    db_id = "3268d599-a162-812d-a59e-e5496dec80e7"
    try:
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
        import ssl
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            results = json.loads(resp.read()).get("results", [])
            if results:
                return results[0].get("url", "")
    except Exception:
        pass
    return ""


def send_via_openclaw(text):
    """Send via openclaw message send — replies trigger NASR agent."""
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

    print("=" * 50)
    print("TELEGRAM BRIEFING SUMMARY")
    print("=" * 50)
    print(text)
    print("=" * 50)
    print(f"Length: {len(text)} chars")

    if dry_run:
        print("\n[DRY RUN - not sent]")
    else:
        ok, msg = send_via_openclaw(text)
        if ok:
            print(f"\n✅ Sent to Telegram via OpenClaw")
        else:
            print(f"\n❌ Failed: {msg}")
