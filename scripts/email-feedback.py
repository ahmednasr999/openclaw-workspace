#!/usr/bin/env python3
"""Record Ahmed feedback for the email agent.

Examples:
  python3 scripts/email-feedback.py wrong-alert --sender "newsletter@example.com" --subject "Market update"
  python3 scripts/email-feedback.py important --sender "recruiter@company.com" --note "Always alert"
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_PATH = ROOT / "data" / "email-feedback.jsonl"
VALID_LABELS = {"wrong_alert", "not_job", "noise", "important", "missed", "critical"}


def now_iso() -> str:
    return datetime.now(ZoneInfo("Africa/Cairo")).isoformat()


def append_feedback(label: str, sender: str, subject: str, note: str) -> dict:
    label = label.replace("-", "_").lower()
    if label not in VALID_LABELS:
        raise SystemExit(f"Invalid label {label}. Use one of: {', '.join(sorted(VALID_LABELS))}")
    entry = {
        "timestamp": now_iso(),
        "label": label,
        "from": sender.strip(),
        "subject": subject.strip(),
        "note": note.strip(),
        "source": "manual_cli",
    }
    if not entry["from"] and not entry["subject"]:
        raise SystemExit("Provide --sender or --subject so the rule can match future mail.")
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def summarize() -> dict:
    counts: dict[str, int] = {}
    if FEEDBACK_PATH.exists():
        for line in FEEDBACK_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                label = (json.loads(line).get("label") or "unknown").lower()
            except Exception:
                label = "invalid"
            counts[label] = counts.get(label, 0) + 1
    return {"path": str(FEEDBACK_PATH), "counts": counts}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, label in [("wrong-alert", "wrong_alert"), ("not-job", "not_job"), ("noise", "noise"), ("important", "important"), ("missed", "missed"), ("critical", "critical")]:
        p = sub.add_parser(name)
        p.set_defaults(label=label)
        p.add_argument("--sender", default="")
        p.add_argument("--subject", default="")
        p.add_argument("--note", default="")
    sub.add_parser("summary")
    args = parser.parse_args()
    if args.cmd == "summary":
        print(json.dumps(summarize(), indent=2, ensure_ascii=False))
        return 0
    entry = append_feedback(args.label, args.sender, args.subject, args.note)
    print(json.dumps({"status": "recorded", "entry": entry, "summary": summarize()}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
