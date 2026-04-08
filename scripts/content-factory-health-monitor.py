#!/usr/bin/env python3
"""
content-factory-health-monitor.py v2
=====================================
Health check for the NEW Content Factory pipeline:
  RSS Crawler → Exa Scanner → Scorer → Bridge → Auto-Drafter → Auto-Poster

Run: Daily via cron at 5 AM Cairo (before pipeline starts)
Alert: Telegram if any critical component is broken.
"""
import json, os, ssl, subprocess, sys, time, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
LOG_DIR = WORKSPACE / "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = LOG_DIR / "cf-health.log"

CAIRO = timezone(timedelta(hours=2))
NOTION_TOKEN = json.load(open(WORKSPACE / "config" / "notion.json"))["token"]

RSS_DB = "32e8d599-a162-8180-9e3a-fbfc17a84e49"
CAL_DB = "3268d599-a162-814b-8854-c9b8bde62468"

HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}

def log(msg):
    ts = datetime.now(CAIRO).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def notion_req(method, path, body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context()) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:150]}"
    except Exception as e:
        return None, str(e)

def query_db(db_id, filter_body=None, page_size=100):
    all_results, cursor = [], None
    while True:
        body = {"page_size": page_size}
        if cursor: body["start_cursor"] = cursor
        if filter_body: body["filter"] = filter_body
        d, err = notion_req("POST", f"/databases/{db_id}/query", body)
        if err: return [], err
        all_results.extend(d.get("results", []))
        cursor = d.get("next_cursor")
        if not cursor: break
    return all_results, None

def send_telegram(msg):
    try:
        oc_config = json.load(open(WORKSPACE / ".." / "openclaw.json"))
        bot_token = oc_config["channels"]["telegram"]["botToken"]
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({"chat_id": "866838380", "text": msg}).encode()
        req = urllib.request.Request(url, data=data, method="POST",
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context())
    except Exception as e:
        log(f"Telegram failed: {e}")

def safe_select_name(prop):
    """Safely extract select name, handling None values."""
    sel = prop.get("select")
    if sel and isinstance(sel, dict):
        return sel.get("name", "?")
    return "?"

def check_component(name, fn):
    try:
        return fn()
    except Exception as e:
        return {"name": name, "status": "error", "message": str(e)[:150]}

# ═══════════════════════════════════════════════════════════════
# COMPONENT CHECKS — NEW PIPELINE
# ═══════════════════════════════════════════════════════════════

def check_notion_auth():
    """Notion token: can we read?"""
    d, err = notion_req("POST", f"/databases/{RSS_DB}/query", {"page_size": 1})
    if err: return {"status": "fail", "message": err}
    return {"status": "ok", "message": "Token OK"}

def check_rss_db():
    """RSS Intelligence DB: reachable, article counts."""
    all_pages, err = query_db(RSS_DB)
    if err: return {"status": "fail", "message": err}
    new = sum(1 for p in all_pages if safe_select_name(p["properties"].get("Status", {})) == "New")
    high = sum(1 for p in all_pages
               if safe_select_name(p["properties"].get("Status", {})) == "New"
               and safe_select_name(p["properties"].get("Priority", {})) == "High")
    return {"status": "ok", "message": f"{len(all_pages)} total, {new} New, {high} Gold waiting"}

def check_rss_crawler():
    """RSS Crawler (7 AM): ran recently?"""
    state_file = DATA_DIR / "rss-intelligence-state.json"
    if not state_file.exists():
        return {"status": "warn", "message": "Never ran (no state file)"}
    state = json.load(open(state_file))
    last_run = state.get("last_run", "never")
    seen = len(state.get("seen_urls", []))
    try:
        lr = datetime.fromisoformat(last_run)
        age_hours = (datetime.now() - lr).total_seconds() / 3600
        if age_hours > 36:
            return {"status": "warn", "message": f"Stale - last ran {last_run[:16]} ({age_hours:.0f}h ago), {seen} URLs seen"}
    except:
        pass
    return {"status": "ok", "message": f"Last ran {last_run[:16]}, {seen} URLs tracked"}

def check_scorer():
    """Scorer (7:30 AM): articles have scores?"""
    # Check for unscored articles (Quality Score = 0 or null)
    scored, err = query_db(RSS_DB, {"property": "Quality Score", "number": {"greater_than": 0}})
    if err: return {"status": "fail", "message": err}
    unscored, _ = query_db(RSS_DB, {"property": "Quality Score", "number": {"equals": 0}})
    if len(scored) == 0:
        return {"status": "warn", "message": "No scored articles found"}
    return {"status": "ok", "message": f"{len(scored)} scored, {len(unscored)} unscored"}

