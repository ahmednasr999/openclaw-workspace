#!/usr/bin/env python3
"""
CTO Desk Agent
--------------
Persistent agent loop for the CTO Agent persona.

Responsibilities:
  - Post daily standup to Telegram topic 8 (-1003882622947:8) at 8:30 AM Cairo Sun-Thu
  - Include gateway status + cron health + open issues in standup
  - Monitor topic 8 for Ahmed's messages and respond
  - Loop in CEO (main session) via sessions_send for system-wide issues or direct messages

Usage:
  python3 cto-desk-agent.py            # Run persistent loop
  python3 cto-desk-agent.py --standup  # Post standup now and exit
  python3 cto-desk-agent.py --status   # Print system status and exit
  python3 cto-desk-agent.py --dry-run  # Simulate without sending
"""

import os
import sys
import json
import time
import subprocess
import datetime
import argparse
import logging
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPTS_DIR = WORKSPACE / "scripts"
LOGS_DIR = WORKSPACE / "logs"
LOG_FILE = LOGS_DIR / "cto-desk-agent.log"

# Telegram
TELEGRAM_CHAT_ID = "-1003882622947"
TELEGRAM_TOPIC_ID = "8"          # CTO Desk thread

# CEO main session (for escalations and loop-ins)
CEO_SESSION = "agent:main:telegram:direct:866838380"

# Cron dashboard script
CRON_UPDATER = SCRIPTS_DIR / "cron-dashboard-updater.py"

# Gateway health endpoint
GATEWAY_URL = "http://localhost:18789/health"

# Operating days: Sun=6, Mon=0, Tue=1, Wed=2, Thu=3
WORK_DAYS = {0, 1, 2, 3, 6}   # Mon-Thu + Sun
STANDUP_HOUR = 8
STANDUP_MINUTE = 30

