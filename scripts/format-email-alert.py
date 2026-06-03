#!/usr/bin/env python3
"""Format email-agent summary JSON as an Ahmed-facing triage card.

Input: /root/.openclaw/workspace/data/email-summary.json by default.
Output: concise Telegram-ready text. No process logs, file paths, UIDs, or model internals.
"""

from __future__ import annotations

import argparse
import json
import re
from email.header import decode_header, make_header
from email.utils import parseaddr
from pathlib import Path
from typing import Any

DEFAULT_SUMMARY = Path("/root/.openclaw/workspace/data/email-summary.json")

URGENT_LEVELS = {"critical", "high"}
ACTIONABLE_CATEGORIES = {
    "interview_invite",
    "assessment",
    "application_response",
    "follow_up_needed",
    "recruiter_reach",
}
NON_ACTIONABLE_CATEGORIES = {"job_alert", "marketing", "newsletter", "other"}
AUTOMATED_ALERT_SENDERS = {
    "bayt",
    "bayt.com",
    "gulftalent",
    "gulftalent.com",
    "monstergulf",
    "monstergulf.com",
    "naukrigulf",
    "naukrigulf.com",
    "linkedin",
    "linkedin.com",
    "foundit",
    "monster",
}
AUTOMATED_ALERT_SUBJECTS = [
    r"thought\s*leader\s*ad",
    r"hot\s+job\s+opportunit",
    r"check\s+out\s+jobs?",
    r"new\s+.+\s+jobs?",
    r"jobs?\s+applied\s+by",
    r"needs\s+a\s+",
    r"opportunit.*waiting\s+for\s+you",
]


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def decode_mime(value: str) -> str:
    value = value or ""
    try:
        return str(make_header(decode_header(value))).strip()
    except Exception:
        return value.strip()


def clean_sender(value: str) -> str:
    value = decode_mime(value)
    name, addr = parseaddr(value)
    label = name or addr or value or "Unknown sender"
    label = re.sub(r"\s+", " ", label).strip().strip('"')
    return label or "Unknown sender"


