#!/usr/bin/env python3

# ==============================================================================
# AGENT BEHAVIOR STANDARD — Anthropic XML-Structured Format
# ==============================================================================
# Prompt structure for any future LLM calls:
#   <task>What to do</task>
#   <context>Background, Ahmed's profile, data available</context>
#   <constraints>Rules, what NOT to do, format requirements</constraints>
#   <output_format>Exact output structure expected</output_format>
# ==============================================================================
"""
Brief Me Runner - Executes the morning briefing by reading all data files
and generating the Notion page + Telegram message.
"""
import json, re, requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.header import decode_header

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
NOTION_TOKEN = "NOTION_TOKEN_REDACTED"
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
BRIEFINGS_DB = "3268d599-a162-812d-a59e-e5496dec80e7"
CAIRO = timezone(timedelta(hours=2))

def linked_text(text, url):
    return {"text": {"content": str(text)[:2000], "link": {"url": url}}}

def mailto(text, addr):
    """Create a clickable mailto link."""
    return linked_text(text, f"mailto:{addr}")

def decode_email_subject(encoded):
    """Decode quoted-printable/RFC2047 email subjects to plain text."""
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
    """Extract email address from 'Name <email@host>' format."""
    if not from_field:
        return ""
    match = re.search(r'<([^>]+)>', from_field)
    if match:
        return match.group(1)
    # Fallback: look for anything that looks like an email
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', from_field)
    return match.group(0) if match else ""

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
    raw_email = data["email"].get("data", {})
    
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
    
    def add_email_items(items, emoji):
        """Render individual emails with Gmail deep links."""
        for item in items:
            subject = decode_email_subject(item.get("subject") or "No subject")
            addr = extract_email_addr(item.get("from") or "")
            subj_short = subject[:65] + ("..." if len(subject) > 65 else "")
            if addr:
                # Gmail deep link — clicking opens Gmail web with the email visible
                gmail_url = f"https://mail.google.com/mail/u/0/?tab=mm&srch={requests.utils.quote(f'subject:\u201c{subject}\u201d')}"
                blocks.append(bul(linked_text(f"{emoji} {subj_short}", gmail_url)))
            else:
                blocks.append(bul(plain(f"{emoji} {subj_short} (no reply address)")))
    
    add_email_items(raw_email.get("interview_invites", []), "🎯")
    add_email_items(raw_email.get("recruiter_messages", []), "📬")
    add_email_items(raw_email.get("follow_ups_needed", []), "🔁")
    
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
    
    # Today's actions + algorithm reminder
    blocks.append(bul(bold("▶ Actions: "), plain(f"1) Apply to {len(submit_jobs)} SUBMIT jobs | 2) Post LinkedIn | 3) Comment Radar")))
    if li_has:
        blocks.append(bul(plain("⏰ After posting: stay active 60 min, reply to every comment (algorithm test)")))
    
    # ── LINKEDIN COMMENT RADAR ──
    if radar_path.exists():
        radar = json.load(open(radar_path))
        top_posts = radar.get("top_posts", [])[:5]
        if top_posts:
            drafted = radar.get("comments_drafted", 0)
            blocks.append(h2(f"📡 Comment Radar ({drafted} drafts ready)"))
            for idx, rp in enumerate(top_posts, 1):
                url = rp.get("url", "")
                author = rp.get("author", "?")[:30]
                pqs = rp.get("pqs", 0)
                pri = " [PRIORITY]" if rp.get("priority") else ""
                preview = rp.get("preview", "")[:100]
                comment = rp.get("draft_comment", "")
                if url:
                    blocks.append(bul(bold(f"#{idx}[PQS:{pqs}]{pri} "), linked_text(f"{author}", url)))
                    blocks.append(bul(plain(f"   Post: {preview}...")))
                    if comment:
                        blocks.append(bul(bold("   Draft: "), plain(comment[:280])))
    
    # ── SUGGESTED CONNECTIONS ──
    outreach_path = DATA_DIR / "outreach-suggestions.json"
    if outreach_path.exists():
        outreach_data = json.load(open(outreach_path))
        suggestions = outreach_data.get("suggestions", [])[:5]
        if suggestions:
            blocks.append(h2(f"🤝 Connect ({len(suggestions)} suggestions)"))
            for idx, s in enumerate(suggestions, 1):
                name = s.get("name", "?")[:30]
                role = s.get("role", "")[:40]
                company = s.get("company", "?")[:25]
                url = s.get("url", "")
                reason = s.get("reason", "")[:60]
                if url:
                    blocks.append(bul(bold(f"#{idx} "), linked_text(name, url), plain(f" - {role}" if role else "")))
                    blocks.append(bul(plain(f"   {reason}")))
                else:
                    blocks.append(bul(bold(f"#{idx} {name}"), plain(f" at {company}")))
        else:
            blocks.append(h2("🤝 Connect"))
            blocks.append(bul(plain("No new suggestions today")))
    else:
        blocks.append(h2("🤝 Connect"))
        blocks.append(bul(plain("Outreach agent not run yet")))
    
    # ── DATA QUALITY (compact) ──
    blocks.append(h2("📡 Data Quality"))
    blocks.append(bul(plain(" | ".join(
        f"{'✅' if d.get('meta',{}).get('status')=='success' else '⚠️'} {d.get('meta',{}).get('agent',k)}"
        for k, d in data.items()
    ))))
    
    # Job source health detail
    source_health = []
    for src_name, src_file in [("LinkedIn", "linkedin.json"), ("Indeed", "indeed.json"), ("Google", "google-jobs.json")]:
        src_path = Path(WORKSPACE) / "data" / "jobs-raw" / src_file
        if src_path.exists():
            try:
                sd = json.loads(src_path.read_text())
                if isinstance(sd, list):
                    cnt = len(sd)
                    age = "no meta"
                else:
                    cnt = len(sd.get("data", []))
                    gen = sd.get("meta", {}).get("generated_at", "")
                    if gen:
                        from datetime import datetime as _dt
                        gen_t = _dt.fromisoformat(gen)
                        age_h = (now_cairo() - gen_t).total_seconds() / 3600
                        age = f"{age_h:.0f}h ago"
                    else:
                        age = "no meta"
                icon = "✅" if cnt > 0 else "❌"
                source_health.append(f"{icon} {src_name}: {cnt} jobs ({age})")
            except Exception:
                source_health.append(f"⚠️ {src_name}: read error")
        else:
            source_health.append(f"❌ {src_name}: file missing")
    
    # Check for pipeline failures
    failures_path = Path(WORKSPACE) / "data" / "source-failures.jsonl"
    failed_agents = []
    if failures_path.exists():
        for line in failures_path.read_text().strip().split("\n"):
            if line.strip():
                try:
                    f_data = json.loads(line)
                    failed_agents.append(f_data.get("agent", "unknown"))
                except Exception:
                    pass
    
    blocks.append(bul(plain("Job Sources: " + " | ".join(source_health))))
    if failed_agents:
        blocks.append(bul(plain(f"🔴 FAILED (after retry): {', '.join(failed_agents)}")))
    
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
    
    # Check for existing briefing page for today - update instead of creating duplicate
    existing_page_id = None
    try:
        query_resp = requests.post(
            f"https://api.notion.com/v1/databases/{BRIEFINGS_DB}/query",
            headers=HEADERS,
            json={"filter": {"property": "Name", "title": {"contains": today}}, "page_size": 5}
        )
        if query_resp.status_code == 200:
            results = query_resp.json().get("results", [])
            if results:
                existing_page_id = results[0]["id"]
                print(f"  Found existing page for {today}, updating...")
    except Exception as e:
        print(f"  Warning: Could not check for existing page: {e}")

    if existing_page_id:
        # Update existing page: update properties + delete old blocks + add new blocks
        # 1. Update properties
        requests.patch(f"https://api.notion.com/v1/pages/{existing_page_id}",
                       headers=HEADERS, json={"properties": properties})
        # 2. Delete old blocks
        try:
            old_blocks = requests.get(
                f"https://api.notion.com/v1/blocks/{existing_page_id}/children?page_size=100",
                headers=HEADERS
            ).json().get("results", [])
            for blk in old_blocks:
                requests.delete(f"https://api.notion.com/v1/blocks/{blk['id']}", headers=HEADERS)
        except Exception:
            pass
        # 3. Add new blocks (Notion limit: 100 per request)
        for i in range(0, len(blocks), 100):
            requests.patch(
                f"https://api.notion.com/v1/blocks/{existing_page_id}/children",
                headers=HEADERS, json={"children": blocks[i:i+100]}
            )
        page = requests.get(f"https://api.notion.com/v1/pages/{existing_page_id}", headers=HEADERS).json()
        url = page.get("url", "")
        print(f"✅ Updated: {url}")
        return url
    else:
        # Create new page
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
