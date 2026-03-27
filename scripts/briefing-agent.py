#!/usr/bin/env python3
"""
Briefing Agent — CEO Edition
============================
Generates Ahmed's morning briefing as a strategic decision document, not a data dump.

Strategic rules:
- First block: EXECUTIVE SUMMARY — 3 bullets, what matters today
- Every section: What changed, what it means, what to do
- System/infra: Only show if broken
- Numbers: Always include context (↑↓ vs yesterday? vs target?)
- Decisions: Frame as yes/no questions, not raw data

Output: Notion page + Telegram summary
"""
import os
import sys
import json, re, requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.header import decode_header

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
BRIEFINGS_DB = "3268d599-a162-812d-a59e-e5496dec80e7"
CAIRO = timezone(timedelta(hours=2))

# Pipeline DB
try:
    sys.path.insert(0, str(WORKSPACE / "scripts"))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

# ── Notion helpers ──────────────────────────────────────────────────────────
def linked_text(text, url):
    return {"text": {"content": str(text)[:2000], "link": {"url": url}}}

def mailto(text, addr):
    return linked_text(text, f"mailto:{addr}")

def plain(text):
    return {"text": {"content": str(text)[:2000]}}

def bold(text):
    return {"text": {"content": str(text)[:2000]}, "annotations": {"bold": True}}