# Poll interval for incoming messages (seconds)
POLL_INTERVAL = 60

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("cto-desk-agent")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_cmd(cmd: str, timeout: int = 30) -> tuple[int, str]:
    """Run a shell command, return (returncode, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode, output
    except subprocess.TimeoutExpired:
        return 1, f"TIMEOUT after {timeout}s"
    except Exception as e:
        return 1, str(e)


def load_env() -> dict:
    """Load key=value pairs from ~/.env."""
    env_path = Path.home() / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def sessions_send(session_id: str, message: str, dry_run: bool = False) -> bool:
    """
    Send a message to another OpenClaw session via sessions_send CLI.
    Returns True on success.
    """
    if dry_run:
        log.info(f"[DRY-RUN] sessions_send → {session_id}: {message[:100]}...")
        return True
    cmd = f'openclaw sessions send "{session_id}" {json.dumps(message)}'
    rc, out = run_cmd(cmd, timeout=15)
    if rc != 0:
        log.error(f"sessions_send failed: {out}")
    return rc == 0


def send_telegram(message: str, dry_run: bool = False) -> bool:
    """
    Post a message to Telegram CTO Desk topic via openclaw message tool.
    Uses the Telegram bot token from ~/.env.
    """
    if dry_run:
        log.info(f"[DRY-RUN] Telegram → topic {TELEGRAM_TOPIC_ID}: {message[:120]}...")
        return True

    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        log.error("TELEGRAM_BOT_TOKEN not found in ~/.env")
        return False

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_thread_id": TELEGRAM_TOPIC_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    import urllib.request, urllib.error
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read())
            if resp_data.get("ok"):
                log.info("Telegram message sent OK")
                return True
            else:
                log.error(f"Telegram API error: {resp_data}")
                return False
    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return False


# ---------------------------------------------------------------------------
# System Health Checks
# ---------------------------------------------------------------------------

def check_gateway() -> dict:
    """Check if the OpenClaw gateway is healthy."""
    rc, out = run_cmd(f"curl -sf {GATEWAY_URL}", timeout=5)
    return {
        "name": "Gateway",
        "pass": rc == 0,
        "detail": out[:100] if out else "No response",
    }


def check_backup_recency() -> dict:
    """Check if a git push happened in the last 24 hours."""
    rc, out = run_cmd(
        f'cd {WORKSPACE} && git log --remotes=origin --since="24 hours ago" --oneline | head -3',
        timeout=10,
    )
    passed = rc == 0 and bool(out.strip())
    return {
        "name": "Backup (last 24h)",
        "pass": passed,
        "detail": out.strip()[:100] if out.strip() else "No recent remote commits",
    }


def check_no_staged_secrets() -> dict:
    """Warn if staged changes contain potential secrets."""
    rc, out = run_cmd(
        f'cd {WORKSPACE} && git diff --staged | grep -iE "(api_key|password|secret|token)" | head -5',
        timeout=10,
    )
    # grep exits 0 if found (bad), 1 if not found (good)
    clean = rc != 0 or not out.strip()
    return {
        "name": "No staged secrets",
        "pass": clean,
        "detail": "Clean" if clean else f"⚠️ Possible secrets: {out.strip()[:80]}",
    }


def check_cron_health() -> dict:
    """Run cron-dashboard-updater in dry-run mode and parse results."""
    if not CRON_UPDATER.exists():
        return {
            "name": "Cron health",
            "pass": False,
            "detail": f"Script not found: {CRON_UPDATER}",
        }
    rc, out = run_cmd(f"python3 {CRON_UPDATER} --dry-run", timeout=60)
    # Heuristic: look for ERROR or FAIL keywords
    lines = out.strip().splitlines() if out else []
    failures = [l for l in lines if any(k in l.upper() for k in ("ERROR", "FAIL", "TIMEOUT"))]
    passed = rc == 0 and not failures
    detail = "; ".join(failures[:3]) if failures else (lines[-1][:100] if lines else "OK")
    return {
        "name": "Cron health",
        "pass": passed,
        "detail": detail,
    }


def check_notion_api() -> dict:
    """Ping Notion API to verify connectivity and token validity."""
    env = load_env()
    token = env.get("NOTION_API_KEY", "")
    if not token:
        return {"name": "Notion API", "pass": False, "detail": "NOTION_API_KEY missing"}
    db_id = "3268d599-a162-8188-b531-e25071653203"
    rc, out = run_cmd(
        f'curl -sf -o /dev/null -w "%{{http_code}}" '
        f'-H "Authorization: Bearer {token}" '
        f'-H "Notion-Version: 2022-06-28" '
        f'"https://api.notion.com/v1/databases/{db_id}"',
        timeout=10,
    )
    http_code = out.strip()
    passed = http_code == "200"
    return {
        "name": "Notion API",
        "pass": passed,
        "detail": f"HTTP {http_code}",
    }


def run_all_checks() -> list[dict]:
    """Run all health checks and return results."""
    checks = [
        check_gateway,
        check_backup_recency,
        check_no_staged_secrets,
        check_cron_health,
        check_notion_api,
    ]
    results = []
    for fn in checks:
        try:
            results.append(fn())
        except Exception as e:
            results.append({"name": fn.__name__, "pass": False, "detail": str(e)})
    return results


# ---------------------------------------------------------------------------
# Standup Message Builder
# ---------------------------------------------------------------------------

def build_standup_message(checks: list[dict]) -> str:
    """Build the daily standup Markdown message."""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))
    date_str = now.strftime("%A %d %b %Y")

    pass_count = sum(1 for c in checks if c["pass"])
    total = len(checks)

    if pass_count == total:
        overall = "✅ All systems healthy"
    elif pass_count >= total - 1:
        overall = "⚠️ Mostly healthy — minor issue"
    else:
        overall = "🚨 Degraded — attention needed"

    lines = [
        f"*🤖 CTO Desk Standup — {date_str}*",
        f"_{overall} ({pass_count}/{total} checks passed)_",
        "",
        "*Health Checks:*",
    ]
    for c in checks:
        icon = "✅" if c["pass"] else "❌"
        lines.append(f"{icon} *{c['name']}* — {c['detail']}")

    # Open issues section
    failing = [c for c in checks if not c["pass"]]
    if failing:
        lines.append("")
        lines.append("*⚡ Open Issues:*")
        for c in failing:
            lines.append(f"• {c['name']}: {c['detail']}")
        lines.append("")
        lines.append("_CTO is investigating. Will update when resolved._")
    else:
        lines.append("")
        lines.append("_No open issues. Clean run. 💪_")

    lines.append("")
    lines.append("_Reply here with any technical questions or issues._")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------

def maybe_escalate(checks: list[dict], dry_run: bool = False) -> None:
    """If critical failures detected, loop in the CEO."""
    critical_names = {"Gateway", "Backup (last 24h)", "Cron health"}
    critical_failures = [c for c in checks if not c["pass"] and c["name"] in critical_names]

    if not critical_failures:
        return

    failure_summary = "\n".join(
        f"• {c['name']}: {c['detail']}" for c in critical_failures
    )
    msg = (
        f"🚨 CTO Alert: {len(critical_failures)} critical check(s) failing:\n"
        f"{failure_summary}\n\n"
        f"Investigating now. Will escalate if not resolved in 2h."
    )
    log.warning(f"Escalating to CEO: {len(critical_failures)} critical failures")
    sessions_send(CEO_SESSION, msg, dry_run=dry_run)


# ---------------------------------------------------------------------------
# Message Polling (Incoming from Ahmed)
# ---------------------------------------------------------------------------

def get_recent_topic_messages(token: str, offset: int = 0) -> list[dict]:
    """
    Fetch recent updates from the Telegram bot for topic 8.
    Returns list of message dicts.
    """
    import urllib.request
    url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=30&allowed_updates=[\"message\"]"
    try:
        with urllib.request.urlopen(url, timeout=35) as resp:
            data = json.loads(resp.read())
            if not data.get("ok"):
                return []
            updates = data.get("result", [])
            messages = []
            for update in updates:
                msg = update.get("message", {})
                if (
                    str(msg.get("chat", {}).get("id", "")) == TELEGRAM_CHAT_ID
                    and str(msg.get("message_thread_id", "")) == TELEGRAM_TOPIC_ID
                ):
                    messages.append({
                        "update_id": update["update_id"],
                        "text": msg.get("text", ""),
                        "from": msg.get("from", {}).get("first_name", "Unknown"),
                        "message_id": msg.get("message_id"),
                    })
            return messages
    except Exception as e:
        log.error(f"Failed to poll Telegram updates: {e}")
        return []


def handle_incoming_message(msg: dict, dry_run: bool = False) -> None:
    """
    Respond to an incoming message from Ahmed in topic 8.
    Also loops in the CEO session.
    """
    text = msg.get("text", "").strip()
    sender = msg.get("from", "Ahmed")
    log.info(f"Incoming message from {sender}: {text[:80]}")

    # Loop in CEO so main session stays in the loop
    ceo_msg = (
        f"📨 {sender} messaged CTO Desk (topic 8):\n"
        f"\"{text}\"\n\n"
        f"CTO Agent is responding."
    )
    sessions_send(CEO_SESSION, ceo_msg, dry_run=dry_run)

    # Build a simple response (the main session / LLM would do the heavy lifting in production)
    # For now, acknowledge and defer to CEO session
    response = (
        f"👋 Got your message, {sender}. Working on it.\n"
        f"I've looped in NASR (main session) for anything that needs deeper context.\n\n"
        f"_— CTO Desk Agent_"
    )
    if not dry_run:
        env = load_env()
        token = env.get("TELEGRAM_BOT_TOKEN", "")
        if token:
            send_telegram(response, dry_run=False)
    else:
        log.info(f"[DRY-RUN] Would respond: {response[:80]}")


# ---------------------------------------------------------------------------
# Standup Scheduler
# ---------------------------------------------------------------------------

def should_post_standup(last_posted: Optional[datetime.date]) -> bool:
    """Return True if we should post standup today (work day, not yet posted)."""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))
    if now.weekday() not in WORK_DAYS:
        return False
    if now.hour < STANDUP_HOUR or (now.hour == STANDUP_HOUR and now.minute < STANDUP_MINUTE):
        return False
    if last_posted == now.date():
        return False
    return True


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

def post_standup_now(dry_run: bool = False) -> None:
    """Run all checks, build standup message, send to topic 8, escalate if needed."""
    log.info("Running health checks for standup...")
    checks = run_all_checks()
    message = build_standup_message(checks)
    log.info("Posting standup to Telegram topic 8")
    send_telegram(message, dry_run=dry_run)
    maybe_escalate(checks, dry_run=dry_run)


def print_status() -> None:
    """Print current system status to stdout."""
    checks = run_all_checks()
    print("\n=== CTO Desk Agent — System Status ===\n")
    for c in checks:
        icon = "✅" if c["pass"] else "❌"
        print(f"  {icon} {c['name']}: {c['detail']}")
    print()
    pass_count = sum(1 for c in checks if c["pass"])
    print(f"  Score: {pass_count}/{len(checks)} checks passing")
    print()


def run_loop(dry_run: bool = False) -> None:
    """Persistent monitoring loop."""
    log.info("CTO Desk Agent starting persistent loop")
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "")

    last_standup_date: Optional[datetime.date] = None
    last_update_id = 0

    while True:
        try:
            # --- Standup check ---
            if should_post_standup(last_standup_date):
                log.info("Standup time — posting now")
                post_standup_now(dry_run=dry_run)
                last_standup_date = datetime.datetime.now(
                    datetime.timezone(datetime.timedelta(hours=2))
                ).date()

            # --- Poll for incoming messages ---
            if token:
                messages = get_recent_topic_messages(token, offset=last_update_id + 1)
                for msg in messages:
                    last_update_id = max(last_update_id, msg["update_id"])
                    if msg.get("text"):
                        handle_incoming_message(msg, dry_run=dry_run)
            else:
                if not dry_run:
                    log.warning("TELEGRAM_BOT_TOKEN not set — skipping message polling")

        except KeyboardInterrupt:
            log.info("CTO Desk Agent stopped by user")
            break
        except Exception as e:
            log.error(f"Loop error: {e}", exc_info=True)
            # Don't crash the loop on transient errors

        time.sleep(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="CTO Desk Agent")
    parser.add_argument("--standup", action="store_true", help="Post standup now and exit")
    parser.add_argument("--status", action="store_true", help="Print system status and exit")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without sending messages")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.standup:
        log.info("Manual standup trigger")
        post_standup_now(dry_run=args.dry_run)
        return

    # Default: persistent loop
    run_loop(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
