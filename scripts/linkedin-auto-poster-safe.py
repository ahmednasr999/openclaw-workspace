#!/usr/bin/env python3
"""
linkedin-auto-poster-safe.py
===============================
Idempotent wrapper for linkedin-auto-poster.py.

PROBLEM: If the auto-poster is killed mid-post (cron timeout, OOM, etc),
the watchdog file is left with no URL but the post may have gone live.
Next cron run would try to post again → duplicate.

SOLUTION: This wrapper checks state BEFORE running:
  1. Check if today already has a successful post (from watchdog + Notion)
  2. If yes → skip, log, and exit
  3. If no → run auto-poster normally

Also writes a PRE-FLIGHT lock to prevent double-runs.
"""
import json, os, subprocess, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPTS_DIR = WORKSPACE / "scripts"
DATA_DIR = WORKSPACE / "data"
LOCK_FILE = DATA_DIR / "linkedin-post.lock"
WATCHDOG_FILE = DATA_DIR / "linkedin-watchdog.json"
POSTS_REGISTRY = DATA_DIR / "linkedin-posts.json"
STATE_FILE = DATA_DIR / "linkedin-auto-poster-safe-state.json"

CAIRO = timezone(timedelta(hours=2))

NOTION_TOKEN = json.load(open(WORKSPACE / "config" / "notion.json"))["token"]
CAL_DB = "3268d599-a162-814b-8854-c9b8bde62468"  # Content Calendar

def now_cairo():
    return datetime.now(CAIRO)

def log(msg):
    print(f"[linkedin-poster-safe] {msg}")

def send_telegram(msg):
    try:
        bot_token = subprocess.check_output(
            ["python3", "-c",
             f"import json; print(json.load(open('{WORKSPACE}/../openclaw.json'))['channels']['telegram']['botToken'])"],
            text=True, timeout=5
        ).strip()
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({"chat_id": "866838380", "text": msg, "parse_mode": "HTML"}).encode()
        req = subprocess.Popen(["curl", "-sf", "-X", "POST", url,
                                "-d", f"chat_id=866838380", "-d", f"text={msg}"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        req.wait(timeout=10)
    except Exception as e:
        log(f"Telegram failed: {e}")

def check_already_posted_today():
    """Check if a post was already successfully made today."""
    today = now_cairo().strftime("%Y-%m-%d")
    
    # Check watchdog
    if WATCHDOG_FILE.exists():
        try:
            wd = json.load(open(WATCHDOG_FILE))
            if wd.get("date") == today and wd.get("post_url"):
                log(f"ALREADY POSTED today (watchdog): {wd.get('post_url')}")
                return True, wd.get("post_url")
        except:
            pass
    
    # Check posts registry
    if POSTS_REGISTRY.exists():
        try:
            reg = json.load(open(POSTS_REGISTRY))
            for post in reg.get("posts", []):
                pub_date = post.get("published_at", "")[:10]
                if pub_date == today and post.get("post_url"):
                    log(f"ALREADY POSTED today (registry): {post.get('post_url')}")
                    return True, post.get("post_url")
        except:
            pass
    
    # Check Content Calendar for Posted today
    try:
        import ssl, urllib.request
        body = {
            "filter": {
                "and": [
                    {"property": "Status", "select": {"equals": "Posted"}},
                    {"property": "Planned Date", "date": {"equals": today}}
                ]
            },
            "page_size": 5
        }
        req = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{CAL_DB}/query",
            data=json.dumps(body).encode(),
            method="POST",
            headers={"Authorization": f"Bearer {NOTION_TOKEN}",
                     "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as r:
            d = json.loads(r.read())
        if d.get("results"):
            post_url = ""
            for prop_name in ["Post URL", "Post URL"]:
                for page in d.get("results", []):
                    url = page.get("properties", {}).get(prop_name, {}).get("url", "")
                    if url:
                        post_url = url
                        break
            log(f"ALREADY POSTED today (Notion): {post_url or 'no URL recorded'}")
            return True, post_url
    except Exception as e:
        log(f"Notion check failed: {e}")
    
    return False, None

def acquire_lock():
    """Acquire a lock to prevent concurrent runs."""
    import socket
    lock_name = f"linkedin-poster-{os.getpid()}"
    
    if LOCK_FILE.exists():
        # Check if stale (older than 30 minutes)
        age = time.time() - os.path.getmtime(LOCK_FILE)
        if age < 1800:
            log(f"LOCK exists (age={age:.0f}s). Another run in progress. Exiting.")
            return False
        else:
            log(f"LOCK stale ({age:.0f}s old). Removing.")
            LOCK_FILE.unlink()
    
    with open(LOCK_FILE, "w") as f:
        f.write(json.dumps({
            "pid": os.getpid(),
            "started_at": now_cairo().isoformat(),
            "hostname": socket.gethostname()
        }))
    return True

def release_lock():
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()

def main():
    now = now_cairo()
    today = now.strftime("%Y-%m-%d")
    log(f"=== Safe LinkedIn Auto-Poster === {now.strftime('%Y-%m-%d %H:%M')} Cairo")
    
    # 1. Idempotency check
    already_posted, post_url = check_already_posted_today()
    if already_posted:
        log(f"STOPPED: Post already made today. No action taken.")
        return 0
    
    # 2. Acquire lock
    if not acquire_lock():
        return 1
    
    try:
        # 3. Run the actual auto-poster with a generous timeout
        log("Running linkedin-auto-poster.py...")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "linkedin-auto-poster.py")],
            capture_output=True, text=True,
            timeout=600,  # 10 minutes max
            cwd=str(WORKSPACE)
        )
        
        output = result.stdout + result.stderr
        
        # 4. Verify post was made
        time.sleep(5)  # Let watchdog file settle
        verified, verified_url = check_already_posted_today()
        
        if verified:
            log(f"✅ POST VERIFIED: {verified_url}")
            # Update state
            state = {"date": today, "posted": True, "post_url": verified_url,
                     "run_at": now.isoformat()}
            json.dump(state, open(STATE_FILE, "w"), indent=2)
            send_telegram(f"✅ LinkedIn post published\n{verified_url}")
        elif result.returncode == 0:
            # Script exited 0 but no URL - possible partial success
            log("⚠️ Auto-poster exited 0 but no URL verified. Flagging for review.")
            send_telegram("⚠️ LinkedIn auto-poster: exit 0 but URL not verified. Check manually.")
            state = {"date": today, "posted": "unverified", "exit_code": 0,
                     "run_at": now.isoformat(), "needs_review": True}
            json.dump(state, open(STATE_FILE, "w"), indent=2)
        else:
            log(f"❌ AUTO-POSTER FAILED (exit {result.returncode})")
            log(f"Output: {output[-500:]}")
            send_telegram(f"❌ LinkedIn auto-poster failed (exit {result.returncode})\n{output[-300:]}")
            state = {"date": today, "posted": False, "exit_code": result.returncode,
                     "error": output[-300:], "run_at": now.isoformat()}
            json.dump(state, open(STATE_FILE, "w"), indent=2)
            return 1
        
        return 0
        
    finally:
        release_lock()

if __name__ == "__main__":
    sys.exit(main())
