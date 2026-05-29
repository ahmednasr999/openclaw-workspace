#!/usr/bin/env python3
"""Mailbox hygiene intelligence for email-agent history.

Read-only. Produces sender/subject patterns that are repeatedly classified as
`other` or `job_alert`, so Ahmed can decide unsubscribe/block/archive rules.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from email.utils import parseaddr
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HISTORY = DATA / "email-history.jsonl"
OUT = DATA / "email-hygiene-report.json"
NOISE_CATS = {"other", "job_alert"}


def sender_key(value: str) -> str:
    name, addr = parseaddr(value or "")
    return (addr or name or value or "unknown").lower()


def main() -> int:
    sender_counts: Counter[str] = Counter()
    subject_counts: Counter[str] = Counter()
    total = 0
    actionable = 0
    if HISTORY.exists():
        for line in HISTORY.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            cats = set(item.get("categories") or [])
            total += 1
            if cats - NOISE_CATS:
                actionable += 1
                continue
            sender_counts[sender_key(item.get("from", ""))] += 1
            subj = (item.get("subject") or "").strip().lower()[:90]
            if subj:
                subject_counts[subj] += 1
    report = {
        "generated_at": datetime.now(ZoneInfo("Africa/Cairo")).isoformat(),
        "history_items": total,
        "actionable_items": actionable,
        "noise_items": sum(sender_counts.values()),
        "top_noise_senders": sender_counts.most_common(15),
        "top_repeated_subjects": subject_counts.most_common(15),
        "recommendation": "Review these candidates manually before unsubscribe, block, archive, or Gmail filter changes. No mailbox action was taken.",
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("📭 Email hygiene report")
    print(f"History items: {total} | noise: {report['noise_items']} | actionable: {actionable}")
    print("Top noisy senders:")
    for sender, count in report["top_noise_senders"][:8]:
        print(f"- {sender}: {count}")
    print(f"Snapshot: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