def h2(t): return {"object":"block","type":"heading_2","heading_2":{"rich_text":[plain(t)]}}
def h3(t): return {"object":"block","type":"heading_3","heading_3":{"rich_text":[plain(t)]}}
def bul(*parts): return {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":list(parts)}}
def div(): return {"object":"block","type":"divider","divider":{}}
def callout(t, emoji="🟢"): return {"object":"block","type":"callout","callout":{"rich_text":[plain(t)],"icon":{"emoji":emoji}}}
def quote(t): return {"object":"block","type":"quote","quote":{"rich_text":[plain(t)]}}

# ── Email helpers ───────────────────────────────────────────────────────────
def decode_email_subject(encoded):
    if not encoded:
        return "No subject"
    try:
        parts = decode_header(encoded)
        decoded = ""
        for part, charset in parts:
            if isinstance(part, bytes):
                decoded += part.decode(charset or 'utf-8', errors='replace')
            elif isinstance(part, str):
                decoded += part
        return decoded.strip()
    except Exception:
        return encoded

def extract_email_addr(from_field):
    if not from_field:
        return ""
    match = re.search(r'<([^>]+)>', from_field)
    if match:
        return match.group(1)
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', from_field)
    return match.group(0) if match else ""

# ── Load data ───────────────────────────────────────────────────────────────
def load_data():
    raw = {}
    sources = {
        "pipeline": "pipeline-status.json",
        "email": "email-summary.json",
        "content": "content-schedule.json",
        "outreach": "outreach-summary.json",
        "system": "system-health.json",
        "jobs": "jobs-summary.json",
    }
    for key, path in sources.items():
        full = DATA_DIR / path
        try:
            with open(full) as f:
                raw[key] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raw[key] = {"meta": {"status": "missing/-corrupt"}, "data": {}, "kpi": {}}
    return raw

# ── Strategic briefing builder ─────────────────────────────────────────────
def build_blocks():
    data = load_data()
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    now_str = datetime.now(CAIRO).strftime("%a %b %d, %I:%M %p")

    raw = data["pipeline"]
    pipe = raw.get("data", {})
    funnel = pipe.get("conversion_funnel", {})
    applied = funnel.get("applied", 0)
    total_apps = pipe.get("total_applications", applied)

    raw_sys = data["system"]
    sys_data = raw_sys.get("data", {})
    infra = sys_data.get("infrastructure", {})
    gw = infra.get("gateway_healthy", True)
    agent_health = sys_data.get("agent_health", {})

    raw_email = data["email"]
    email_data = raw_email.get("data", {})
    cats = email_data.get("categories", {})
    interview_count = cats.get("interview_invite", 0)
    if isinstance(interview_count, list):
        interview_count = len(interview_count)
    recruiter_count = cats.get("recruiter_reach", 0)
    if isinstance(recruiter_count, list):
        recruiter_count = len(recruiter_count)

    raw_jobs = data["jobs"]
    jobs_data = raw_jobs.get("data", {})
    submit_jobs = jobs_data.get("submit", [])[:5]  # Cap at 5
    review_jobs = jobs_data.get("review", [])[:5]
    avg_fit = raw_jobs.get("kpi", {}).get("avg_fit_score", None)

    raw_content = data["content"]
    content_data = raw_content.get("data", {})
    health = content_data.get("health", {})
    streak = health.get("posting_streak", 0)
    runway = health.get("days_until_content_runs_out", None)
    post_today = content_data.get("today", {}).get("scheduled_post", None)

    # DB funnel
    db_total = 0
    db_applied = 0
    db_interviews = 0
    db_stale = 0
    if _pdb:
        try:
            db_funnel = _pdb.get_funnel()
            db_total = db_funnel.get("_total", 0)
            db_applied = db_funnel.get("applied", 0)
            db_interviews = db_funnel.get("interview", 0)
            db_stale = len(_pdb.get_stale(days=7))
        except Exception:
            pass

    # Use DB as authoritative if available
    pipeline_total = max(total_apps, db_total)
    pipeline_applied = max(applied, db_applied)
    pipeline_interviews = db_interviews

    blocks = []

    # ── 1. EXECUTIVE SUMMARY ────────────────────────────────────────────────
    blocks.append(h2(f"📋 Morning Briefing — {now_str}"))
    blocks.append(div())

    summary_items = []

    # Interview invites → always first priority
    if interview_count:
        summary_items.append(
            f"🎯 {interview_count} interview invite(s) — open email immediately"
        )

    # Content today
    if post_today:
        summary_items.append(
            f"📣 LinkedIn post ready to go today"
        )
    elif streak > 0:
        summary_items.append(
            f"🔥 Content streak: {streak} days — don't break it (no post queued)"
        )
    else:
        summary_items.append(
            f"📝 No content streak active — queue a post this week"
        )

    # Pipeline health
    if db_stale > 5:
        summary_items.append(
            f"⚠️ {db_stale} applications stalled (7+ days no update) — needs review"
        )
    elif pipeline_applied >= 100:
        summary_items.append(
            f"📊 Pipeline: {pipeline_applied} applied, {pipeline_interviews} interviews"
        )
    elif pipeline_applied > 0:
        summary_items.append(
            f"📊 Pipeline building: {pipeline_applied} applied ({pipeline_interviews} interviews)"
        )

    # Job SUBMIT
    if submit_jobs:
        summary_items.append(
            f"✅ {len(submit_jobs)} job(s) ready to apply today"
        )
    elif review_jobs:
        summary_items.append(
            f"👀 {len(review_jobs)} jobs need your review before applying"
        )

    # System
    if not gw:
        summary_items.append("🚨 Gateway DOWN — AI agents not running")
    elif isinstance(agent_health, dict):
        stale_agents = sum(1 for v in agent_health.values()
                         if isinstance(v, dict) and v.get("stale", False))
        if stale_agents > 3:
            summary_items.append(f"⚠️ {stale_agents} AI agents stalled — check system")

    # Build the summary callout
    if summary_items:
        callout_text = " | ".join(summary_items)
        emoji = "🔴" if interview_count or not gw else ("⚠️" if db_stale > 5 else "🟢")
    else:
        callout_text = "All clear. No urgent items."
        emoji = "🟢"
    blocks.append(callout(callout_text, emoji))

    # ── 1b. CTO REPORT (runs cron dashboard check live) ───────────────────
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(WORKSPACE / "scripts" / "cron-dashboard-updater.py"), "--dry-run"],
            capture_output=True, text=True, timeout=60
        )
        cto_output = result.stdout.strip()
        if cto_output:
            lines = [l for l in cto_output.splitlines() if l.strip()]
            if lines:
                blocks.append(div())
                blocks.append(h2("🛠 CTO Report"))
                for line in lines[:8]:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    llower = line.lower()
                    if any(x in llower for x in ["fail", "red", "error", "down"]):
                        blocks.append(bul(plain(f"🔴 {line}")))
                    elif any(x in llower for x in ["amber", "warn", "stale"]):
                        blocks.append(bul(plain(f"⚠️ {line}")))
                    elif "ok" in llower or "pass" in llower:
                        blocks.append(bul(plain(f"🟢 {line}")))
                    else:
                        blocks.append(bul(plain(line)))
    except Exception:
        pass  # Non-blocking

    # ── 2. DECISIONS NEEDED ────────────────────────────────────────────────
    blocks.append(h2("🎯 Decisions Needed Today"))

    decisions = []

    if interview_count:
        decisions.append("YES — Reply to interview invite(s) today (recruiter patience window is ~24h)")

    if submit_jobs:
        top = submit_jobs[0]
        company = top.get("company", "?")
        title = top.get("title", "?")[:50]
        decisions.append(
            f"YES — Apply to #{company}: {title}? (Fit {top.get('career_fit_score','?')}, ATS {top.get('ats_score','?')})"
        )

    if review_jobs and not submit_jobs:
        decisions.append(
            f"REVIEW — {len(review_jobs)} jobs in REVIEW queue. "
            f"Approve top candidates to move to SUBMIT."
        )

    if not post_today and not content_data.get("today"):
        decisions.append(
            "POST — No LinkedIn post scheduled. Queue one today to maintain streak."
        )

    if db_stale > 5:
        decisions.append(
            f"CLEANUP — {db_stale} stalled applications. Follow up or mark inactive."
        )

    if recruiter_count:
        decisions.append(
            f"REPLY — {recruiter_count} recruiter message(s). Respond within 48h."
        )

    if decisions:
        for d in decisions:
            blocks.append(bul(bold("→ "), plain(d)))
    else:
        blocks.append(callout("Nothing pressing today. Focus on networking and content.", "🟢"))

    # ── 3. TOP JOBS ────────────────────────────────────────────────────────
    blocks.append(div())
    blocks.append(h2("💼 Top Jobs to Apply"))

    if submit_jobs:
        blocks.append(bul(plain(f"Recommended ({len(submit_jobs)} shown, max 5):")))
        for idx, job in enumerate(submit_jobs, 1):
            fit = job.get("career_fit_score", "?")
            ats = job.get("ats_score", 0)
            title = job.get("title", "?")[:60]
            company = job.get("company", "?")
            location = job.get("location", "?")
            url = job.get("url", "")
            source = (job.get("sources", [job.get("source", "?")])[0] or "?").upper()[:15]
            verdict = job.get("verdict_reason", "")[:80]

            parts = [bold(f"#{idx} "), bold(f"[Fit:{fit} ATS:{ats} {source}] ")]
            if url:
                parts.append(linked_text(title, url))
            else:
                parts.append(plain(title))
            parts.append(plain(f" @ {company} ({location})"))
            blocks.append(bul(*parts))
            if verdict:
                blocks.append(bul(plain(f"    💡 {verdict}")))
    elif review_jobs:
        blocks.append(bul(plain(f"No SUBMIT jobs today. {len(review_jobs)} in REVIEW:")))
        for idx, job in enumerate(review_jobs[:3], 1):
            title = job.get("title", "?")[:50]
            company = job.get("company", "?")
            fit = job.get("career_fit_score", "?")
            blocks.append(bul(bold(f"#{idx} "), plain(f"{title} @ {company} (Fit:{fit})")))
    else:
        blocks.append(bul(plain("No new jobs scored today. Job radar will run next cycle.")))

    # ── 4. PIPELINE HEALTH ───────────────────────────────────────────────
    blocks.append(div())
    blocks.append(h2("📊 Pipeline Health"))

    # Pipeline narrative
    if pipeline_total > 0:
        rate = (pipeline_interviews / pipeline_total * 100) if pipeline_total > 0 else 0
        if rate >= 10:
            blocks.append(callout(
                f"Strong pipeline: {pipeline_applied} applied, {pipeline_interviews} interviews "
                f"({rate:.0f}% interview rate). Target: 15%+.",
                "🟢" if rate >= 15 else "⚠️"
            ))
        elif rate >= 5:
            blocks.append(callout(
                f"Building momentum: {pipeline_applied} applied, {rate:.0f}% interview rate. "
                f"Push more apps or improve targeting.",
                "⚠️"
            ))
        else:
            blocks.append(callout(
                f"Low interview rate ({rate:.0f}%). Consider better CV tailoring or "
                f"higher-scoring jobs only.",
                "⚠️"
            ))

        blocks.append(bul(plain(f"Total tracked: {pipeline_total} | Applied: {pipeline_applied} | "
                              f"Interviews: {pipeline_interviews} | Stale: {db_stale}")))
    else:
        blocks.append(callout("Pipeline empty. Job radar hasn't found matches yet.", "⚠️"))

    # ── 5. CONTENT ────────────────────────────────────────────────────────
    blocks.append(div())
    blocks.append(h2("📝 Content & Engagement"))

    if post_today:
        blocks.append(callout(
            f"📣 Post queued for today: {post_today.get('title', post_today.get('hook','untitled'))[:60]}",
            "🟢"
        ))
        blocks.append(bul(plain("Post and stay active 60 min — reply to every comment")))
    else:
        if streak > 0:
            blocks.append(callout(
                f"⚠️ {streak}-day streak at risk. No post scheduled for today.",
                "⚠️"
            ))
        else:
            blocks.append(bul(plain("No content streak active. Queue a post this week.")))

    # Runway
    if runway is not None:
        if runway <= 3:
            blocks.append(bul(plain(f"🚨 Content runway: {runway} days. Queue more posts NOW.")))
        elif runway <= 7:
            blocks.append(bul(plain(f"⚠️ Content runway: {runway} days. Schedule posts soon.")))
        else:
            blocks.append(bul(plain(f"Content runway: {runway} days. Healthy.")))

    # ── 6. SYSTEM STATUS (only if problems) ─────────────────────────────
    blocks.append(div())
    blocks.append(h2("🔧 System Status"))

    issues = []
    if not gw:
        issues.append("Gateway DOWN — AI agents not responding")
    if isinstance(agent_health, dict):
        for name, info in agent_health.items():
            if isinstance(info, dict):
                if info.get("stale"):
                    issues.append(f"Agent '{name}' stalled")
                if not info.get("healthy", True):
                    issues.append(f"Agent '{name}' unhealthy")

    if failures_path.exists() and failures_path.stat().st_size > 0:
        issues.append("Job source failures in last run")

    if issues:
        for issue in issues:
            blocks.append(bul(plain(f"❌ {issue}")))
    else:
        blocks.append(callout("All systems operational.", "🟢"))

    # ── 7. CALENDAR (compact) ───────────────────────────────────────────
    cal_path = Path("/tmp") / f"calendar-events-{today}.json"
    if cal_path.exists():
        try:
            cal_raw = json.load(open(cal_path))
            cal_events = cal_raw if isinstance(cal_raw, list) else cal_raw.get("events", cal_raw.get("data", []))
            if cal_events:
                blocks.append(div())
                blocks.append(h2(f"📅 Today ({len(cal_events)} events)"))
                for ev in cal_events[:5]:
                    title = ev.get("title", ev.get("summary", "?"))[:50]
                    start = str(ev.get("start", ""))[:16]
                    is_all_day = ev.get("is_all_day", "T" not in start)
                    if is_all_day:
                        blocks.append(bul(plain(f"🗓 {title}")))
                    else:
                        t = start.split("T")[-1][:5] if "T" in start else start
                        blocks.append(bul(plain(f"🕐 {t} — {title}")))
        except Exception:
            pass

    return blocks, today

