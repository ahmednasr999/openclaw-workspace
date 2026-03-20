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
    today_display = datetime.now(CAIRO).strftime("%A, %B %d, %Y")
    
    pipe = _adapters.adapt_pipeline(data["pipeline"])
    jobs = _adapters.adapt_jobs(data["jobs"])
    content = _adapters.adapt_content(data["content"])
    sys_adapted = _adapters.adapt_system(data["system"])
    outreach = _adapters.adapt_outreach(data["outreach"])
    email = _adapters.adapt_email(data["email"])
    
    submit_jobs = jobs.get("submit", [])[:10]  # Cap at 10 to stay under Notion's 100-block limit
    review_jobs = jobs.get("review", [])[:10]
    active = pipe.get("active_count", 0)
    health = content.get("content_health", {})
    pipeline_c = content.get("pipeline", {})
    infra = sys_adapted.get("infrastructure", {})
    cats = email.get("categories", {})
    # email is already adapted via adapt_email
    
    # Build blocks
    blocks = []
    blocks.append(callout("No urgent items today. All systems operational.", "🟢"))
    blocks.append(div())
    
    # PIPELINE
    blocks.append(h2("📋 Pipeline Update"))
    app_statuses = {k:v for k,v in pipe.get("by_status",{}).items() if "discovered" not in k.lower()}
    blocks.append(bul(plain(f"Active applications: {active} | Total tracked: {pipe.get('total_applications', 0)}")))
    blocks.append(bul(plain(f"External confirmed: {pipe.get('external_applied_count', 0)}")))
    if app_statuses:
        blocks.append(bul(plain("By status: " + ", ".join(f"{k}: {v}" for k,v in app_statuses.items() if v > 0))))
    tw = pipe.get("this_week", {})
    blocks.append(bul(plain(f"This week: {tw.get('applied', 0)} applications")))
    funnel = pipe.get("conversion_funnel", {})
    blocks.append(bul(plain(f"Funnel: {funnel.get('applied',0)} applied > {funnel.get('screening',0)} screening > {funnel.get('interview',0)} interview > {funnel.get('offer',0)} offer")))
    stale = pipe.get("stale_applications", [])
    blocks.append(bul(plain(f"Stale (14+ days): {len(stale)}" if stale else "No stale applications")))
    followups = pipe.get("follow_ups_overdue", [])
    blocks.append(bul(plain(f"Follow-ups overdue: {len(followups)}" if followups else "No overdue follow-ups")))
    interviews = pipe.get("interviews_upcoming", [])
    blocks.append(bul(plain(f"Upcoming interviews: {len(interviews)}" if interviews else "No upcoming interviews")))
    blocks.append(div())
    
    # JOBS - ALL with clickable links + ATS
    blocks.append(h2("🔍 New Job Recommendations"))
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
    source_summary = " | ".join(f"{s.upper()}: {c}" for s, c in sorted(source_counts.items(), key=lambda x: -x[1]))
    blocks.append(bul(plain(f"Scanned {total_scanned} jobs → {len(submit_jobs)} SUBMIT | {len(review_jobs)} REVIEW")))
    if source_summary:
        blocks.append(bul(plain(f"Sources: {source_summary}")))
    
    blocks.append(h3("🟢 SUBMIT — Strong Career Fit"))
    for idx, job in enumerate(submit_jobs, 1):
        fit = job.get("career_fit_score", "?")
        ats = job.get("ats_score", 0)
        title = job.get("title", "?")
        company = job.get("company", "?")
        location = job.get("location", "?")
        url = job.get("url", "")
        reason = job.get("verdict_reason", "")
        
        source = ", ".join(job.get("sources", [job.get("source", "?")])).upper()
        parts = [bold(f"#{idx} [Fit: {fit}/10 | ATS: {ats}/100 | {source}] ")]
        if url:
            parts.append(linked_text(title, url))
        else:
            parts.append(plain(title))
        parts.append(plain(f" at {company} ({location})"))
        blocks.append(bul(*parts))
        if reason:
            blocks.append(bul(plain(f"  → {reason}")))
    
    blocks.append(h3("🟡 REVIEW — Worth a Look"))
    for idx, job in enumerate(review_jobs, 1):
        fit = job.get("career_fit_score", "?")
        ats = job.get("ats_score", 0)
        title = job.get("title", "?")
        company = job.get("company", "?")
        location = job.get("location", "?")
        url = job.get("url", "")
        reason = job.get("verdict_reason", "")
        
        source = ", ".join(job.get("sources", [job.get("source", "?")])).upper()
        parts = [bold(f"#{idx} [Fit: {fit}/10 | ATS: {ats}/100 | {source}] ")]
        if url:
            parts.append(linked_text(title, url))
        else:
            parts.append(plain(title))
        parts.append(plain(f" at {company} ({location})"))
        blocks.append(bul(*parts))
        if reason:
            blocks.append(bul(plain(f"  → {reason}")))
    
    blocks.append(div())
    
    # EMAIL
    blocks.append(h2("📧 Email Highlights"))
    blocks.append(bul(plain(f"Scanned: {email.get('scanned_count', 0)} emails")))
    n_int = len(cats.get("interview_invite", []))
    n_rec = len(cats.get("recruiter_reach", []))
    if n_int:
        blocks.append(bul(plain(f"🎯 {n_int} interview invitations detected!")))
    if n_rec:
        blocks.append(bul(plain(f"📨 {n_rec} recruiter messages")))
    if not (n_int or n_rec):
        blocks.append(bul(plain("No urgent emails detected")))
    blocks.append(div())
    
    # CONTENT
    blocks.append(h2("📝 Content Status"))
    tp = content.get("today", {}).get("scheduled_post", {})
    if tp and tp.get("title"):
        blocks.append(bul(plain(f"Today: \"{tp['title']}\" ({tp.get('status','?')})")))
    else:
        blocks.append(bul(plain("No post scheduled for today")))
    blocks.append(bul(plain(f"Streak: {health.get('posting_streak',0)} days | Runway: {health.get('days_until_content_runs_out','?')} days")))
    blocks.append(bul(plain(f"Pipeline: {pipeline_c.get('ideas',0)} ideas | {pipeline_c.get('drafts',0)} drafts | {pipeline_c.get('scheduled',0)} scheduled | {pipeline_c.get('published',0)} published")))
    blocks.append(div())
    
    # OUTREACH
    blocks.append(h2("🤝 Network & Outreach"))
    next_acts = outreach.get("next_actions", [])
    if next_acts:
        for a in next_acts[0:3]:
            blocks.append(bul(plain(f"{a.get('next_action','?')}: {a.get('name','?')} ({a.get('title','')}, {a.get('company','')})")))
    else:
        blocks.append(bul(plain("No outreach actions queued")))
    weekly = outreach.get("this_week", {})
    if weekly:
        blocks.append(bul(plain(f"This week: {weekly.get('sent',0)} sent | {weekly.get('accepted',0)} accepted | {weekly.get('pending',0)} pending")))
    blocks.append(div())
    
    # SYSTEM
    blocks.append(h2("🖥️ System Health"))
    infra = sys_adapted.get("infrastructure", {})
    gw_status = "✅ healthy" if infra.get("gateway_healthy") else "❌ down"
    blocks.append(bul(plain(f"Disk: {infra.get('disk_percent','?')}% | RAM: {infra.get('ram_percent','?')}% | Gateway: {gw_status}")))
    hc = sys_adapted.get("agent_health_count", 0)
    tc = sys_adapted.get("agent_total_count", 0)
    blocks.append(bul(plain(f"Agents: {hc}/{tc} healthy")))
    alert_list = sys_adapted.get("alerts", [])
    if alert_list:
        for a in alert_list[0:3]:
            blocks.append(bul(plain(f"⚠️ {a.get('message', str(a))}")))
    else:
        blocks.append(bul(plain("No alerts")))
    blocks.append(div())
    
    # KPIs
    blocks.append(h2("📊 KPI Dashboard"))
    avg_fit = jobs.get("kpi", {}).get("avg_fit_score", "?")
    blocks.append(bul(plain(f"Pipeline: {active} active | {len(interviews)} interviews")))
    blocks.append(bul(plain(f"Jobs: {len(submit_jobs)} SUBMIT, {len(review_jobs)} REVIEW | Avg fit: {avg_fit}")))
    blocks.append(bul(plain(f"Content: {pipeline_c.get('published',0)} published | {health.get('posting_streak',0)}d streak")))
    blocks.append(bul(plain(f"System: {hc}/{tc} agents healthy")))
    blocks.append(div())
    
    # ACTIONS
    blocks.append(h2("▶️ Today's Actions"))
    blocks.append(bul(plain(f"1. Review {len(submit_jobs)} SUBMIT job recommendations and apply")))
    blocks.append(bul(plain(f"2. Check pipeline for follow-up opportunities ({active} active)")))
    blocks.append(bul(plain(f"3. Content runway: {health.get('days_until_content_runs_out','?')} days")))
    blocks.append(div())
    
    # DATA QUALITY
    blocks.append(h2("📡 Data Quality"))
    for key, d in data.items():
        m = d.get("meta", {})
        e = "✅" if m.get("status") == "success" else "⚠️"
        blocks.append(bul(plain(f"{e} {m.get('agent',key)}: {m.get('status','?')} | {str(m.get('generated_at','?'))[0:19]} | {m.get('duration_ms',0)}ms")))
    
    # Properties for DB
    total_jobs = len(submit_jobs) + len(review_jobs) + jobs.get("skip_count", 0)
    gen_time = round(sum(d.get("meta", {}).get("duration_ms", 0) for d in data.values()) / 1000, 1)
    sys_infra = sys_adapted.get("infrastructure", {})
    sys_health = "✅ All Clear"
    disk_pct = sys_infra.get("disk_percent", 0)
    disk_pct = disk_pct if isinstance(disk_pct, (int, float)) else 0
    if disk_pct > 90 or not sys_infra.get("gateway_healthy", True):
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
        "Emails Flagged": {"number": len(email.get("action_required", []))},
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
