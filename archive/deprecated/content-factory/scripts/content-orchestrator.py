#!/usr/bin/env python3
"""
content-orchestrator.py — Single daily cron that coordinates the content pipeline.

Sequence: PRIME (pre-post comments) -> PUBLISH (auto-poster) -> ENGAGE (monitor) -> COLLECT (scrape engagement)

Each step checks the previous step's output before proceeding.
State persisted in data/content-pipeline-state.json.

Usage:
  python3 content-orchestrator.py                # Full daily pipeline
  python3 content-orchestrator.py --step prime    # Run one step only
  python3 content-orchestrator.py --step publish
  python3 content-orchestrator.py --step engage
  python3 content-orchestrator.py --step collect
  python3 content-orchestrator.py --dry-run       # No side effects
"""

import json, os, sys, subprocess, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
SCRIPTS_DIR = WORKSPACE / "scripts"
STATE_FILE = DATA_DIR / "content-pipeline-state.json"
POSTS_REGISTRY = DATA_DIR / "linkedin-posts.json"
WATCHDOG_FILE = DATA_DIR / "linkedin-watchdog.json"
COMMENT_RADAR_OUTPUT = DATA_DIR / "comment-radar.json"

CAIRO = timezone(timedelta(hours=2))

DRY_RUN = "--dry-run" in sys.argv
STEP_ONLY = None
if "--step" in sys.argv:
    idx = sys.argv.index("--step")
    if idx + 1 < len(sys.argv):
        STEP_ONLY = sys.argv[idx + 1]


def now_cairo():
    return datetime.now(CAIRO)


def log(msg):
    print(f"[orchestrator] {msg}")


def load_state():
    """Load pipeline state."""
    if STATE_FILE.exists():
        try:
            return json.load(open(STATE_FILE))
        except:
            pass
    return {}


def save_state(state):
    """Save pipeline state."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(state, open(STATE_FILE, "w"), indent=2)


def run_script(script_name, args=None, timeout_sec=300):
    """Run a Python script and return (success, output)."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)]
    if args:
        cmd.extend(args)
    
    log(f"  Running {script_name}...")
    
    if DRY_RUN:
        log(f"  [DRY RUN] Would run: {' '.join(cmd)}")
        return True, "[dry run]"
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_sec,
            cwd=str(WORKSPACE)
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            log(f"  FAILED (exit {result.returncode}): {output[-500:]}")
            return False, output
        return True, output
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT after {timeout_sec}s")
        return False, "timeout"
    except Exception as e:
        log(f"  ERROR: {e}")
        return False, str(e)


def step_prime(state):
    """Step 1: Pre-post priming — run comment radar, find posts to engage with."""
    log("=== STEP 1: PRIME (Pre-post comment radar) ===")
    
    success, output = run_script("comment-radar-agent.py", timeout_sec=180)
    
    if success and COMMENT_RADAR_OUTPUT.exists():
        try:
            radar = json.load(open(COMMENT_RADAR_OUTPUT))
            posts_found = radar.get("posts_found", 0)
            comments_drafted = radar.get("comments_drafted", 0)
            log(f"  Radar: {posts_found} posts found, {comments_drafted} comments drafted")
            state["last_primed_at"] = now_cairo().isoformat()
            state["prime_status"] = "ok"
            state["prime_comments_drafted"] = comments_drafted
        except:
            state["prime_status"] = "parse_error"
    else:
        state["prime_status"] = "failed"
        log("  WARNING: Comment radar failed. Continuing to publish step.")
    
    return state


def step_publish(state):
    """Step 2: Publish — run auto-poster."""
    log("=== STEP 2: PUBLISH (Auto-poster) ===")
    
    success, output = run_script("linkedin-auto-poster.py", timeout_sec=300)
    
    if success:
        # Check watchdog for post result
        if WATCHDOG_FILE.exists():
            try:
                watchdog = json.load(open(WATCHDOG_FILE))
                today = now_cairo().strftime("%Y-%m-%d")
                if watchdog.get("date") == today and watchdog.get("post_url"):
                    state["today_post_url"] = watchdog["post_url"]
                    state["today_post_score"] = watchdog.get("score", 0)
                    state["posted_at"] = now_cairo().isoformat()
                    state["publish_status"] = "posted"
                    log(f"  Posted: {watchdog['post_url']}")
                    
                    # Register post for reaction tracker
                    register_post_for_tracking(watchdog)
                    return state
                elif watchdog.get("date") == today:
                    state["publish_status"] = "attempted_no_url"
                    log("  WARNING: Auto-poster ran but no post URL in watchdog")
            except:
                pass
        
        state["publish_status"] = "completed_no_watchdog"
        log("  Auto-poster completed but no watchdog data found")
    else:
        state["publish_status"] = "failed"
        log("  Auto-poster FAILED")
    
    return state


