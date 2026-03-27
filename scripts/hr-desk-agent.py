#!/usr/bin/env python3
"""
HR Desk Agent — Persistent monitor for HR Desk topic 9
Chat: -1003882622947 | Topic: 9

Responsibilities:
- Monitor topic 9 for Ahmed's job/CV requests
- Respond in-thread
- Loop in CEO via sessions_send
- Post weekly pipeline summary every Monday
"""

import os
import sys
import json
import subprocess
import datetime
import time
import logging
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
WORKSPACE = Path("/root/.openclaw/workspace")
CHAT_ID = "-1003882622947"
TOPIC_ID = 9
CEO_SESSION = "agent:main:telegram:direct:866838380"
PIPELINE_DB = WORKSPACE / "data" / "nasr-pipeline.db"
LOG_FILE = WORKSPACE / "logs" / "hr-desk-agent.log"
POLL_INTERVAL = 30  # seconds

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HR-Agent] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("hr-desk-agent")


# ── Telegram helpers ──────────────────────────────────────────────────────────

def send_message(text: str, topic_id: int = TOPIC_ID, chat_id: str = CHAT_ID) -> bool:
    """Send a message to the HR Desk thread via openclaw message tool."""
    cmd = [
        "openclaw", "message", "send",
        "--channel", "telegram",
        "--target", chat_id,
        "--thread-id", str(topic_id),
        "--message", text,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log.info(f"Sent to topic {topic_id}: {text[:80]}...")
            return True
        else:
            log.error(f"Send failed: {result.stderr}")
            return False
    except Exception as e:
        log.error(f"Send exception: {e}")
        return False


def send_to_ceo(text: str) -> bool:
    """Loop in CEO via sessions_send."""
    cmd = [
        "openclaw", "sessions", "send",
        "--target", CEO_SESSION,
        "--message", text,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log.info(f"CEO notified: {text[:80]}...")
            return True
        else:
            log.error(f"CEO notify failed: {result.stderr}")
            return False
    except Exception as e:
        log.error(f"CEO notify exception: {e}")
        return False


# ── Pipeline helpers ──────────────────────────────────────────────────────────

def get_pipeline_summary() -> dict:
    """Query SQLite for pipeline counts by status."""
    import sqlite3
    summary = {
        "total": 0,
        "discovered": 0,
        "scored": 0,
        "applied": 0,
        "cv_built": 0,
        "interview": 0,
        "offer": 0,
        "rejected": 0,
        "stale": [],
    }
    if not PIPELINE_DB.exists():
        log.warning(f"Pipeline DB not found: {PIPELINE_DB}")
        return summary

    try:
        conn = sqlite3.connect(str(PIPELINE_DB))
        cur = conn.cursor()

        # Count by status
        cur.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
        for row in cur.fetchall():
            status_key = row[0].lower().replace(" ", "_").replace("-", "_")
            if status_key in summary:
                summary[status_key] = row[1]
            summary["total"] += row[1]

        # Stale: Applied > 14 days with no follow-up
        cutoff = (datetime.date.today() - datetime.timedelta(days=14)).isoformat()
        cur.execute(
            """SELECT title, company, date_applied FROM applications
               WHERE status = 'Applied' AND date_applied < ?
               AND (last_followup IS NULL OR last_followup < ?)""",
            (cutoff, cutoff),
        )
        summary["stale"] = [{"title": r[0], "company": r[1], "date": r[2]} for r in cur.fetchall()]

        conn.close()
    except Exception as e:
        log.error(f"Pipeline query error: {e}")

    return summary


def format_weekly_summary(s: dict) -> str:
    """Format the weekly pipeline summary for Telegram."""
    today = datetime.date.today().strftime("%B %d, %Y")
    stale_lines = ""
    if s["stale"]:
        stale_items = "\n".join(
            f"  • {j['title']} @ {j['company']} (applied {j['date']})"
            for j in s["stale"]
        )
        stale_lines = f"\n\n⚠️ *Stale (>14 days, no follow-up):*\n{stale_items}"

    return (
        f"📊 *Weekly HR Pipeline — {today}*\n\n"
        f"Total in pipeline: {s['total']}\n"
        f"🔍 Discovered: {s['discovered']}\n"
        f"📋 Scored: {s['scored']}\n"
        f"📤 Applied: {s['applied']}\n"
        f"📄 CV Built: {s['cv_built']}\n"
        f"🎤 Interview: {s['interview']}\n"
        f"💼 Offer: {s['offer']}\n"
        f"❌ Rejected: {s['rejected']}"
        f"{stale_lines}\n\n"
        f"_Reply with a job link to add, or 'pipeline' for details._"
    )


# ── Weekly summary ────────────────────────────────────────────────────────────

def maybe_post_weekly_summary():
    """Post weekly pipeline summary on Mondays."""
    state_file = WORKSPACE / "data" / "hr-agent-state.json"
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            state = {}

    today = datetime.date.today().isoformat()
    last_weekly = state.get("last_weekly_summary", "")
    is_monday = datetime.date.today().weekday() == 0  # 0 = Monday

    if is_monday and last_weekly != today:
        log.info("Monday detected — posting weekly summary")
        summary = get_pipeline_summary()
        text = format_weekly_summary(summary)
        if send_message(text):
            state["last_weekly_summary"] = today
            state_file.write_text(json.dumps(state, indent=2))
            # Inform CEO
            send_to_ceo(f"[HR Agent] Weekly pipeline summary posted to HR Desk.\n{summary}")


# ── Message handling ──────────────────────────────────────────────────────────

def classify_message(text: str) -> str:
    """Classify incoming message intent."""
    t = text.lower().strip()
    if any(kw in t for kw in ["linkedin.com/jobs", "bayt.com", "indeed.com", "glassdoor.com",
                                "naukri.com", "ziprecruiter.com", "jobs.google.com",
                                "http://", "https://", "job link"]):
        return "job_link"
    if any(kw in t for kw in ["build cv", "make cv", "create cv", "tailor cv", "build the cv",
                                "make the cv", "go ahead", "do it"]):
        return "build_cv"
    if any(kw in t for kw in ["pipeline", "applications", "how many jobs", "status update",
                                "what's in pipeline", "show pipeline"]):
        return "pipeline_status"
    if any(kw in t for kw in ["recruiter", "outreach", "reach out", "contact", "email recruiter"]):
        return "outreach"
    if any(kw in t for kw in ["interview", "prep", "prepare", "questions"]):
        return "interview_prep"
    if any(kw in t for kw in ["search jobs", "find jobs", "look for jobs", "new opportunities"]):
        return "job_search"
    return "unknown"


def handle_job_link(text: str, message_id: str):
    """Handle a job link submission from Ahmed."""
    reply = (
        "🔍 Got the job link. I'll:\n"
        "1. Extract the JD\n"
        "2. Score it against your profile (tier + ATS fit)\n"
        "3. Add to pipeline if it passes\n"
        "4. Duplicate check before adding\n\n"
        "_Reply 'build CV' once scored to trigger CV creation._"
    )
    send_message(reply)
    send_to_ceo(f"[HR Agent] Ahmed submitted a job link in HR Desk:\n{text[:300]}\nScoring in progress.")


def handle_pipeline_status():
    """Report current pipeline status."""
    summary = get_pipeline_summary()
    text = format_weekly_summary(summary)
    send_message(text)


def handle_unknown(text: str):
    """Handle unrecognised messages."""
    reply = (
        "I'm your HR Agent 🎯\n\n"
        "I can help with:\n"
        "• Job links → score + add to pipeline\n"
        "• 'build CV' → tailored CV for a role\n"
        "• 'pipeline' → current application status\n"
        "• Interview prep\n"
        "• Recruiter outreach\n\n"
        "_For tech/content questions, go to the main chat._"
    )
    send_message(reply)


def process_message(msg: dict):
    """Process a single incoming message."""
    text = msg.get("text", "")
    message_id = msg.get("message_id", "")
    sender = msg.get("from", {}).get("first_name", "Ahmed")

    log.info(f"Message from {sender}: {text[:100]}")
    intent = classify_message(text)
    log.info(f"Intent: {intent}")

    if intent == "job_link":
        handle_job_link(text, message_id)
    elif intent == "build_cv":
        send_message("📄 CV build triggered. Loading your master CV data and the JD now...")
        send_to_ceo(f"[HR Agent] Ahmed triggered CV build in HR Desk. JD context: {text[:200]}")
    elif intent == "pipeline_status":
        handle_pipeline_status()
    elif intent == "outreach":
        send_message("📧 Outreach workflow loaded. Tell me the recruiter's name and company and I'll draft the message.")
        send_to_ceo(f"[HR Agent] Ahmed requested recruiter outreach: {text[:200]}")
    elif intent == "interview_prep":
        send_message("🎤 Interview prep mode. Share the company and role and I'll build your full brief.")
        send_to_ceo(f"[HR Agent] Ahmed requested interview prep: {text[:200]}")
    elif intent == "job_search":
        send_message("🔍 Searching across LinkedIn, Bayt, Naukri, Indeed, Glassdoor, ZipRecruiter, and Google Jobs...")
        send_to_ceo(f"[HR Agent] Job search triggered by Ahmed: {text[:200]}")
    else:
        handle_unknown(text)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    log.info("HR Desk Agent starting — monitoring topic 9")
    send_message("🟢 HR Agent online. Ready for job links, CV requests, and pipeline updates.")

    last_seen_id = None
    state_file = WORKSPACE / "data" / "hr-agent-state.json"

    # Load last seen message ID from state
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            last_seen_id = state.get("last_seen_id")
        except Exception:
            pass

    while True:
        try:
            # Check weekly summary
            maybe_post_weekly_summary()

            # Poll for new messages in topic 9
            # Using openclaw CLI to read messages from topic
            poll_cmd = [
                "openclaw", "message", "read",
                "--channel", "telegram",
                "--target", CHAT_ID,
                "--thread-id", str(TOPIC_ID),
                "--limit", "10",
                "--format", "json",
            ]
            result = subprocess.run(poll_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                try:
                    messages = json.loads(result.stdout)
                    if isinstance(messages, dict):
                        messages = messages.get("messages", [])

                    new_messages = []
                    for msg in messages:
                        msg_id = msg.get("message_id") or msg.get("id")
                        if last_seen_id is None or str(msg_id) > str(last_seen_id):
                            new_messages.append(msg)

                    if new_messages:
                        new_messages.sort(key=lambda m: m.get("message_id") or m.get("id") or 0)
                        for msg in new_messages:
                            process_message(msg)
                            last_seen_id = msg.get("message_id") or msg.get("id")

                        # Persist state
                        try:
                            state = json.loads(state_file.read_text()) if state_file.exists() else {}
                            state["last_seen_id"] = last_seen_id
                            state_file.write_text(json.dumps(state, indent=2))
                        except Exception as e:
                            log.error(f"State write error: {e}")

                except json.JSONDecodeError:
                    log.debug("No JSON in poll response — likely no new messages")

        except KeyboardInterrupt:
            log.info("HR Desk Agent stopped by user")
            send_message("🔴 HR Agent going offline.")
            break
        except Exception as e:
            log.error(f"Loop error: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