def check_bridge():
    """Bridge (8:30 AM): ran today?"""
    state_file = DATA_DIR / "rss-to-calendar-state.json"
    if not state_file.exists():
        return {"status": "warn", "message": "Never ran"}
    state = json.load(open(state_file))
    last_run = state.get("last_run", "never")
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    yesterday = (datetime.now(CAIRO) - timedelta(days=1)).strftime("%Y-%m-%d")
    added = state.get("added", 0)
    skipped = state.get("skipped_dup", 0)
    if last_run[:10] == today:
        return {"status": "ok", "message": f"Ran today: {added} added, {skipped} dup skipped"}
    elif last_run[:10] == yesterday:
        return {"status": "ok", "message": f"Ran yesterday: {added} added (next run 8:30 AM)"}
    return {"status": "warn", "message": f"Stale - last ran {last_run[:10]}"}

def check_content_calendar():
    """Content Calendar: entry counts by status."""
    all_pages, err = query_db(CAL_DB)
    if err: return {"status": "fail", "message": err}
    by_status = {}
    for p in all_pages:
        s = safe_select_name(p["properties"].get("Status", {}))
        by_status[s] = by_status.get(s, 0) + 1
    ideas = by_status.get("Ideas", 0) + by_status.get("Idea", 0)
    drafts = by_status.get("Draft", 0) + by_status.get("Drafted", 0)
    scheduled = by_status.get("Scheduled", 0)
    posted = by_status.get("Posted", 0)
    msg = f"{len(all_pages)} total | Ideas={ideas} | Drafts={drafts} | Scheduled={scheduled} | Posted={posted}"
    if ideas == 0 and drafts == 0 and scheduled == 0:
        return {"status": "warn", "message": f"Pipeline empty - no content in queue. {msg}"}
    return {"status": "ok", "message": msg}

def check_auto_drafter():
    """Auto-Drafter: drafts being created? Smart: suppress warning if this week's posts are covered."""
    now = datetime.now(CAIRO)
    weekday = now.weekday()  # 0=Mon ... 6=Sun
    
    # Check for Draft entries
    drafts, err = query_db(CAL_DB, {"property": "Status", "select": {"equals": "Draft"}})
    if err: return {"status": "fail", "message": err}
    if len(drafts) > 0:
        return {"status": "ok", "message": f"{len(drafts)} drafts ready for review"}
    
    # No drafts - but check if this week's Scheduled posts cover us
    # Get remaining work days this week (Sun=6 through Thu=3 in Cairo work week)
    today_str = now.strftime("%Y-%m-%d")
    # Find end of work week (Thursday)
    days_to_thu = (3 - weekday) % 7
    if days_to_thu == 0 and weekday == 3:
        days_to_thu = 0  # Today is Thursday
    end_of_week = (now + timedelta(days=days_to_thu)).strftime("%Y-%m-%d")
    
    scheduled, err2 = query_db(CAL_DB, {"and": [
        {"property": "Status", "select": {"equals": "Scheduled"}},
        {"property": "Planned Date", "date": {"on_or_after": today_str}},
        {"property": "Planned Date", "date": {"on_or_before": end_of_week}},
    ]})
    if err2:
        scheduled = []
    
    if len(scheduled) > 0:
        return {"status": "ok", "message": f"No drafts, but {len(scheduled)} posts scheduled through {end_of_week} ✓"}
    
    # Only warn Thu-Sat (when next week's batch should be getting created)
    # Sun-Wed: CREATE job hasn't run yet, don't cry wolf
    if weekday in (3, 4, 5):  # Thu, Fri, Sat
        return {"status": "warn", "message": "No drafts in queue and no upcoming scheduled posts - drafter may need attention"}
    
    return {"status": "ok", "message": "No drafts yet (CREATE job runs Fri, batch expected by weekend)"}

