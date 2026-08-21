#!/usr/bin/env python3
"""Validate, summarize, and render the executive experience bank."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


STATUS_VALUES = {"verified", "partial", "candidate"}
ATTRIBUTION_VALUES = {"direct", "shared", "contextual"}
DISCLOSURE_VALUES = {"private", "confidential", "public-approved"}
ID_PATTERN = re.compile(r"^exp-[0-9]{4}-[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_RECORD_FIELDS = {
    "id",
    "title",
    "organization",
    "role",
    "period",
    "status",
    "domains",
    "competencies",
    "source_evidence",
    "situation",
    "responsibility",
    "actions",
    "outcomes",
    "scope_metrics",
    "story_angles",
    "questions_to_complete",
    "disclosure",
}


def load_bank(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"bank not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError("bank root must be a JSON object")
    return data


def _require_nonempty_string(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")


def _require_string_list(value: Any, field: str, errors: list[str], allow_empty: bool = True) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{field} must be a list of non-empty strings")
    elif not allow_empty and not value:
        errors.append(f"{field} must not be empty")


def validate_bank(bank: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("schema_version", "subject", "last_updated"):
        _require_nonempty_string(bank.get(field), field, errors)

    if isinstance(bank.get("last_updated"), str):
        try:
            date.fromisoformat(bank["last_updated"])
        except ValueError:
            errors.append("last_updated must use YYYY-MM-DD")

    _require_string_list(bank.get("source_of_truth"), "source_of_truth", errors, allow_empty=False)

    records = bank.get("records")
    if not isinstance(records, list):
        errors.append("records must be a list")
        return errors
    if not records:
        errors.append("records must not be empty")
        return errors

    seen_record_ids: set[str] = set()
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing = sorted(REQUIRED_RECORD_FIELDS - set(record))
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(missing)}")

        record_id = record.get("id")
        _require_nonempty_string(record_id, f"{prefix}.id", errors)
        if isinstance(record_id, str):
            if not ID_PATTERN.fullmatch(record_id):
                errors.append(f"{prefix}.id must match {ID_PATTERN.pattern}")
            if record_id in seen_record_ids:
                errors.append(f"duplicate record id: {record_id}")
            seen_record_ids.add(record_id)

        for field in ("title", "organization", "role", "period", "situation", "responsibility"):
            _require_nonempty_string(record.get(field), f"{prefix}.{field}", errors)

        if record.get("status") not in STATUS_VALUES:
            errors.append(f"{prefix}.status must be one of {sorted(STATUS_VALUES)}")

        for field, allow_empty in (
            ("domains", False),
            ("competencies", False),
            ("actions", False),
            ("story_angles", True),
            ("questions_to_complete", True),
        ):
            _require_string_list(record.get(field), f"{prefix}.{field}", errors, allow_empty=allow_empty)

        evidence = record.get("source_evidence")
        evidence_ids: set[str] = set()
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}.source_evidence must be a non-empty list")
        else:
            for ev_index, item in enumerate(evidence):
                ev_prefix = f"{prefix}.source_evidence[{ev_index}]"
                if not isinstance(item, dict):
                    errors.append(f"{ev_prefix} must be an object")
                    continue
                for field in ("id", "source", "locator", "claim"):
                    _require_nonempty_string(item.get(field), f"{ev_prefix}.{field}", errors)
                evidence_id = item.get("id")
                if isinstance(evidence_id, str):
                    if evidence_id in evidence_ids:
                        errors.append(f"{prefix} has duplicate evidence id: {evidence_id}")
                    evidence_ids.add(evidence_id)

        outcomes = record.get("outcomes")
        if not isinstance(outcomes, list):
            errors.append(f"{prefix}.outcomes must be a list")
        else:
            for outcome_index, item in enumerate(outcomes):
                out_prefix = f"{prefix}.outcomes[{outcome_index}]"
                if not isinstance(item, dict):
                    errors.append(f"{out_prefix} must be an object")
                    continue
                _require_nonempty_string(item.get("statement"), f"{out_prefix}.statement", errors)
                if item.get("attribution") not in ATTRIBUTION_VALUES:
                    errors.append(f"{out_prefix}.attribution must be one of {sorted(ATTRIBUTION_VALUES)}")
                refs = item.get("source_refs")
                _require_string_list(refs, f"{out_prefix}.source_refs", errors, allow_empty=False)
                if isinstance(refs, list):
                    unknown = sorted(set(refs) - evidence_ids)
                    if unknown:
                        errors.append(f"{out_prefix} has unknown source refs: {', '.join(unknown)}")

        metrics = record.get("scope_metrics")
        if not isinstance(metrics, list):
            errors.append(f"{prefix}.scope_metrics must be a list")
        else:
            for metric_index, item in enumerate(metrics):
                met_prefix = f"{prefix}.scope_metrics[{metric_index}]"
                if not isinstance(item, dict):
                    errors.append(f"{met_prefix} must be an object")
                    continue
                _require_nonempty_string(item.get("label"), f"{met_prefix}.label", errors)
                _require_nonempty_string(item.get("value"), f"{met_prefix}.value", errors)
                if not isinstance(item.get("verified"), bool):
                    errors.append(f"{met_prefix}.verified must be boolean")
                refs = item.get("source_refs")
                _require_string_list(refs, f"{met_prefix}.source_refs", errors, allow_empty=False)
                if isinstance(refs, list):
                    unknown = sorted(set(refs) - evidence_ids)
                    if unknown:
                        errors.append(f"{met_prefix} has unknown source refs: {', '.join(unknown)}")

        disclosure = record.get("disclosure")
        if not isinstance(disclosure, dict):
            errors.append(f"{prefix}.disclosure must be an object")
        else:
            if disclosure.get("classification") not in DISCLOSURE_VALUES:
                errors.append(
                    f"{prefix}.disclosure.classification must be one of {sorted(DISCLOSURE_VALUES)}"
                )
            if not isinstance(disclosure.get("external_reuse_requires_approval"), bool):
                errors.append(f"{prefix}.disclosure.external_reuse_requires_approval must be boolean")
            _require_string_list(
                disclosure.get("constraints"), f"{prefix}.disclosure.constraints", errors, allow_empty=True
            )

    return errors


def _join(values: list[str], empty: str = "None recorded") -> str:
    return ", ".join(values) if values else empty


def render_markdown(bank: dict[str, Any]) -> str:
    records = bank["records"]
    counts = Counter(record["status"] for record in records)
    lines = [
        "# Ahmed Nasr - Executive Experience Bank",
        "",
        "> Private working evidence. External reuse requires review and approval unless a record says otherwise.",
        "",
        f"Last updated: {bank['last_updated']}",
        f"Records: {len(records)} ({counts['verified']} verified, {counts['partial']} partial, {counts['candidate']} candidate)",
        "",
        "## Index",
        "",
        "| ID | Story | Organization | Status | Strongest scope |",
        "|---|---|---|---|---|",
    ]
    for record in records:
        strongest = record["scope_metrics"][0]["value"] if record["scope_metrics"] else "No metric"
        lines.append(
            f"| `{record['id']}` | {record['title']} | {record['organization']} | {record['status']} | {strongest} |"
        )

    for record in records:
        lines.extend(
            [
                "",
                f"## {record['title']}",
                "",
                f"- ID: `{record['id']}`",
                f"- Organization: {record['organization']}",
                f"- Role: {record['role']}",
                f"- Period: {record['period']}",
                f"- Status: {record['status']}",
                f"- Domains: {_join(record['domains'])}",
                f"- Competencies: {_join(record['competencies'])}",
                f"- Disclosure: {record['disclosure']['classification']}; external approval required: {str(record['disclosure']['external_reuse_requires_approval']).lower()}",
                "",
                "### Situation",
                "",
                record["situation"],
                "",
                "### Responsibility",
                "",
                record["responsibility"],
                "",
                "### Supported actions",
                "",
            ]
        )
        lines.extend(f"- {action}" for action in record["actions"])
        lines.extend(["", "### Outcomes and attribution", ""])
        if record["outcomes"]:
            lines.extend(
                f"- [{outcome['attribution']}] {outcome['statement']}" for outcome in record["outcomes"]
            )
        else:
            lines.append("- No result claim is currently supported.")
        lines.extend(["", "### Scope metrics", ""])
        if record["scope_metrics"]:
            lines.extend(
                f"- {metric['label']}: {metric['value']} ({'verified' if metric['verified'] else 'unverified'})"
                for metric in record["scope_metrics"]
            )
        else:
            lines.append("- No scope metric recorded.")
        lines.extend(["", "### Reusable angles", ""])
        if record["story_angles"]:
            lines.extend(f"- {angle}" for angle in record["story_angles"])
        else:
            lines.append("- None recorded.")
        lines.extend(["", "### Questions to complete", ""])
        if record["questions_to_complete"]:
            lines.extend(f"- {question}" for question in record["questions_to_complete"])
        else:
            lines.append("- None.")
        lines.extend(["", "### Evidence", ""])
        lines.extend(
            f"- `{item['id']}` - {item['source']} - {item['locator']}: {item['claim']}"
            for item in record["source_evidence"]
        )
        constraints = record["disclosure"]["constraints"]
        if constraints:
            lines.extend(["", "### Disclosure constraints", ""])
            lines.extend(f"- {constraint}" for constraint in constraints)

    lines.append("")
    return "\n".join(lines)


def print_stats(bank: dict[str, Any]) -> None:
    records = bank["records"]
    statuses = Counter(record["status"] for record in records)
    domains = Counter(domain for record in records for domain in record["domains"])
    unanswered = sum(bool(record["questions_to_complete"]) for record in records)
    print(f"records={len(records)}")
    print("statuses=" + ",".join(f"{key}:{statuses[key]}" for key in sorted(statuses)))
    print("domains=" + ",".join(f"{key}:{domains[key]}" for key in sorted(domains)))
    print(f"records_with_open_questions={unanswered}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate a JSON experience bank")
    validate_parser.add_argument("bank", type=Path)

    render_parser = subparsers.add_parser("render", help="render the JSON bank as Markdown")
    render_parser.add_argument("bank", type=Path)
    render_parser.add_argument("output", type=Path)

    stats_parser = subparsers.add_parser("stats", help="print compact bank statistics")
    stats_parser.add_argument("bank", type=Path)

    args = parser.parse_args()
    try:
        bank = load_bank(args.bank)
        errors = validate_bank(bank)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        if args.command == "validate":
            print(f"OK: {args.bank} ({len(bank['records'])} records)")
        elif args.command == "render":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(render_markdown(bank), encoding="utf-8")
            print(f"OK: rendered {len(bank['records'])} records to {args.output}")
        elif args.command == "stats":
            print_stats(bank)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
