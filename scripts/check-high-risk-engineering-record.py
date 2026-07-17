#!/usr/bin/env python3
"""Fail-closed validator for completed high-risk engineering records."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED = (
    "Before evidence",
    "Changed files",
    "Focused tests",
    "Original reproduction after fix",
    "Review A findings and disposition",
    "Review B findings and disposition",
    "Repairs and retest evidence",
    "Actual outcome inspected",
    "Rollback evidence",
    "Remaining risk",
)

PLACEHOLDER = re.compile(r"^\s*(?:-|<[^>]+>|tbd|todo|none supplied)?\s*$", re.I)


def extract(text: str, label: str) -> str | None:
    pattern = re.compile(
        rf"(?ms)^-?\s*{re.escape(label)}:\s*(.*?)(?=\n-?\s*[A-Z][^\n:]+:\s*|\n##\s|\Z)"
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def validate(text: str) -> list[str]:
    failures: list[str] = []
    for label in REQUIRED:
        value = extract(text, label)
        if value is None:
            failures.append(f"missing: {label}")
        elif PLACEHOLDER.fullmatch(value):
            failures.append(f"empty: {label}")
    if "Review A" in text and "Review B" in text:
        a = extract(text, "Review A findings and disposition") or ""
        b = extract(text, "Review B findings and disposition") or ""
        if a == b:
            failures.append("reviews are identical")
    if not re.search(r"(?im)^-?\s*Status:\s*(success|clean-noop)\b", text):
        failures.append("missing successful terminal Status")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    text = args.record.read_text(encoding="utf-8")
    failures = validate(text)
    print(json.dumps({"ok": not failures, "failures": failures}, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
