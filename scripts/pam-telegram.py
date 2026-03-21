#!/usr/bin/env python3
"""
Pam Telegram Sender — Pushes the daily Pam newsletter to Telegram.
Reads data/pam-newsletter.json and sends formatted message via OpenClaw CLI.

Usage:
  python3 pam-telegram.py              # Send full digest
  python3 pam-telegram.py --summary    # Short summary only
  python3 pam-telegram.py --dry-run    # Preview without sending
"""

import json, subprocess, sys, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
NEWSLETTER_FILE = WORKSPACE / "data/pam-newsletter.json"
TZ_OFFSET = 2
BOT_TOKEN = "8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304"
CHAT_ID = "866838380"

def load_newsletter():
    try:
        return json.load(open(NEWSLETTER_FILE))
    except:
        return None

def format_digest(nl):
    """Format newsletter as Telegram-friendly markdown."""
    date = nl.get("date", datetime.now(timezone(timedelta(hours=TZ_OFFSET))).strftime("%A, %B %d %Y"))

    parts = []

    # Header
    parts.append(f"🌅 *Good Morning — {date}*")
    parts.append("")

    # System status
    sys_text = nl.get("system", "")
    if sys_text:
        if "ALERT" in sys_text or "🔴" in sys_text:
            emoji = "🔴"
        elif "WARN" in sys_text or "🟡" in sys_text:
            emoji = "🟡"
        else:
            emoji = "✅"
        parts.append(f"{emoji} *System:* {sys_text}")

    # Jobs
    jobs = nl.get("jobs", "")
    if jobs:
        parts.append("")
        parts.append("💼 *Jobs:*")
        for line in jobs.split("\n"):
            line = line.strip()
            if line:
                parts.append(f"  {line}")

    # LinkedIn
    li = nl.get("linkedin_post", "")
    if li:
        parts.append("")
        parts.append("✍️ *LinkedIn:*")
        for line in li.split("\n"):
            line = line.strip()
            if line:
                parts.append(f"  {line}")

    # Comment Radar
    cr = nl.get("comment_radar", "")
    if cr:
        parts.append("")
        parts.append("💬 *Comment Radar:*")
        for line in cr.split("\n"):
            line = line.strip()
            if line:
                parts.append(f"  {line}")

    # Outreach
    out = nl.get("outreach", "")
    if out:
        parts.append("")
        parts.append("📬 *Outreach:*")
        for line in out.split("\n"):
            line = line.strip()
            if line:
                parts.append(f"  {line}")

    # GitHub
    gh = nl.get("github", "")
    if gh:
        parts.append("")
        parts.append("🐙 *GitHub Radar:*")
        for line in gh.split("\n"):
            line = line.strip()
            if line:
                parts.append(f"  {line}")

    # Footer
    parts.append("")
    parts.append("───────────────────")
    parts.append("🤖 Pam | NASR Command Center")

    return "\n".join(parts)


def format_summary(nl):
    """Short 5-line summary."""
    date = nl.get("date", "")
    jobs = nl.get("jobs", "")
    outreach = nl.get("outreach", "")
    system = nl.get("system", "")

    # Extract key numbers
    submit = next((p.strip() for p in jobs.split("|") if "Submit" in p), "—")
    response_rate = next((p.strip() for p in outreach.split("|") if "Response" in p), "—")

    lines = [
        f"🌅 *{date} Briefing*",
        f"✅ System: {system.split('|')[0].strip() if system else 'OK'}",
        f"💼 Jobs: {submit}",
        f"📬 Outreach: {response_rate}",
        "🤖 Pam | NASR Command Center",
    ]
    return "\n".join(lines)


def send_telegram(text):
    """Send message via Telegram Bot API directly (bypasses OpenClaw gateway).
    Replies to this message will NOT trigger any agent session."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_notification": True,  # No buzz at 5 AM
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                return True, f"msg_id={result['result']['message_id']}"
            else:
                return False, result.get("description", "Unknown error")
    except Exception as e:
        return False, str(e)[:200]


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    summary_only = "--summary" in sys.argv

    nl = load_newsletter()
    if not nl:
        print("ERROR: No newsletter found. Run pam-newsletter-agent.py first.")
        sys.exit(1)

    text = format_summary(nl) if summary_only else format_digest(nl)

    print("=" * 50)
    print("PAM TELEGRAM")
    print("=" * 50)
    print(text[:500] + "..." if len(text) > 500 else text)
    print("=" * 50)

    if dry_run:
        print("\n[DRY RUN — not sent]")
    else:
        ok, msg = send_telegram(text)
        if ok:
            print(f"\n✅ Sent to Telegram")
        else:
            print(f"\n❌ Failed: {msg}")
