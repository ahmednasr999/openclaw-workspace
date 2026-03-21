#!/usr/bin/env python3
"""
Pam Newsletter Agent - Formats daily briefing data into a polished morning digest.
Inspired by Shubham Saboo's "Pam turns the daily intel into a newsletter" agent.

Reads all agent outputs from data/ and produces a clean, readable digest.
Output: data/pam-newsletter.json + optionally prints formatted text.

Usage:
  python3 pam-newsletter-agent.py              # Generate digest
  python3 pam-newsletter-agent.py --format txt  # Plain text output
  python3 pam-newsletter-agent.py --dry-run     # Preview without saving
"""

import json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
OUTPUT = DATA_DIR / "pam-newsletter.json"
TZ_OFFSET = 2  # Cairo = UTC+2

def load_json(path, default=None):
    try:
        return json.load(open(path))
    except:
        return default or {}

def ts_local(iso_ts):
    """Convert UTC ISO timestamp to Cairo time."""
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        dt = dt + timedelta(hours=TZ_OFFSET)
        return dt.strftime("%-I:%M %p")  # 7:00 AM format
    except:
        return "?"

def section(title, content):
    """Add a section if content is non-empty."""
    if content and content.strip():
        return f"\n{'='*50}\n{title}\n{'='*50}\n{content}\n"

def bullet(items, max_items=None):
    """Format a list as bullet points."""
    if not items:
        return "  (none)"
    if max_items:
        items = items[:max_items]
    return "\n".join(f"  - {i}" for i in items)

