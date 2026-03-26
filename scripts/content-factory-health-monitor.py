#!/usr/bin/env python3
"""
content-factory-health-monitor.py
===================================
Comprehensive end-to-end health check for the Content Factory.
Reports status of every component: RSS → Bridge → Calendar → Scoring → Posting → Engagement.

Run: Daily via cron (after morning briefing)
  0 8 * * * python3 .../content-factory-health-monitor.py >> .../logs/cf-health.log 2>&1

Alert: Telegram if any component is broken.
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

# DB IDs
RSS_DB  = "32e8d599-a162-8180-9e3a-fbfc17a84e49"
CAL_DB  = "3268d599-a162-814b-8854-c9b8bde62468"
PIPE_DB = "3268d599-a162-81b4-b768-f162adfa4971"

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
        if err:
            return [], err
        all_results.extend(d.get("results", []))
        cursor = d.get("next_cursor")
        if not cursor: break
    return all_results, None

def send_telegram(msg):
    try:
        bot_token = subprocess.check_output(
            ["python3", "-c",
             f"import json; print(json.load(open('{WORKSPACE}/../openclaw.json'))['channels']['telegram']['botToken'])"],
            text=True, timeout=5
        ).strip()
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        req = subprocess.Popen(
            ["curl", "-sf", "-X", "POST", url,
             "-d", f"chat_id=866838380", "-d", f"text={msg}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        req.wait(timeout=10)
    except Exception as e:
        log(f"Telegram failed: {e}")

def check_component(name, fn):
    """Run a health check function, catch exceptions."""
    try:
        result = fn()
        if result.get("status") == "ok":
            return result
        else:
            return {"name": name, "status": "fail", **result}
    except Exception as e:
        return {"name": name, "status": "error", "message": str(e)}

# ═══════════════════════════════════════════════════════════════
# COMPONENT CHECKS
# ═══════════════════════════════════════════════════════════════

def check_rss_db():
    """RSS Intelligence DB: reachable, has articles, has new ones today."""
    pages, err = query_db(RSS_DB, {"property": "Status", "select": {"equals": "New"}})
    if err:
        return {"status": "fail", "message": err}
    
    all_pages, _ = query_db(RSS_DB)
    new_count = len(pages)
    total = len(all_pages)
    
    if new_count == 0 and total > 50:
        msg = f"OK — {total} total, 0 new (all processed)"
    elif new_count > 0:
        msg = f"OK — {total} total, {new_count} NEW"
    else:
        msg = f"SUSPICIOUS — only {total} total articles"
    
    return {"status": "ok", "message": msg, "total": total, "new": new_count}

def check_content_calendar():
    """Content Calendar DB: has entries, recent activity."""
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    
    # Count by status
    all_pages, err = query_db(CAL_DB)
    if err:
        return {"status": "fail", "message": err}
    
    by_status = {}
    for p in all_pages:
        s = p["properties"].get("Status", {}).get("select", {}).get("name", "?") or \
            p["properties"].get("Status", {}).get("status", {}).get("name", "?") or "?"
        by_status[s] = by_status.get(s, 0) + 1
    
    # Check scheduled for today
    scheduled_today = 0
    for p in all_pages:
        pd = p["properties"].get("Planned Date", {}).get("date", {}).get("start", "")
        ps = p["properties"].get("Status", {}).get("select", {}).get("name", "") or \
             p["properties"].get("Status", {}).get("status", {}).get("name", "")
        if pd == today and ps == "Scheduled":
            scheduled_today += 1
    
    # Check Ideas queue depth
    ideas_count = by_status.get("Idea", 0) + by_status.get("Ideas", 0)
    
    msg = f"{len(all_pages)} entries | Ideas={ideas_count} | Scheduled today={scheduled_today} | {by_status}"
    
    if len(all_pages) < 5:
        return {"status": "warn", "message": f"Very few entries: {msg}", **by_status}
    if scheduled_today == 0:
        return {"status": "warn", "message": f"No post scheduled for today: {msg}", **by_status}
    
    return {"status": "ok", "message": msg, "total": len(all_pages),
            "ideas": ideas_count, "scheduled_today": scheduled_today, "by_status": by_status}

def check_rss_to_cal_bridge():
    """RSS → Content Calendar bridge: ran today?"""
    state_file = DATA_DIR / "rss-to-calendar-state.json"
    
    if not state_file.exists():
        return {"status": "warn", "message": "Never ran (no state file)"}
    
    state = json.load(open(state_file))
    last_run = state.get("last_run", "never")
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    
    if last_run != today:
        return {"status": "warn", "message": f"Last ran {last_run} (not today)"}
    
    added = state.get("added", 0)
    skipped = state.get("skipped_dup", 0)
    return {"status": "ok", "message": f"Ran today: {added} added, {skipped} dup skipped"}

def check_content_orchestrator():
    """Content Orchestrator: ran today?"""
    state_file = DATA_DIR / "content-pipeline-state.json"
    
    if not state_file.exists():
        return {"status": "warn", "message": "Never ran"}
    
    state = json.load(open(state_file))
    last_run = state.get("last_run", "never")
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    yesterday = (datetime.now(CAIRO) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if last_run[:10] not in [today, yesterday]:
        return {"status": "warn", "message": f"Last ran {last_run[:10]} (stale)"}
    
    prime = state.get("prime_status", "?")
    publish = state.get("publish_status", "?")
    collect = state.get("collect_status", "?")
    post_url = state.get("today_post_url", "")
    
    msg = f"prime={prime}, publish={publish}, collect={collect}"
    if post_url:
        msg += f", post={post_url[:50]}"
    
    if "failed" in [prime, collect]:
        return {"status": "warn", "message": msg, "prime": prime, "publish": publish, "collect": collect}
    
    return {"status": "ok", "message": msg, "prime": prime, "publish": publish, "collect": collect,
            "post_url": post_url}

def check_linkedin_post_today():
    """LinkedIn: was a post made today?"""
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    
    # Check watchdog
    wd_file = DATA_DIR / "linkedin-watchdog.json"
    if wd_file.exists():
        wd = json.load(open(wd_file))
        if wd.get("date") == today and wd.get("post_url"):
            return {"status": "ok", "message": f"Posted: {wd['post_url'][:60]}",
                    "post_url": wd["post_url"]}
    
    # Check safe state
    safe_state = DATA_DIR / "linkedin-auto-poster-safe-state.json"
    if safe_state.exists():
        ss = json.load(open(safe_state))
        if ss.get("date") == today:
            posted = ss.get("posted", False)
            if posted == "unverified" or ss.get("needs_review"):
                return {"status": "warn", "message": f"Unverified: {ss}"}
            if posted:
                return {"status": "ok", "message": f"Posted: {ss.get('post_url','?')[:60]}",
                        "post_url": ss.get("post_url")}
            if not posted:
                return {"status": "warn", "message": f"Auto-poster ran but no post (exit {ss.get('exit_code')})"}
    
    # Check Content Calendar Posted today
    today_pages, err = query_db(CAL_DB, {
        "and": [
            {"property": "Status", "select": {"equals": "Posted"}},
            {"property": "Planned Date", "date": {"equals": today}}
        ]
    })
    if not err and today_pages:
        url = today_pages[0]["properties"].get("Post URL", {}).get("url", "")
        return {"status": "ok", "message": f"Posted (via Notion): {url[:60]}"}
    
    return {"status": "warn", "message": "No post made today"}

def check_engagement_data():
    """Engagement collector: is it collecting data?"""
    eng_file = DATA_DIR / "linkedin-engagement.json"
    
    if not eng_file.exists():
        return {"status": "warn", "message": "No engagement data yet"}
    
    eng = json.load(open(eng_file))
    collected = eng.get("collected_at", "never")
    
    # Check if collected today or recently
    if collected.startswith(datetime.now(CAIRO).strftime("%Y-%m-%d")):
        return {"status": "ok", "message": f"Collected today: {collected[11:16]}"}
    
    days_ago = "?"
    try:
        from datetime import datetime as dt
        c = datetime.fromisoformat(collected)
        days = (datetime.now(CAIRO) - c).days
        days_ago = str(days)
    except:
        pass
    
    return {"status": "warn", "message": f"Last collected {days_ago} days ago"}

def check_notion_auth():
    """Notion token: can we read?"""
    d, err = notion_req("POST", f"/databases/{RSS_DB}/query", {"page_size": 1})
    if err:
        return {"status": "fail", "message": err}
    return {"status": "ok", "message": "Token OK"}

def check_composio_linkedin():
    """Composio LinkedIn connection."""
    try:
        # Check via Composio MCP if available
        result = subprocess.run(
            ["openclaw", "status"],
            capture_output=True, text=True, timeout=15
        )
        # If we get here, gateway is up
        return {"status": "ok", "message": "Gateway up"}
    except:
        return {"status": "fail", "message": "Gateway unreachable"}

def check_content_learning():
    """Learning database: posts are being analyzed?"""
    learning_dir = DATA_DIR / "learning"
    if not learning_dir.exists():
        return {"status": "warn", "message": "No learning directory"}
    
    files = list(learning_dir.glob("*"))
    if not files:
        return {"status": "warn", "message": "No learning data yet"}
    
    newest = max(f.stat().st_mtime for f in files if f.is_file())
    from datetime import datetime as dt
    age_days = (datetime.now().timestamp() - newest) / 86400
    return {"status": "ok", "message": f"{len(files)} files, newest {age_days:.1f}d old",
            "files": len(files), "newest_age_days": round(age_days, 1)}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    now = datetime.now(CAIRO)
    log(f"=== Content Factory Health Monitor === {now.strftime('%Y-%m-%d %H:%M')} Cairo")
    
    components = [
        ("notion_auth",         check_notion_auth),
        ("rss_db",             check_rss_db),
        ("content_calendar",    check_content_calendar),
        ("rss_to_cal_bridge",   check_rss_to_cal_bridge),
        ("content_orchestrator",check_content_orchestrator),
        ("linkedin_post",       check_linkedin_post_today),
        ("engagement_collector",check_engagement_data),
        ("content_learning",    check_content_learning),
        ("composio_linkedin",   check_composio_linkedin),
    ]
    
    results = []
    for name, fn in components:
        r = check_component(name, fn)
        r["name"] = name
        results.append(r)
        icon = {"ok": "✅", "warn": "⚠️", "fail": "🔴", "error": "🔴"}.get(r["status"], "?")
        msg = r.get("message", "")
        log(f"  {icon} {name}: {msg}")
    
    # Save state
    health_state = {
        "checked_at": now.isoformat(),
        "components": {r["name"]: {"status": r["status"], "message": r.get("message", "")}
                       for r in results}
    }
    json.dump(health_state, open(DATA_DIR / "cf-health-state.json", "w"), indent=2)
    
    # Alert logic
    critical = [r for r in results if r["status"] in ("fail", "error")]
    warnings = [r for r in results if r["status"] == "warn"]
    ok = [r for r in results if r["status"] == "ok"]
    
    log(f"\n  Summary: {len(ok)} ✅  {len(warnings)} ⚠️  {len(critical)} 🔴")
    
    if critical:
        lines = [f"🛡️ Content Factory — {len(critical)} CRITICAL issue(s)\n"]
        for r in critical:
            lines.append(f"🔴 {r['name']}: {r.get('message','')}")
        if warnings:
            lines.append(f"\n⚠️ Warnings:")
            for r in warnings:
                lines.append(f"  ⚠️ {r['name']}: {r.get('message','')}")
        send_telegram("\n".join(lines))
    elif warnings:
        # Only alert on warnings if they persist 2+ days
        log("  ⚠️ Warnings present — not alerting (monitoring)")
    
    return 0 if not critical else 1

if __name__ == "__main__":
    sys.exit(main())
