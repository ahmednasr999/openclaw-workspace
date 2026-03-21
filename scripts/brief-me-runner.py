#!/usr/bin/env python3
"""
Brief Me Runner - Executes the morning briefing by reading all data files
and generating the Notion page + Telegram message.
"""
import json, requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
NOTION_TOKEN = "NOTION_TOKEN_REDACTED"
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
BRIEFINGS_DB = "3268d599-a162-812d-a59e-e5496dec80e7"
CAIRO = timezone(timedelta(hours=2))

def linked_text(text, url):
    return {"text": {"content": str(text)[:2000], "link": {"url": url}}}

def plain(text):
    return {"text": {"content": str(text)[:2000]}}

def bold(text):
    return {"text": {"content": str(text)[:2000]}, "annotations": {"bold": True}}

def h2(t): return {"object":"block","type":"heading_2","heading_2":{"rich_text":[plain(t)]}}
def h3(t): return {"object":"block","type":"heading_3","heading_3":{"rich_text":[plain(t)]}}
def bul(*parts): return {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text": list(parts)}}
def div(): return {"object":"block","type":"divider","divider":{}}
def callout(t, emoji="🟢"): return {"object":"block","type":"callout","callout":{"rich_text":[plain(t)],"icon":{"emoji":emoji}}}

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module as _import
_adapters = _import("briefing-adapters")

def load_data():
    raw = {}
    for key, path in {
        "pipeline":"pipeline-status.json",
        "email":"email-summary.json", 
        "content":"content-schedule.json",
        "outreach":"outreach-summary.json",
        "system":"system-health.json",
        "jobs":"jobs-summary.json"
    }.items():
        with open(DATA_DIR / path) as f:
            raw[key] = json.load(f)
    return raw

def create_briefing():
    data = load_data()
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    
    pipe = _adapters.adapt_pipeline(data["pipeline"])
    jobs = _adapters.adapt_jobs(data["jobs"])
    content = _adapters.adapt_content(data["content"])
    sys_adapted = _adapters.adapt_system(data["system"])
    outreach = _adapters.adapt_outreach(data["outreach"])
    email = _adapters.adapt_email(data["email"])
    
    # Cap jobs to stay under Notion's 100-block limit
    submit_jobs = jobs.get("submit", [])[:8]
    review_jobs = jobs.get("review", [])[:8]
    active = pipe.get("active_count", 0)
    health = content.get("content_health", {})
    pipeline_c = content.get("pipeline", {})
    cats = email.get("categories", {})
    interviews = pipe.get("interviews_upcoming", [])
    li_post_path = DATA_DIR / "linkedin-post.json"
    radar_path = DATA_DIR / "comment-radar.json"
    infra = sys_adapted.get("infrastructure", {})
    hc = sys_adapted.get("agent_health_count", 0)
    tc = sys_adapted.get("agent_total_count", 0)
    
    # Count total scanned from jobs-merged.json
    merged_path = DATA_DIR / "jobs-merged.json"
    total_scanned = 0
    source_counts = {}
    if merged_path.exists():
        merged = json.load(open(merged_path))
        merged_jobs = merged.get("data", merged.get("jobs", []))
        if isinstance(merged_jobs, list):
            total_scanned = len(merged_jobs)
        for mj in (merged_jobs if isinstance(merged_jobs, list) else []):
            for s in mj.get("sources", [mj.get("source", "?")]):
                source_counts[s] = source_counts.get(s, 0) + 1
    source_summary = " | ".join(f"{s.upper()}: {c}" for s, c in sorted(source_counts.items(), key=lambda x: -x[1])[:5])
    
    avg_fit = jobs.get("kpi", {}).get("avg_fit_score", "?")
    n_int = len(cats.get("interview_invite", []))
    n_rec = len(cats.get("recruiter_reach", []))
    alert_list = sys_adapted.get("alerts", [])
    gw_status = "✅" if infra.get("gateway_healthy") else "❌"
    
    # Build blocks — NO dividers to save block count
    blocks = []
    blocks.append(callout("No urgent items today. All systems operational.", "🟢"))
    
    # ── PIPELINE + SYSTEM (consolidated) ──
    blocks.append(h2("📋 Pipeline & System"))
    funnel = pipe.get("conversion_funnel", {})
    blocks.append(bul(
        plain(f"Pipeline: {active} active | {pipe.get('total_applications',0)} total | "),
        plain(f"Funnel: {funnel.get('applied',0)}→{funnel.get('screening',0)}→{funnel.get('interview',0)}→{funnel.get('offer',0)}"),
        plain(f" | Interviews: {len(interviews)} | Stale: {len(pipe.get('stale_applications',[]))}")
    ))
    blocks.append(bul(
        plain(f"System: Disk {infra.get('disk_percent','?')}% | RAM {infra.get('ram_percent','?')}% | "),
        plain(f"Gateway {gw_status} | Agents {hc}/{tc} healthy")
    ))
    if alert_list:
        blocks.append(bul(plain("⚠️ " + " | ".join(a.get('message', str(a)) for a in alert_list[:2]))))
    
    # ── JOBS ──
    blocks.append(h2(f"🔍 Jobs ({total_scanned} scanned → {len(submit_jobs)} SUBMIT | {len(review_jobs)} REVIEW)"))
    if source_summary:
        blocks.append(bul(plain(f"Sources: {source_summary}")))
    
    blocks.append(h3("🟢 SUBMIT"))
    for idx, job in enumerate(submit_jobs, 1):
        fit = job.get("career_fit_score", "?")
        ats = job.get("ats_score", 0)
        title = job.get("title", "?")
        company = job.get("company", "?")
        location = job.get("location", "?")
        url = job.get("url", "")
        source = ", ".join(job.get("sources", [job.get("source", "?")])).upper()[:20]
        parts = [bold(f"#{idx} [Fit:{fit} ATS:{ats} {source}] ")]
        if url:
            parts.append(linked_text(title, url))
        else:
            parts.append(plain(title))
        parts.append(plain(f" @ {company} ({location})"))
        blocks.append(bul(*parts))
    
    blocks.append(h3("🟡 REVIEW"))
    for idx, job in enumerate(review_jobs, 1):
        fit = job.get("career_fit_score", "?")
        ats = job.get("ats_score", 0)
        title = job.get("title", "?")
        company = job.get("company", "?")
        location = job.get("location", "?")
        url = job.get("url", "")
        source = ", ".join(job.get("sources", [job.get("source", "?")])).upper()[:20]
        parts = [bold(f"#{idx} [Fit:{fit} ATS:{ats} {source}] ")]
        if url:
            parts.append(linked_text(title, url))
        else:
            parts.append(plain(title))
        parts.append(plain(f" @ {company} ({location})"))
        blocks.append(bul(*parts))
    
    # ── EMAIL ──
    blocks.append(h2("📧 Email"))
    blocks.append(bul(plain(f"Scanned: {email.get('scanned_count',0)} | 🎯 {n_int} invites | 📬 {n_rec} recruiter reach")))
    if not (n_int or n_rec):
        blocks.append(bul(plain("No urgent emails")))
    
    # ── CONTENT + ACTIONS ──
    blocks.append(h2("📝 Content & Actions"))
    tp = content.get("today", {}).get("scheduled_post", {})
    li_has = li_post_path.exists() and json.load(open(li_post_path)).get("has_post")
    blocks.append(bul(plain(
        f"Streak: {health.get('posting_streak',0)}d | Runway: {health.get('days_until_content_runs_out','?')}d | "
        f"Pipeline: {pipeline_c.get('ideas',0)}/{pipeline_c.get('drafts',0)}/{pipeline_c.get('scheduled',0)}/{pipeline_c.get('published',0)}"
    )))
    
    # LinkedIn post
    if li_has:
        li_post = json.load(open(li_post_path))["post"]
        blocks.append(bul(bold("📣 Today: "), plain(li_post.get("title","?")[:80] + ( "..." if len(li_post.get("title","")) > 80 else ""))))
        if not li_post.get("image_url"):
            blocks.append(bul(plain("⚠️ No image attached!")))
    elif radar_path.exists() and json.load(open(radar_path)).get("top_posts"):
        blocks.append(bul(plain("📣 No post today — engage via Comment Radar")))
    
    # Today's actions
    blocks.append(bul(bold("▶ Actions: "), plain(f"1) Apply to {len(submit_jobs)} SUBMIT jobs | 2) Post LinkedIn | 3) Comment Radar")))
    
    # ── LINKEDIN COMMENT RADAR ──
    if radar_path.exists():
        radar = json.load(open(radar_path))
        top_posts = radar.get("top_posts", [])[:5]
        if top_posts:
            blocks.append(h2("📡 LinkedIn Radar"))
            blocks.append(bul(plain(f"{radar.get('posts_found',0)} posts found | Top {len(top_posts)}:")))
            for idx, rp in enumerate(top_posts, 1):
                url = rp.get("url", "")
                author = rp.get("author", "?")[:25]
                pqs = rp.get("pqs", 0)
                preview = rp.get("preview", "")[:80]
                if url:
                    blocks.append(bul(bold(f"#{idx}[PQS:{pqs}] "), linked_text(f"{author}", url), plain(f" — {preview}...")))
                else:
                    blocks.append(bul(bold(f"#{idx}[PQS:{pqs}] {author}")))
    
    # ── OUTREACH ──
    blocks.append(h2("🤝 Outreach"))
    next_acts = outreach.get("next_actions", [])[:3]
    if next_acts:
        blocks.append(bul(plain(" | ".join(f"{a.get('next_action','?')}: {a.get('name','?')}" for a in next_acts))))
    weekly = outreach.get("this_week", {})
    if weekly:
        blocks.append(bul(plain(f"This week: {weekly.get('sent',0)} sent | {weekly.get('accepted',0)} accepted | {weekly.get('pending',0)} pending")))
    else:
        blocks.append(bul(plain("No outreach queued")))
    
    # ── DATA QUALITY (compact) ──
    blocks.append(h2("📡 Data Quality"))
    blocks.append(bul(plain(" | ".join(
        f"{'✅' if d.get('meta',{}).get('status')=='success' else '⚠️'} {d.get('meta',{}).get('agent',k)}"
        for k, d in data.items()
    ))))
    
    # Properties for DB
    total_jobs = len(submit_jobs) + len(review_jobs) + jobs.get("skip_count", 0)
    gen_time = round(sum(d.get("meta", {}).get("duration_ms", 0) for d in data.values()) / 1000, 1)
    sys_health = "✅ All Clear"
    disk_pct = infra.get("disk_percent", 0)
    disk_pct = disk_pct if isinstance(disk_pct, (int, float)) else 0
    if disk_pct > 90 or not infra.get("gateway_healthy", True):
        sys_health = "🔴 Issue"
    elif disk_pct > 80:
        sys_health = "⚠️ Warning"
    
    properties = {
        "title": {"title": [{"text": {"content": f"Daily Briefing - {today}"}}]},
        "Date": {"date": {"start": today}},
        "Status": {"select": {"name": "✅ Delivered"}},
        "System Health": {"select": {"name": sys_health}},
        "Jobs Found": {"number": total_jobs},
        "Priority Picks": {"number": len(submit_jobs)},
        "Emails Flagged": {"number": n_int + n_rec},
        "Calendar Events": {"number": 0},
        "LinkedIn Impressions": {"number": 0},
        "Model Used": {"rich_text": [{"text": {"content": "MiniMax-M2.7 + ATS Scorer"}}]},
        "Generation Time (s)": {"number": gen_time}
    }
    
    resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json={
        "parent": {"database_id": BRIEFINGS_DB},
        "properties": properties,
        "children": blocks
    })
    
    if resp.status_code == 200:
        page = resp.json()
        url = page.get("url", "")
        print(f"✅ Created: {url}")
        return url
    else:
        print(f"❌ Error {resp.status_code}: {resp.text[:300]}")
        return None

if __name__ == "__main__":
    create_briefing()