def register_post_for_tracking(watchdog):
    """Register today's post in linkedin-posts.json for reaction tracker."""
    try:
        registry = json.load(open(POSTS_REGISTRY)) if POSTS_REGISTRY.exists() else {"posts": []}
    except:
        registry = {"posts": []}
    
    post_url = watchdog.get("post_url", "")
    
    # Extract activity ID from URL
    import re
    m = re.search(r'activity[/-](\d+)', post_url)
    activity_id = m.group(1) if m else ""
    
    if not activity_id:
        log("  WARNING: Could not extract activity ID from post URL")
        return
    
    # Check if already registered
    existing_ids = {p.get("activity_id") for p in registry["posts"]}
    if activity_id in existing_ids:
        log(f"  Post {activity_id} already registered")
        return
    
    registry["posts"].append({
        "activity_urn": f"urn:li:activity:{activity_id}",
        "activity_id": activity_id,
        "title": watchdog.get("title", "")[:50],
        "post_url": post_url,
        "published_at": now_cairo().isoformat(),
        "registered_at": now_cairo().isoformat(),
        "score": watchdog.get("score", 0),
    })
    
    if not DRY_RUN:
        json.dump(registry, open(POSTS_REGISTRY, "w"), indent=2)
        log(f"  Registered post {activity_id} for reaction tracking")


def step_engage(state):
    """Step 3: Engagement window — monitor our post's early performance."""
    log("=== STEP 3: ENGAGE (60-min engagement window) ===")
    
    post_url = state.get("today_post_url")
    if not post_url:
        log("  No post published today. Skipping engagement window.")
        state["engage_status"] = "skipped_no_post"
        return state
    
    posted_at = state.get("posted_at", "")
    if posted_at:
        try:
            post_time = datetime.fromisoformat(posted_at)
            minutes_since = (now_cairo() - post_time).total_seconds() / 60
            if minutes_since < 55:
                log(f"  Post is only {minutes_since:.0f}m old. Engagement window still open.")
                state["engage_status"] = "window_open"
                state["engage_minutes_since_post"] = round(minutes_since)
                return state
        except:
            pass
    
    state["engage_status"] = "monitored"
    state["engagement_window_closed"] = now_cairo().isoformat()
    log("  Engagement window closed. Collection will capture metrics.")
    
    return state


def step_collect(state):
    """Step 4: Collect engagement data via scraper."""
    log("=== STEP 4: COLLECT (Engagement metrics) ===")
    
    success, output = run_script("linkedin-engagement-collector.py", timeout_sec=120)
    
    if success:
        state["last_collected_at"] = now_cairo().isoformat()
        state["collect_status"] = "ok"
        log("  Collection complete")
    else:
        state["collect_status"] = "failed"
        log("  Collection failed. Will retry next cycle.")
    
    return state


def send_telegram_alert(message):
    """Send alert via OpenClaw gateway."""
    if DRY_RUN:
        log(f"  [DRY RUN] Telegram: {message}")
        return
    # Use openclaw announce which sends to last active channel
    try:
        subprocess.run(
            ["openclaw", "announce", message],
            capture_output=True, timeout=15
        )
    except:
        log("  WARNING: Could not send Telegram alert")


def main():
    now = now_cairo()
    today = now.strftime("%Y-%m-%d")
    
    log(f"=== Content Orchestrator ===")
    log(f"Time: {now.strftime('%Y-%m-%d %H:%M')} Cairo")
    log(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    if STEP_ONLY:
        log(f"Step: {STEP_ONLY} only")
    
    state = load_state()
    
    # Reset state if new day
    if state.get("date") != today:
        state = {"date": today, "started_at": now.isoformat()}
    
    steps = {
        "prime": step_prime,
        "publish": step_publish,
        "engage": step_engage,
        "collect": step_collect,
    }
    
    if STEP_ONLY:
        if STEP_ONLY in steps:
            state = steps[STEP_ONLY](state)
        else:
            log(f"  Unknown step: {STEP_ONLY}. Valid: {', '.join(steps.keys())}")
            sys.exit(1)
    else:
        # Full pipeline
        for step_name, step_func in steps.items():
            state = step_func(state)
            save_state(state)
            time.sleep(2)  # Brief pause between steps
    
    state["last_run"] = now.isoformat()
    save_state(state)
    
    # Summary
    log(f"\n=== Pipeline Summary ===")
    log(f"  Prime: {state.get('prime_status', 'not_run')}")
    log(f"  Publish: {state.get('publish_status', 'not_run')}")
    log(f"  Engage: {state.get('engage_status', 'not_run')}")
    log(f"  Collect: {state.get('collect_status', 'not_run')}")
    
    if state.get("today_post_url"):
        log(f"  Post URL: {state['today_post_url']}")


if __name__ == "__main__":
    main()