def check_linkedin_poster():
    """Auto-Poster (9:30 AM): posting status."""
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    # Check watchdog
    wd_file = DATA_DIR / "linkedin-watchdog.json"
    if wd_file.exists():
        wd = json.load(open(wd_file))
        if wd.get("date") == today and wd.get("post_url"):
            return {"status": "ok", "message": f"Posted today: {wd['post_url'][:60]}"}
    # Check safe state
    safe_state = DATA_DIR / "linkedin-auto-poster-safe-state.json"
    if safe_state.exists():
        ss = json.load(open(safe_state))
        if ss.get("date") == today:
            if ss.get("posted"):
                return {"status": "ok", "message": f"Posted: {ss.get('post_url','?')[:60]}"}
            return {"status": "warn", "message": f"Poster ran but no post (exit {ss.get('exit_code')})"}
    # Check Content Calendar for today's posted
    posted_today, _ = query_db(CAL_DB, {"and": [
        {"property": "Status", "select": {"equals": "Posted"}},
        {"property": "Planned Date", "date": {"equals": today}}
    ]})
    if posted_today:
        return {"status": "ok", "message": "Posted (confirmed via Notion)"}
    # Check if there's a scheduled post for today
    sched_today, _ = query_db(CAL_DB, {"and": [
        {"property": "Status", "select": {"equals": "Scheduled"}},
        {"property": "Planned Date", "date": {"equals": today}}
    ]})
    if sched_today:
        return {"status": "ok", "message": f"{len(sched_today)} scheduled for today (poster fires 9:30 AM)"}
    return {"status": "info", "message": "No post scheduled for today"}

def check_gateway():
    """OpenClaw gateway: responsive?"""
    try:
        req = urllib.request.Request("http://127.0.0.1:18789/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=5) as r:
            return {"status": "ok", "message": "Gateway up"}
    except:
        return {"status": "fail", "message": "Gateway unreachable (crons won't fire)"}

def check_visuals():
    """Visual templates: directory exists with recent files?"""
    vis_dir = WORKSPACE / "media" / "post-visuals"
    if not vis_dir.exists():
        return {"status": "warn", "message": "No visuals directory"}
    pngs = list(vis_dir.glob("*.png"))
    if not pngs:
        return {"status": "warn", "message": "No visual templates generated yet"}
    newest = max(f.stat().st_mtime for f in pngs)
    age_days = (datetime.now().timestamp() - newest) / 86400
    return {"status": "ok", "message": f"{len(pngs)} visuals, newest {age_days:.1f}d old"}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    now = datetime.now(CAIRO)
    log(f"=== Content Factory Health v2 === {now.strftime('%Y-%m-%d %H:%M')} Cairo")

    components = [
        ("notion_auth",     check_notion_auth),
        ("gateway",         check_gateway),
        ("rss_db",          check_rss_db),
        ("rss_crawler",     check_rss_crawler),
        ("scorer",          check_scorer),
        ("bridge",          check_bridge),
        ("content_calendar", check_content_calendar),
        ("auto_drafter",    check_auto_drafter),
        ("linkedin_poster", check_linkedin_poster),
        ("visuals",         check_visuals),
    ]

    results = []
    for name, fn in components:
        r = check_component(name, fn)
        r["name"] = name
        results.append(r)
        icon = {"ok": "✅", "warn": "⚠️", "fail": "🔴", "error": "🔴", "info": "ℹ️"}.get(r["status"], "?")
        log(f"  {icon} {name}: {r.get('message','')}")

    # Save state
    health_state = {
        "checked_at": now.isoformat(),
        "components": {r["name"]: {"status": r["status"], "message": r.get("message", "")} for r in results}
    }
    json.dump(health_state, open(DATA_DIR / "cf-health-state.json", "w"), indent=2)

    critical = [r for r in results if r["status"] in ("fail", "error")]
    warnings = [r for r in results if r["status"] == "warn"]
    ok = [r for r in results if r["status"] == "ok"]
    info = [r for r in results if r["status"] == "info"]

    log(f"\n  Summary: {len(ok)} ✅  {len(warnings)} ⚠️  {len(critical)} 🔴  {len(info)} ℹ️")

    # Telegram alert
    if critical or warnings:
        lines = []
        if critical:
            lines.append(f"🛡️ Content Factory Health - ISSUES FOUND")
        else:
            lines.append(f"🛡️ Content Factory Health - ISSUES FOUND")
        lines.append(f"{now.strftime('%Y-%m-%d %H:%M')} Cairo\n")
        for r in critical:
            lines.append(f"🔴 {r['name']}: {r.get('message','')}")
        for r in warnings:
            lines.append(f"⚠️ {r['name']}: {r.get('message','')}")
        lines.append(f"\n✅ OK: {len(ok)}")
        send_telegram("\n".join(lines))
    else:
        lines = [f"🛡️ Content Factory Health - ALL GREEN",
                 f"{now.strftime('%Y-%m-%d %H:%M')} Cairo\n",
                 f"✅ All {len(ok)} components healthy"]
        if info:
            for r in info:
                lines.append(f"ℹ️ {r['name']}: {r.get('message','')}")
        send_telegram("\n".join(lines))

    return 0 if not critical else 1

if __name__ == "__main__":
    sys.exit(main())
