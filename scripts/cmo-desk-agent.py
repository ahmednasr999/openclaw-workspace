#!/usr/bin/env python3
"""
cmo-desk-agent.py — CMO Desk Agent
Persistent agent loop for the CMO Agent skill.

Responsibilities:
- Monitor Telegram topic 7 (-1003882622947:7) for Ahmed's content requests
- Post weekly batch summary every Friday
- Monitor content calendar gaps and alert CEO
- Always loop in CEO when Ahmed messages directly or posting fails

Usage:
    python3 cmo-desk-agent.py [--dry-run] [--once]
"""

import os
import sys
import json
import time
import datetime
import argparse
import subprocess
import logging
from pathlib import Path

# ─── Config ────────────────────────────────────────────────────────────────────

WORKSPACE = Path("/root/.openclaw/workspace")
LOG_DIR = WORKSPACE / "logs"
DATA_DIR = WORKSPACE / "data"
SCRIPTS_DIR = WORKSPACE / "scripts"
NOTION_DB_ID = "3268d599-a162-814b-8854-c9b8bde62468"

TELEGRAM_CHAT_ID = "-1003882622947"
TELEGRAM_TOPIC_ID = "7"        # CMO Desk
CEO_DM_CHAT_ID = "866838380"  # Ahmed's personal DM (also CEO inbox)

# Polling interval (seconds) for main loop
POLL_INTERVAL = 60

# ─── Logging ────────────────────────────────────────────────────────────────────

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CMO] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "cmo-desk-agent.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("cmo-desk-agent")

# ─── Helpers ────────────────────────────────────────────────────────────────────

def run_script(script_name: str, args: list[str] = []) -> tuple[str, int]:
    """Run a script from SCRIPTS_DIR, return (output, returncode)."""
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(WORKSPACE))
    output = result.stdout + result.stderr
    return output, result.returncode


def send_telegram(chat_id: str, text: str, thread_id: str = None, dry_run: bool = False) -> bool:
    """Send a Telegram message via openclaw message tool (shell wrapper)."""
    if dry_run:
        target = f"{chat_id}:{thread_id}" if thread_id else chat_id
        log.info(f"[DRY RUN] → Telegram {target}: {text[:100]}...")
        return True

    cmd = ["openclaw", "message", "send", "--channel", "telegram",
           "--target", chat_id, "--message", text]
    if thread_id:
        cmd += ["--thread-id", thread_id]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"Failed to send Telegram message: {result.stderr}")
        return False
    return True


def sessions_send_to_ceo(message: str, dry_run: bool = False) -> bool:
    """Loop in the main NASR session (CEO) via sessions_send."""
    if dry_run:
        log.info(f"[DRY RUN] → sessions_send to CEO: {message[:100]}...")
        return True

    cmd = ["openclaw", "sessions", "send", "--target", "main", "--message", message]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback: send via Telegram DM to CEO
        log.warning(f"sessions_send failed, falling back to Telegram DM: {result.stderr}")
        return send_telegram(CEO_DM_CHAT_ID, f"[CMO→CEO] {message}", dry_run=dry_run)
    return True


def get_notion_scheduled_posts(days_ahead: int = 5) -> list[dict]:
    """Query Notion for Scheduled posts in the next N days."""
    output, code = run_script("notion-query.py", [
        "--db", NOTION_DB_ID,
        "--filter", f'{{"status": "Scheduled", "days_ahead": {days_ahead}}}'
    ])
    if code != 0:
        log.warning(f"notion-query.py failed: {output}")
        return []
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        log.warning(f"Could not parse notion-query output: {output[:200]}")
        return []


def get_pending_engagement() -> list[dict]:
    """Load pending engagement approvals."""
    pending_file = DATA_DIR / "linkedin-engagement-pending.json"
    if not pending_file.exists():
        return []
    try:
        with open(pending_file) as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"Could not read pending engagement: {e}")
        return []


# ─── Core Checks ────────────────────────────────────────────────────────────────