def clean_subject(value: str) -> str:
    value = decode_mime(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or "No subject"


def is_automated_alert(sender: str, subject: str) -> bool:
    sender_l = (sender or "").lower()
    subject_l = (subject or "").lower()
    domain_match = any(marker in sender_l for marker in AUTOMATED_ALERT_SENDERS)
    subject_match = any(re.search(pattern, subject_l, re.IGNORECASE) for pattern in AUTOMATED_ALERT_SUBJECTS)
    return domain_match and subject_match


def short(value: str, limit: int = 82) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def human_priority(value: str) -> str:
    value = (value or "").strip().lower()
    return {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }.get(value, value.title() or "Medium")


def action_text(item: dict[str, Any]) -> str:
    action = (item.get("action") or "").strip().lower()
    category = (item.get("category") or "").strip().lower()
    deadline = (item.get("response_deadline") or "").strip()

    if action == "respond" or category == "interview_invite":
        if deadline and deadline.lower() not in {"when convenient", "n/a", "none"}:
            return f"Open and respond within {deadline}."
        return "Open and respond."
    if category == "assessment":
        return "Open and check the deadline before planning the assessment."
    if category == "application_response":
        return "Open and complete the recruiter form or CV response."
    if category == "follow_up_needed":
        return "Review and decide whether to reply."
    if category == "recruiter_reach":
        return "Review for fit; respond only if the role is relevant."
    if action == "read_and_file":
        return "Read when convenient; no reply needed."
    if action == "no_action":
        return "No action needed."
    return "Review only if relevant."


def collect_items(summary: dict[str, Any]) -> list[dict[str, Any]]:
    data = summary.get("data") or summary
    llm = data.get("llm_analysis") or {}
    items = []

    def item_key(item: dict[str, Any]) -> tuple[str, str]:
        item_id = str(item.get("id") or "").strip()
        if item_id:
            return ("id", item_id)
        return ("fingerprint", f"{clean_sender(item.get('from') or '')}|{clean_subject(item.get('subject') or '')}".lower())

    seen_keys = set()
    vetoed_keys = set()
    llm_present = isinstance(llm, dict) and bool(llm.get("summary") or llm.get("actionable_emails"))

    for item in llm.get("actionable_emails") or []:
        category = (item.get("category") or "").strip().lower()
        action = (item.get("action") or "").strip().lower()
        sender = clean_sender(item.get("from") or "")
        subject = clean_subject(item.get("subject") or "")
        normalized_key_item = {"id": str(item.get("id") or ""), "from": sender, "subject": subject}
        key = item_key(normalized_key_item)
        fp = ("fingerprint", f"{sender}|{subject}".lower())

        if category in NON_ACTIONABLE_CATEGORIES or action in {"no_action", "read_and_file"}:
            vetoed_keys.update({key, fp})
            continue
        notes = f"{item.get('notes') or ''} {item.get('intent') or ''}".lower()
        if any(marker in notes for marker in ("marketing", "automated", "job alert", "recommendations", "newsletter", "false positive")) and action != "respond":
            vetoed_keys.update({key, fp})
            continue
        if is_automated_alert(sender, subject) and action != "respond":
            vetoed_keys.update({key, fp})
            continue
        normalized = {
            "id": str(item.get("id") or ""),
            "from": sender,
            "subject": subject,
            "category": item.get("category") or "",
            "urgency": (item.get("urgency") or "medium").lower(),
            "action": item.get("action") or "",
            "response_deadline": item.get("response_deadline") or "",
            "notes": item.get("notes") or item.get("intent") or "",
        }
        seen_keys.add(key)
        seen_keys.add(fp)
        items.append(normalized)

    llm_summary = llm.get("summary") or {}
    if llm_present and llm_summary.get("total_actionable") == 0:
        # The LLM has reviewed the actionable candidates and explicitly found
        # none. Do not resurrect heuristic false positives via fallback groups.
        return sorted(items, key=lambda item: ({"critical": 0, "high": 1, "medium": 2, "low": 3}.get(item.get("urgency"), 2), 4))

    fallback_groups = [
        ("interview_invite", data.get("interview_invites") or []),
        ("assessment", data.get("assessments") or []),
        ("application_response", data.get("application_responses") or []),
        ("follow_up_needed", data.get("follow_ups_needed") or []),
        ("recruiter_reach", data.get("recruiter_messages") or []),
        ("follow_up_needed", data.get("hot_alerts") or []),
    ]
    for category, group in fallback_groups:
        for raw in group:
            raw_id = str(raw.get("id") or raw.get("email_id") or "")
            sender = clean_sender(raw.get("from") or "")
            subject = clean_subject(raw.get("subject") or "")
            if not raw_id and sender == "Unknown sender" and subject == "No subject":
                continue
            if is_automated_alert(sender, subject):
                continue
            raw_confidence = raw.get("confidence")
            if raw_confidence is not None and int(raw_confidence or 0) < 55:
                continue
            normalized = {"id": raw_id, "from": sender, "subject": subject}
            key = item_key(normalized)
            fp = ("fingerprint", f"{sender}|{subject}".lower())
            if key in seen_keys or key in vetoed_keys or fp in vetoed_keys:
                continue
            priority = (raw.get("priority") or raw.get("urgency") or "medium").lower()
            if category == "interview_invite" and priority not in {"critical", "high", "hot"}:
                continue
            items.append({
                "id": raw_id,
                "from": sender,
                "subject": subject,
                "category": category,
                "urgency": "critical" if priority == "hot" else priority,
                "action": "respond" if category == "interview_invite" else "review",
                "response_deadline": "24h" if category == "interview_invite" else "",
                "notes": raw.get("why_actionable") or "",
                "confidence": raw.get("confidence"),
            })
            seen_keys.add(key)

    def rank(item: dict[str, Any]) -> tuple[int, int]:
        urgency_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(item.get("urgency"), 2)
        category_rank = {
            "interview_invite": 0,
            "assessment": 1,
            "application_response": 2,
            "follow_up_needed": 3,
            "recruiter_reach": 4,
        }.get(item.get("category"), 4)
        return urgency_rank, category_rank

    return sorted(items, key=rank)


def format_item(item: dict[str, Any], urgent: bool) -> list[str]:
    sender = short(item.get("from") or "Unknown sender", 42)
    subject = short(item.get("subject") or "No subject", 74)
    lines = [f"• {sender} - {subject}"]
    if not urgent:
        confidence = item.get("confidence")
        priority = human_priority(item.get('urgency') or 'medium')
        if confidence is not None:
            priority = f"{priority}, confidence {confidence}%"
        lines.append(f"  Priority: {priority}")
    lines.append(f"  Next: {action_text(item)}")
    if urgent:
        deadline = (item.get("response_deadline") or "").strip()
        if deadline and deadline.lower() not in {"when convenient", "n/a", "none"}:
            lines.append(f"  Timing: {deadline}")
    return lines


def build_alert(summary: dict[str, Any]) -> str:
    data = summary.get("data") or summary
    total_scanned = data.get("total_scanned")
    items = collect_items(summary)
    hot_alerts = data.get("hot_alerts") or []
    urgent_items = [item for item in items if (item.get("urgency") or "").lower() in URGENT_LEVELS]

    if urgent_items:
        picked = urgent_items
        if not picked:
            scanned = "new emails" if total_scanned is None else f"{total_scanned} new email(s)"
            return f"📬 Email scan: all clear ✅\nScanned {scanned}. Nothing requiring action."
        lines = ["🚨 Email alert - action needed", "", "🎯 Action required"]
        for item in picked[:3]:
            lines.extend(format_item(item, urgent=True))
        focus = ((data.get("llm_analysis") or {}).get("summary") or {}).get("daily_focus")
        if focus:
            allowed_subjects = [clean_subject(item.get("subject") or "").lower() for item in items]
            if not any(subject and subject[:35] in focus.lower() for subject in allowed_subjects):
                focus = None
        bottom = focus or "Handle the highest-priority email first."
        lines.extend(["", f"✅ Bottom line: {short(bottom, 120)}"])
        return "\n".join(lines)

    if items:
        label = "action item found" if len(items) == 1 else f"{len(items)} items to review"
        lines = [f"📬 Email scan: {label}", "", "🎯 Needs review"]
        for item in items[:5]:
            lines.extend(format_item(item, urgent=False))
        bottom = "No urgent email action needed."
        lines.extend(["", f"✅ Bottom line: {bottom}"])
        return "\n".join(lines)

    scanned = "new emails" if total_scanned is None else f"{total_scanned} new email(s)"
    return f"📬 Email scan: all clear ✅\nScanned {scanned}. Nothing requiring action."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()
    print(build_alert(load_summary(args.input)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