# ── Notion publish ─────────────────────────────────────────────────────────
def notion_req(method, endpoint, body=None):
    url = f"https://api.notion.com/v1{endpoint}"
    resp = requests.request(method, url, headers=HEADERS, json=body, timeout=30)
    if resp.status_code >= 400:
        print(f"  Notion API error {resp.status_code}: {resp.text[:200]}")
        return None, resp.text[:200]
    return resp.json() if body is not None else None, None

def publish_to_notion(blocks, date_str):
    """Create or update today's briefing page in Notion."""
    today_iso = datetime.now(CAIRO).date().isoformat()

    # Check if today's page already exists
    query_body = {
        "filter": {
            "property": "Name",
            "title": {"contains": today_iso}
        }
    }
    try:
        result, _ = notion_req("POST", f"/databases/{BRIEFINGS_DB}/query", query_body)
        if result and result.get("results"):
            page_id = result["results"][0]["id"]
            # Update existing page
            notion_req("PATCH", f"/pages/{page_id}", {
                "properties": {"Name": {"title": [{"text": {"content": f"AM — {today_iso}"}}]}}
            })
            # Clear and rewrite blocks
            try:
                requests.patch(
                    f"https://api.notion.com/v1/blocks/{page_id}/children",
                    headers=HEADERS, json={"children": blocks[:100]}, timeout=30
                )
            except Exception as e:
                print(f"  Block write error (non-fatal): {e}")
            return page_id
    except Exception as e:
        print(f"  Query error (creating new page): {e}")

    # Create new page
    page_body = {
        "parent": {"database_id": BRIEFINGS_DB},
        "properties": {
            "Name": {"title": [{"text": {"content": f"AM — {today_iso}"}}]},
            "Date": {"date": {"start": today_iso}}
        }
    }
    try:
        result, _ = notion_req("POST", "/pages", page_body)
        if result and result.get("id"):
            page_id = result["id"]
            time.sleep(1)
            try:
                requests.patch(
                    f"https://api.notion.com/v1/blocks/{page_id}/children",
                    headers=HEADERS, json={"children": blocks[:100]}, timeout=30
                )
            except Exception as e:
                print(f"  Block write error (non-fatal): {e}")
            return page_id
    except Exception as e:
        print(f"  Page creation error: {e}")
    return None

if __name__ == "__main__":
    failures_path = Path(WORKSPACE / "data" / "source-failures.jsonl")
    print("Building CEO briefing...")
    blocks, date_str = build_blocks()
    print(f"  Generated {len(blocks)} blocks")

    page_id = publish_to_notion(blocks, date_str)
    if page_id:
        print(f"  ✅ Published to Notion: {page_id}")
    else:
        print("  ⚠️ Notion publish failed — check token/permissions")

    print("\nDone.")