def generate_digest():
    """Read all agent outputs and generate newsletter."""

    # Load all data sources
    email = load_json(DATA_DIR / "email-summary.json", {})
    linkedin_post = load_json(DATA_DIR / "linkedin-post.json", {})
    comment_radar = load_json(DATA_DIR / "comment-radar.json", {})
    outreach = load_json(DATA_DIR / "outreach-summary.json", {})
    system = load_json(DATA_DIR / "system-health.json", {})
    jobs = load_json(DATA_DIR / "jobs-summary.json", {})
    github = load_json(DATA_DIR / "github-discovery.json", {})
    engagement = load_json(DATA_DIR / "linkedin-engagement.json", {})
    autoresearch = load_json(DATA_DIR / "linkedin-autoresearch" / "latest.json", {})

    now = datetime.now(timezone(timedelta(hours=TZ_OFFSET)))
    date_str = now.strftime("%A, %B %d %Y")

    # ── System Health ──────────────────────────────────────
    sys_status = []
    sys_data = system.get("data", {})
    sys_kpi = system.get("kpi", {})
    if sys_data.get("system"):
        s = sys_data["system"]
        sys_status.append(f"Disk: {s.get('disk_usage_pct','?')}% | RAM: {s.get('memory',{}).get('used_pct','?')}% | Uptime: {sys_kpi.get('system_uptime','?')}%")
    if sys_kpi.get("alerts_active"):
        sys_status.append(f"ALERTS: {sys_kpi['alerts_active']} active")
    if sys_kpi.get("agents_healthy") is not None:
        sys_status.append(f"Agents healthy: {sys_kpi['agents_healthy']}")
    sys_text = "\n".join(sys_status) if sys_status else "All systems nominal"

    # ── Email ─────────────────────────────────────────────
    email_data = email.get("data", {})
    by_cat = email_data.get("by_category", {})
    email_items = []
    for cat, count in by_cat.items():
        if count and isinstance(count, int) and count > 0:
            email_items.append(f"{cat.title()}: {count} unread")
    email_text = bullet(email_items) if email_items else "No unread emails"

    # ── LinkedIn Post ────────────────────────────────────
    lp = linkedin_post
    if lp.get("has_post"):
        topic = lp.get("post", {}).get("topic", lp.get("topic", "?"))
        hook = lp.get("hook", lp.get("post", {}).get("hook", "?"))[:100]
        status = lp.get("status", "?")
        post_text = f"Today's topic: {topic}\nHook: {hook}...\nStatus: {status}"
    elif lp.get("next_scheduled"):
        ns = lp.get("next_scheduled", {})
        post_text = f"Next scheduled: {ns.get('title', ns.get('topic', '?'))}\nDate: {ns.get('date', '?')}"
    else:
        post_text = "No post scheduled"

    # Engagement snapshot
    eng_text = "No engagement data"
    if engagement:
        posts = engagement.get("posts", [])
        if posts:
            total_eng = sum(p.get("engagement", 0) for p in posts)
            eng_text = f"{len(posts)} posts tracked, {total_eng} total engagement"
        else:
            eng_text = f"Collected: {engagement.get('collected_at', '?')[:16]}"

    # ── Comment Radar ─────────────────────────────────────
    cr = comment_radar
    cr_posts = cr.get("top_posts", [])
    if cr_posts:
        top = cr_posts[0]
        top_score = top.get("pqs", "?")
        top_author = top.get("author", "?")[:30]
        top_topic = top.get("title", top.get("topic", "?"))[:70]
        comment_text = f"Top post (PQS {top_score}): {top_author}\n  {top_topic}..."
        if len(cr_posts) > 1:
            comment_text += f"\n  +{len(cr_posts)-1} more posts queued"
    else:
        comment_text = "No posts flagged for engagement today"

    # ── Outreach ───────────────────────────────────────────
    out_data = outreach.get("data", {}).get("today", {})
    out_kpi = outreach.get("kpi", {})
    out_today = out_data.get("sent", 0)
    out_target = out_data.get("target", 0)
    out_resp = out_kpi.get("response_rate", 0)
    out_overdue = out_kpi.get("overdue_count", 0)
    outreach_text = f"Sent today: {out_today}/{out_target} | Response rate: {out_resp:.0f}%"
    if out_overdue > 0:
        outreach_text += f"\n  WARNING: {out_overdue} overdue follow-ups"
    outreach_text += f"\nQueue depth: {out_kpi.get('queue_depth', 0)}"

    # ── Jobs ─────────────────────────────────────────────
    job_data = jobs.get("data", {})
    submit_data = job_data.get("submit", {})
    review_data = job_data.get("review", {})
    total = job_data.get("total_candidates", "?")
    reviewed = job_data.get("reviewed", "?")
    submit_count = len(submit_data) if isinstance(submit_data, list) else submit_data
    review_count = len(review_data) if isinstance(review_data, list) else review_data
    jobs_text = f"Total merged: {total} | Reviewed: {reviewed} | Submit: {submit_count} | Review: {review_count}"
    if isinstance(submit_data, list) and submit_data:
        top_job = submit_data[0]
        title = top_job.get("title", top_job.get("company", "?"))
        company = top_job.get("company", top_job.get("title", "?"))
        score = top_job.get("fit_score", top_job.get("score", "?"))
        jobs_text += f"\nTop pick: {title} at {company} ({score}/10)"

    # ── GitHub Radar ───────────────────────────────────────
    gh_data = github.get("top_relevant", github.get("top_global", []))
    if isinstance(gh_data, list) and gh_data:
        gh_repos = gh_data[:3]
        gh_text = "\n".join(f"  {r.get('name',r.get('repo',r))[:50]} ({r.get('stars',r.get('star_count','?'))}) - {r.get('description','')[:60]}" for r in gh_repos)
    else:
        gh_text = "No relevant repos found today"

    # ── Autoresearch Insights ──────────────────────────────
    ar_text = "No recent analysis"
    if autoresearch:
        latest = autoresearch.get("generated", "")[:16] if isinstance(autoresearch, dict) else ""
        if latest:
            ar_text = f"Last analysis: {latest}"
        insights = autoresearch.get("insights", [])
        if insights:
            ar_text = "\n".join(f"  - {i[:80]}" for i in insights[:3])

    # ── Compile newsletter ─────────────────────────────────
    sections = {
        "date": date_str,
        "generated_at": datetime.now(timezone(timedelta(hours=TZ_OFFSET))).isoformat(),
        "system": sys_text,
        "email": email_text,
        "linkedin_post": post_text,
        "comment_radar": comment_text,
        "outreach": outreach_text,
        "jobs": jobs_text,
        "github": gh_text,
        "autoresearch": ar_text,
    }

    # ── Format as readable text ─────────────────────────────
    lines = []
    lines.append(f"\n{'#'*60}")
    lines.append(f"  GOOD MORNING — {date_str}")
    lines.append(f"{'#'*60}")

    lines.append(f"\n{'='*60}")
    lines.append(f"  SYSTEM STATUS")
    lines.append(f"{'='*60}")
    lines.append(f"  {sys_text}")

    lines.append(f"\n{'='*60}")
    lines.append(f"  EMAIL")
    lines.append(f"{'='*60}")
    lines.append(f"  {email_text}")

    lines.append(f"\n{'='*60}")
    lines.append(f"  LINKEDIN")
    lines.append(f"{'='*60}")
    lines.append(f"  {post_text}")
    lines.append(f"  Engagement: {eng_text}")

    lines.append(f"\n{'='*60}")
    lines.append(f"  COMMENT RADAR")
    lines.append(f"{'='*60}")
    lines.append(f"  {comment_text}")

    lines.append(f"\n{'='*60}")
    lines.append(f"  OUTREACH")
    lines.append(f"{'='*60}")
    lines.append(f"  {outreach_text}")

    lines.append(f"\n{'='*60}")
    lines.append(f"  JOBS")
    lines.append(f"{'='*60}")
    lines.append(f"  {jobs_text}")

    lines.append(f"\n{'='*60}")
    lines.append(f"  GITHUB RADAR")
    lines.append(f"{'='*60}")
    lines.append(gh_text)

    lines.append(f"\n{'='*60}")
    lines.append(f"  CONTENT INTELLIGENCE")
    lines.append(f"{'='*60}")
    lines.append(f"  {ar_text}")

    lines.append(f"\n{'*'*60}")
    lines.append(f"  Pam Newsletter | {datetime.now(timezone(timedelta(hours=TZ_OFFSET))).strftime('%I:%M %p Cairo')}")
    lines.append(f"{'*'*60}\n")

    return sections, "\n".join(lines)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    txt_mode = "--format" in sys.argv and "txt" in sys.argv

    sections, text = generate_digest()

    if dry_run or txt_mode:
        print(text)
    else:
        output_data = {
            "generated": datetime.now(timezone(timedelta(hours=TZ_OFFSET))).isoformat(),
            "version": "1.0.0",
            **sections,
        }
        json.dump(output_data, open(OUTPUT, "w"), indent=2)
        print(f"Newsletter saved: {OUTPUT}")
        print(f"\nPreview:\n{text}")