def check_calendar_gaps(dry_run: bool = False) -> bool:
    """
    Check for content calendar gaps.
    Returns True if a gap was detected (and alert sent).
    """
    scheduled = get_notion_scheduled_posts(days_ahead=5)

    if len(scheduled) == 0:
        alert = (
            "⚠️ *Content gap detected!*\n"
            "No posts scheduled for the next 5 business days.\n\n"
            "Action needed: Move at least 3 posts from Draft/Ideas → Scheduled in Notion.\n"
            f"Notion DB: https://notion.so/{NOTION_DB_ID}"
        )
        log.warning("Calendar gap detected — alerting CEO")
        send_telegram(TELEGRAM_CHAT_ID, alert, thread_id=TELEGRAM_TOPIC_ID, dry_run=dry_run)
        sessions_send_to_ceo(alert, dry_run=dry_run)
        return True

    # Check streak: need ≥3 posts/week Sun–Thu
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())  # Monday
    week_posts = [
        p for p in scheduled
        if p.get("planned_date") and week_start <= datetime.date.fromisoformat(p["planned_date"]) <= week_start + datetime.timedelta(days=4)
    ]
    if len(week_posts) < 3:
        alert = (
            f"⚠️ *Streak risk:* Only {len(week_posts)} post(s) scheduled this week.\n"
            "Target: 3+ posts Sun–Thu for GCC executive visibility.\n"
            "Please move content from Ideas/Draft → Scheduled."
        )
        log.warning(f"Streak risk: {len(week_posts)}/3 posts this week")
        send_telegram(TELEGRAM_CHAT_ID, alert, thread_id=TELEGRAM_TOPIC_ID, dry_run=dry_run)
        sessions_send_to_ceo(alert, dry_run=dry_run)
        return True

    log.info(f"Calendar OK: {len(scheduled)} posts scheduled in next 5 days")
    return False


def run_friday_batch(dry_run: bool = False):
    """Generate next week's content batch (every Friday)."""
    log.info("Friday batch: generating next week's content ideas...")
    output, code = run_script("content-batch-generator.py", ["--dry-run"] if dry_run else [])

    if code != 0:
        error_msg = (
            "❌ *Friday batch failed*\n"
            f"Error: {output[:300]}\n"
            "Please run manually: `python3 scripts/content-batch-generator.py`"
        )
        send_telegram(TELEGRAM_CHAT_ID, error_msg, thread_id=TELEGRAM_TOPIC_ID, dry_run=dry_run)
        sessions_send_to_ceo(f"CMO Friday batch failed: {output[:200]}", dry_run=dry_run)
        return

    success_msg = (
        "📅 *Next week's content batch is ready!*\n\n"
        f"{output[:800]}\n\n"
        "Review in Notion and move any post to *Scheduled* to approve for auto-posting."
    )
    send_telegram(TELEGRAM_CHAT_ID, success_msg, thread_id=TELEGRAM_TOPIC_ID, dry_run=dry_run)
    sessions_send_to_ceo(f"CMO Friday batch complete:\n{output[:500]}", dry_run=dry_run)
    log.info("Friday batch complete")


def check_stale_posts(dry_run: bool = False):
    """Alert CEO if any Scheduled post is >48h past its Planned Date."""
    output, code = run_script("notion-query.py", [
        "--db", NOTION_DB_ID,
        "--filter", '{"status": "Scheduled", "overdue_hours": 48}'
    ])
    if code != 0:
        return

    try:
        stale = json.loads(output)
    except Exception:
        return

    if stale:
        titles = ", ".join(p.get("title", "Untitled") for p in stale)
        alert = (
            f"⚠️ *Stale posts detected:* {len(stale)} post(s) missed their scheduled date.\n"
            f"Posts: {titles}\n\n"
            "These have been rescheduled to the next business day. Please verify."
        )
        log.warning(f"Stale posts: {titles}")
        send_telegram(CEO_DM_CHAT_ID, alert, dry_run=dry_run)
        sessions_send_to_ceo(alert, dry_run=dry_run)


def check_engagement_queue(dry_run: bool = False):
    """Nudge CEO if engagement approval queue has been sitting >3 days."""
    pending = get_pending_engagement()
    if not pending:
        return

    old_pending = []
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=3)
    for item in pending:
        sent_at = item.get("sent_for_approval_at")
        if sent_at:
            try:
                sent_dt = datetime.datetime.fromisoformat(sent_at)
                if sent_dt < cutoff:
                    old_pending.append(item)
            except Exception:
                pass

    if len(old_pending) >= 3:
        alert = (
            f"👋 Reminder: {len(pending)} comment(s) waiting for your approval.\n"
            f"{len(old_pending)} have been waiting 3+ days.\n"
            "Check your DMs for the approval buttons."
        )
        log.info(f"Nudging CEO: {len(pending)} pending engagement items")
        send_telegram(CEO_DM_CHAT_ID, alert, dry_run=dry_run)


# ─── Message Monitoring ────────────────────────────────────────────────────────

