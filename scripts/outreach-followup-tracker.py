#!/usr/bin/env python3
"""
Outreach Follow-up Tracker — Alerts when outreach response rate drops or follow-ups are overdue.

Reads: data/outreach-summary.json + data/outreach-history.json
Alerts: writes to data/outreach-alerts.json + Telegram if critical

Usage:
  python3 outreach-followup-tracker.py         # Run check
  python3 outreach-followup-tracker.py --report    # Full report
  python3 outreach-followup-tracker.py --dry-run  # Preview without alerts
"""

import json, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
OUTREACH_SUMMARY = WORKSPACE / "data/outreach-summary.json"
OUTREACH_HISTORY = WORKSPACE / "data/outreach-history.json"
OUTREACH_ALERTS = WORKSPACE / "data/outreach-alerts.json"
TZ_OFFSET = 2

# Thresholds
RESPONSE_RATE_CRITICAL = 20   # % below which we alert
RESPONSE_RATE_WARNING = 35
QUEUE_DEPTH_CRITICAL = 0      # No queue = reminder to add more
OVERDUE_CRITICAL = 2           # More than 2 overdue = urgent alert


def load_json(path, default=None):
    try:
        return json.load(open(path))
    except:
        return default or {}


def overdue_followups():
    """Find overdue follow-ups from outreach history."""
    history = load_json(OUTREACH_HISTORY, {"sent": []})
    suggestions = history.get("suggested", [])

    now = datetime.now(timezone(timedelta(hours=TZ_OFFSET)))
    overdue = []

    for s in suggestions:
        sent_date = s.get("date", "")
        if not sent_date:
            continue
        try:
            sent = datetime.strptime(sent_date, "%Y-%m-%d")
            sent = sent.replace(tzinfo=timezone(timedelta(hours=TZ_OFFSET)))
            days_ago = (now - sent).days

            # Follow-up expected after 5-7 days
            if days_ago >= 7 and s.get("response_pending", True):
                overdue.append({
                    "name": s.get("name", "?"),
                    "company": s.get("company", "?"),
                    "sent_date": sent_date,
                    "days_ago": days_ago,
                    "url": s.get("url", "?"),
                })
        except:
            pass

    return sorted(overdue, key=lambda x: -x["days_ago"])


def check_queue_depth():
    """Check if outreach queue is running low."""
    history = load_json(OUTREACH_HISTORY, {"suggested": []})
    today = datetime.now(timezone(timedelta(hours=TZ_OFFSET))).strftime("%Y-%m-%d")
    sent_today = [s for s in history.get("suggested", []) if s.get("date") == today]
    return len(sent_today)


def generate_alerts():
    """Check all thresholds and generate alerts."""
    summary = load_json(OUTREACH_SUMMARY, {})
    kpi = summary.get("kpi", {})
    data = summary.get("data", {})
    today_data = data.get("today", {})

    alerts = []
    warnings = []

    # Response rate
    rr = kpi.get("response_rate", 0)
    if rr < RESPONSE_RATE_CRITICAL:
        alerts.append(f"Response rate CRITICAL: {rr:.0f}% (threshold: <{RESPONSE_RATE_CRITICAL}%)")
    elif rr < RESPONSE_RATE_WARNING:
        warnings.append(f"Response rate low: {rr:.0f}% (threshold: <{RESPONSE_RATE_WARNING}%)")

    # Overdue follow-ups
    overdue = overdue_followups()
    if len(overdue) >= OVERDUE_CRITICAL:
        alerts.append(f"{len(overdue)} overdue follow-ups (7+ days, no response)")
    elif overdue:
        warnings.append(f"{len(overdue)} overdue follow-ups pending")

    # Queue depth
    target = today_data.get("target", 0)
    sent = today_data.get("sent", 0)
    if sent < target and target > 0:
        pct = sent / target * 100 if target > 0 else 0
        if pct < 50:
            alerts.append(f"Outreach behind schedule: {sent}/{target} ({pct:.0f}%)")
        else:
            warnings.append(f"Outreach slightly behind: {sent}/{target}")

    # No new outreach today
    if sent == 0 and target == 0:
        warnings.append("No outreach queued for today — add new targets")

    return alerts, warnings, overdue


def format_report(alerts, warnings, overdue):
    """Format as Telegram message."""
    now = datetime.now(timezone(timedelta(hours=TZ_OFFSET))).strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append(f"📬 *Outreach Follow-up Report* — {now}")

    if alerts:
        lines.append("\n🔴 *Alerts:*")
        for a in alerts:
            lines.append(f"  • {a}")

    if warnings:
        lines.append("\n🟡 *Warnings:*")
        for w in warnings:
            lines.append(f"  • {w}")

    if overdue:
        lines.append(f"\n⏰ *{len(overdue)} Overdue Follow-ups:*")
        for o in overdue[:5]:
            lines.append(f"  • {o['name'][:25]} at {o['company']} — {o['days_ago']}d ago")
        if len(overdue) > 5:
            lines.append(f"  +{len(overdue)-5} more")

    if not alerts and not warnings and not overdue:
        lines.append("\n✅ All clear — no alerts")

    lines.append("\n🤖 Outreach Tracker | NASR")

    return "\n".join(lines)


def send_alert(report_text):
    """Send critical alerts to Telegram."""
    try:
        result = subprocess.run(
            ["openclaw", "send", "--text", report_text,
             "--channel", "telegram", "--to", "866838380"],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except:
        return False


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    report_mode = "--report" in sys.argv

    alerts, warnings, overdue = generate_alerts()
    report = format_report(alerts, warnings, overdue)

    # Always show report
    print(report)

    # Save alerts
    alert_data = {
        "generated": datetime.now(timezone(timedelta(hours=TZ_OFFSET))).isoformat(),
        "alerts": alerts,
        "warnings": warnings,
        "overdue_count": len(overdue),
        "overdue": overdue[:10],
    }
    json.dump(alert_data, open(OUTREACH_ALERTS, "w"), indent=2)

    # Send critical alerts to Telegram (not in dry run)
    if alerts and not dry_run:
        ok = send_alert(report)
        if ok:
            print("\n✅ Critical alert sent to Telegram")
        else:
            print("\n⚠️ Alert saved but Telegram send failed")

    if dry_run:
        print("\n[DRY RUN — no alerts sent]")
