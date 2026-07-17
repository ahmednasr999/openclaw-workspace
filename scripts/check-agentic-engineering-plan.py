#!/usr/bin/env python3
"""Fail-closed structural validator for executor-ready engineering plans."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_HEADINGS = (
    "Plan Metadata",
    "Objective",
    "Evidence And Current State",
    "Scope",
    "Authority And Safety",
    "Ordered Implementation Steps",
    "Test Plan",
    "Stop Conditions",
    "Done Criteria",
    "Review Handoff",
)

REQUIRED_FIELDS = (
    "Status",
    "Owner",
    "Planned at",
    "Target outcome",
    "User-visible success condition",
    "Source anchors",
    "In scope",
    "Do not touch",
    "Permission profile",
    "Approval boundary",
    "Rollback path",
)

PLACEHOLDER = re.compile(
    r"^\s*(?:-|none|n/a|tbd|todo|draft|<[^>]+>|[^\n]*<[^>]+>[^\n]*)\s*$",
    re.I,
)
FILE_LINE = re.compile(r"(?:^|[\s`'(])[^\s`':]+(?:/[^\s`':]+)*:[1-9]\d*(?:[-:][1-9]\d*)?")


def field_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?im)^-\s*{re.escape(label)}:\s*(.+)$", text)
    return match.group(1).strip() if match else None


def validate(text: str) -> list[str]:
    failures: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"(?m)^##\s+{re.escape(heading)}\s*$", text):
            failures.append(f"missing heading: {heading}")

    for label in REQUIRED_FIELDS:
        value = field_value(text, label)
        if value is None:
            failures.append(f"missing field: {label}")
        elif PLACEHOLDER.fullmatch(value):
            failures.append(f"empty field: {label}")

    planned_at = field_value(text, "Planned at") or ""
    if planned_at and not re.search(r"(?i)(commit\s+`?[0-9a-f]{7,40}`?|non-git snapshot\s+\S+)", planned_at):
        failures.append("Planned at must name a git commit or non-git snapshot")

    source_anchors = field_value(text, "Source anchors") or ""
    if source_anchors and not FILE_LINE.search(source_anchors):
        failures.append("Source anchors must include file:line evidence")

    if "**Drift check:**" not in text:
        failures.append("missing drift check")

    steps = re.findall(r"(?m)^###\s+Step\s+\d+:", text)
    if not steps:
        failures.append("missing ordered implementation step")

    for label in ("Verify command/check", "Expected result"):
        count = len(re.findall(rf"(?im)^-\s*{re.escape(label)}:\s*(.+)$", text))
        if count < len(steps):
            failures.append(f"each step requires {label}")

    if re.search(r"(?i)(api[_ -]?key|token|password|secret)\s*[:=]\s*[A-Za-z0-9_\-]{16,}", text):
        failures.append("possible secret value embedded in plan")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    failures = validate(args.plan.read_text(encoding="utf-8"))
    print(json.dumps({"ok": not failures, "failures": failures}, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