def handle_ahmed_message(message: str, dry_run: bool = False):
    """
    Handle a direct message from Ahmed to CMO thread.
    ALWAYS loop in CEO.
    """
    log.info(f"Ahmed messaged CMO directly: {message[:100]}")

    # Loop in CEO immediately
    ceo_notice = (
        f"📨 Ahmed messaged CMO directly (topic 7):\n"
        f"\"{message}\"\n\n"
        f"CMO is handling this. Will report back."
    )
    sessions_send_to_ceo(ceo_notice, dry_run=dry_run)

    # Acknowledge Ahmed in topic 7
    ack = "Got it, Ahmed. On it — I'll loop in NASR and report back."
    send_telegram(TELEGRAM_CHAT_ID, ack, thread_id=TELEGRAM_TOPIC_ID, dry_run=dry_run)

    # Route to appropriate handler based on message content
    msg_lower = message.lower()
    if any(word in msg_lower for word in ["batch", "next week", "ideas", "content for"]):
        run_friday_batch(dry_run=dry_run)
    elif any(word in msg_lower for word in ["gap", "scheduled", "calendar", "what's coming"]):
        check_calendar_gaps(dry_run=dry_run)
    elif any(word in msg_lower for word in ["post", "publish", "linkedin"]):
        # Notify CEO that manual posting request needs attention
        sessions_send_to_ceo(
            f"Ahmed wants to post to LinkedIn: \"{message}\"\n"
            "Please clarify the post content or I'll prepare a draft.",
            dry_run=dry_run
        )
    else:
        # Generic — let CEO handle
        sessions_send_to_ceo(
            f"Ahmed's CMO request needs your input: \"{message}\"",
            dry_run=dry_run
        )


def poll_telegram_topic(last_message_id: int, dry_run: bool = False) -> int:
    """Poll topic 7 for new messages. Returns new last_message_id."""
    # This uses openclaw CLI to check recent messages in the topic
    cmd = [
        "openclaw", "message", "poll",
        "--channel", "telegram",
        "--target", TELEGRAM_CHAT_ID,
        "--thread-id", TELEGRAM_TOPIC_ID,
        "--since-id", str(last_message_id),
        "--format", "json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return last_message_id

    try:
        messages = json.loads(result.stdout)
        if not messages:
            return last_message_id

        for msg in messages:
            sender = msg.get("from", {}).get("username", "")
            text = msg.get("text", "")
            msg_id = msg.get("message_id", last_message_id)

            # Only react to messages from Ahmed (not bot's own messages)
            if sender in ("Ahmed_Nasr", "ahmednasr") and text:
                handle_ahmed_message(text, dry_run=dry_run)

            last_message_id = max(last_message_id, msg_id)

        return last_message_id
    except Exception as e:
        log.warning(f"Error polling Telegram: {e}")
        return last_message_id


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CMO Desk Agent")
    parser.add_argument("--dry-run", action="store_true", help="No real sends; log only")
    parser.add_argument("--once", action="store_true", help="Run checks once and exit")
    args = parser.parse_args()

    log.info("CMO Desk Agent starting up...")
    if args.dry_run:
        log.info("DRY RUN mode — no real Telegram/LinkedIn/Notion writes")

    last_message_id = 0
    last_friday_batch = None
    last_gap_check = None
    last_stale_check = None
    last_engagement_nudge = None

    while True:
        now = datetime.datetime.now()
        today = now.date()
        is_friday = now.weekday() == 4  # Friday = 4

        try:
            # ── Calendar gap check (daily at 8 AM or on startup) ──────────────
            if last_gap_check != today and now.hour >= 8:
                check_calendar_gaps(dry_run=args.dry_run)
                check_stale_posts(dry_run=args.dry_run)
                last_gap_check = today
                last_stale_check = today

            # ── Friday batch (once per Friday, 9 AM) ─────────────────────────
            if is_friday and last_friday_batch != today and now.hour >= 9:
                run_friday_batch(dry_run=args.dry_run)
                last_friday_batch = today

            # ── Engagement queue nudge (daily) ────────────────────────────────
            if last_engagement_nudge != today and now.hour >= 10:
                check_engagement_queue(dry_run=args.dry_run)
                last_engagement_nudge = today

            # ── Poll Telegram topic 7 for Ahmed messages ──────────────────────
            last_message_id = poll_telegram_topic(last_message_id, dry_run=args.dry_run)

        except KeyboardInterrupt:
            log.info("CMO Desk Agent stopped by user")
            break
        except Exception as e:
            log.error(f"Unexpected error in main loop: {e}", exc_info=True)
            sessions_send_to_ceo(
                f"⚠️ CMO Desk Agent error: {str(e)[:200]}",
                dry_run=args.dry_run
            )

        if args.once:
            log.info("--once flag set, exiting after first run")
            break

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
