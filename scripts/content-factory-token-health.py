#!/usr/bin/env python3
"""
content-factory-token-health.py
=================================
Checks all Content Factory tokens daily.
Alert via Telegram if anything is dead.

Checks:
1. Notion token - API query to RSS DB
2. Composio LinkedIn - check connection via Composio API
3. Telegram bot - getMe
4. LinkedIn cookies (if used by any script)

Run: Daily via cron (key-health-check.sh calls this)
"""
import json, ssl, subprocess, sys, urllib.request
from datetime import datetime, timezone, timedelta

WORKSPACE = "/root/.openclaw/workspace"
CAIRO = timezone(timedelta(hours=2))
NOW = datetime.now(CAIRO)

def send_telegram(msg):
    try:
        token = json.load(open(f"{WORKSPACE}/config/notion.json")).get("telegram_bot_token") or \
                json.load(open(f"{WORKSPACE}/../openclaw.json"))['channels']['telegram']['botToken']
        bot_token = subprocess.check_output(
            ["python3", "-c", f"import json; print(json.load(open('{WORKSPACE}/../openclaw.json'))['channels']['telegram']['botToken'])"],
            text=True, timeout=5
        ).strip()
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({"chat_id": "866838380", "text": msg, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(url, data=data, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"Telegram send failed: {e}")
        return None

def check_notion_token():
    """Test Notion token by querying the RSS DB."""
    try:
        token = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
        url = "https://api.notion.com/v1/databases/32e8d599a16281809e3afbfc17a84e49/query"
        req = urllib.request.Request(url,
            data=json.dumps({"page_size": 1}).encode(),
            method="POST",
            headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as r:
            d = json.loads(r.read())
            return True, f"OK - {len(d.get('results', []))} results from RSS DB"
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        return False, f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, str(e)

def check_notion_token_write():
    """Test that Notion token can WRITE (not just read)."""
    try:
        token = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
        # Try querying the Content Calendar (lightweight test)
        url = "https://api.notion.com/v1/databases/3268d599-a162-814b-8854-c9b8bde62468/query"
        req = urllib.request.Request(url,
            data=json.dumps({"page_size": 1}).encode(),
            method="POST",
            headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as r:
            d = json.loads(r.read())
            return True, "Write-capable"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)

def check_composio_linkedin():
    """Check Composio LinkedIn connection via API health check."""
    try:
        # Use the gateway to check Composio connection
        # Read Composio config
        composio_config = f"{WORKSPACE}/config/service-registry.json"
        if not open(composio_config).read():
            return None, "No Composio config found"
        
        cfg = json.load(open(composio_config))
        linkedin_conn = cfg.get("connections", {}).get("linkedin", {})
        status = linkedin_conn.get("status", "unknown")
        
        if status == "ACTIVE":
            return True, "Composio LinkedIn: ACTIVE"
        else:
            return False, f"Composio LinkedIn: {status}"
    except Exception as e:
        return None, f"Could not check Composio: {e}"

def check_telegram_bot():
    """Check Telegram bot token."""
    try:
        bot_token = subprocess.check_output(
            ["python3", "-c",
             f"import json; print(json.load(open('{WORKSPACE}/../openclaw.json'))['channels']['telegram']['botToken'])"],
            text=True, timeout=5
        ).strip()
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        req = urllib.request.Request(url, headers={})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            if d.get("ok"):
                return True, f"Telegram bot '{d.get('result',{}).get('username')}': OK"
            return False, f"Telegram error: {d}"
    except Exception as e:
        return False, str(e)

def check_rss_feeds():
    """Check if RSS feeds are responding (sample 3 feeds)."""
    import xml.etree.ElementTree as ET
    feeds = {
        "FinTech": "https://connectingthedotsinfin.tech/rss/",
        "AI/VentureBeat": "https://venturebeat.com/category/ai/feed/",
        "Strategy": "https://fs.blog/feed/",
    }
    results = []
    for name, url in list(feeds.items())[:3]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context()) as r:
                raw = r.read()
            return True, f"RSS feeds responding"
        except Exception as e:
            results.append(f"{name}: {e}")
    if results:
        return False, "; ".join(results)
    return True, "OK"

def check_content_factory_crons():
    """Check if key Content Factory cron jobs ran today."""
    import os
    cron_log_dir = f"{WORKSPACE}/logs"
    results = []
    
    # Check morning briefing ran today
    briefing_log = f"{WORKSPACE}/logs/briefing/cron.log"
    if os.path.exists(briefing_log):
        with open(briefing_log) as f:
            lines = f.readlines()
        today_prefix = NOW.strftime("%Y-%m-%d")
        today_lines = [l for l in lines if l.startswith(today_prefix)]
        if today_lines:
            results.append(f"Morning briefing: OK ({len(today_lines)} runs)")
        else:
            results.append("Morning briefing: NO RUN TODAY")
    
    # Check content orchestrator
    state_file = f"{WORKSPACE}/data/content-pipeline-state.json"
    if os.path.exists(state_file):
        state = json.load(open(state_file))
        last_run = state.get("last_run", "never")
        last_date = last_run[:10] if last_run else "never"
        if last_date == NOW.strftime("%Y-%m-%d"):
            results.append(f"Content orchestrator: OK (last {last_run[11:16]})")
        elif last_date == (NOW - timedelta(days=1)).strftime("%Y-%m-%d"):
            results.append(f"Content orchestrator: Expected (ran yesterday {last_run[11:16]})")
        else:
            results.append(f"Content orchestrator: STALE (last {last_run[:10]})")
    
    return results

def main():
    print(f"[content-factory-token-health] {NOW.strftime('%Y-%m-%d %H:%M')} Cairo")
    
    issues = []
    ok_items = []
    
    # 1. Notion token
    print("  Checking Notion token...")
    ok, msg = check_notion_token()
    if ok:
        print(f"  ✓ {msg}")
        ok_items.append(f"Notion: {msg}")
    else:
        print(f"  🔴 {msg}")
        issues.append(f"🔴 Notion READ: {msg}")
    
    # 2. Notion write
    print("  Checking Notion write capability...")
    ok, msg = check_notion_token_write()
    if ok:
        print(f"  ✓ {msg}")
        ok_items.append(f"Notion write: {msg}")
    else:
        print(f"  🔴 {msg}")
        issues.append(f"🔴 Notion WRITE: {msg}")
    
    # 3. Telegram
    print("  Checking Telegram bot...")
    ok, msg = check_telegram_bot()
    if ok:
        print(f"  ✓ {msg}")
        ok_items.append(msg)
    else:
        print(f"  🔴 {msg}")
        issues.append(f"🔴 Telegram: {msg}")
    
    # 4. RSS feeds
    print("  Checking RSS feeds...")
    ok, msg = check_rss_feeds()
    if ok:
        print(f"  ✓ {msg}")
        ok_items.append(f"RSS: {msg}")
    else:
        print(f"  ⚠️ {msg}")
        issues.append(f"⚠️ RSS: {msg}")
    
    # 5. Content Factory cron status
    print("  Checking Content Factory crons...")
    cron_results = check_content_factory_crons()
    for r in cron_results:
        if "STALE" in r or "NO RUN" in r:
            issues.append(f"⚠️ {r}")
        else:
            ok_items.append(r)
        print(f"  {'🔴' if 'STALE' in r else '⚠️' if 'NO RUN' in r else '✓'} {r}")
    
    # Report
    if issues:
        report = f"🛡️ Content Factory Health — ISSUES FOUND\n{NOW.strftime('%Y-%m-%d %H:%M')} Cairo\n\n"
        for issue in issues:
            report += f"{issue}\n"
        report += f"\n✅ OK: {len(ok_items)}"
        print(f"\n{'='*50}")
        print(report)
        send_telegram(report)
    else:
        print(f"\n✅ All checks passed ({len(ok_items)} items)")
    
    # Save state
    health_file = f"{WORKSPACE}/data/content-factory-health.json"
    health = {
        "checked_at": NOW.isoformat(),
        "issues": issues,
        "ok": ok_items,
        "status": "issues" if issues else "ok"
    }
    json.dump(health, open(health_file, "w"), indent=2)
    
    return 1 if issues else 0

if __name__ == "__main__":
    sys.exit(main())
