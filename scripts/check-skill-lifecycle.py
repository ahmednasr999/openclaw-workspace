#!/usr/bin/env python3
"""Validate the native OpenClaw skill lifecycle policy and build its compact index."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FULL_GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]
    resident_count: int
    local_on_demand_count: int
    quarantined_count: int
    model_visible_count: int
    classified_visible_count: int

    @property
    def verdict(self) -> str:
        return "PASS" if not self.errors else "FAIL"


def _resident_names(config: dict[str, Any], errors: list[str]) -> list[str]:
    names: list[str] = []
    for position, entry in enumerate(config.get("resident", []), start=1):
        if not isinstance(entry, dict) or not entry.get("name"):
            errors.append(f"Resident entry {position} must have a name")
            continue
        if not entry.get("reason"):
            errors.append(f"Resident skill {entry['name']} must have a reason")
        names.append(entry["name"])
    return names


def _local_names(config: dict[str, Any], errors: list[str]) -> list[str]:
    local = config.get("local_on_demand", {})
    if not isinstance(local, dict):
        errors.append("local_on_demand must be an object grouped by lane")
        return []
    names: list[str] = []
    for lane, entries in local.items():
        if not isinstance(entries, list):
            errors.append(f"Local lane {lane} must be a list")
            continue
        names.extend(str(item) for item in entries)
    return names


def validate(config: dict[str, Any], skills_snapshot: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if config.get("schema_version") != 1:
        errors.append("schema_version must equal 1")

    resident = _resident_names(config, errors)
    local = _local_names(config, errors)
    active_names = resident + local
    duplicates = sorted(name for name, count in Counter(active_names).items() if count > 1)
    if duplicates:
        errors.append("Active skills classified more than once: " + ", ".join(duplicates))

    resident_cap = config.get("resident_max_count")
    if not isinstance(resident_cap, int) or resident_cap < 1:
        errors.append("resident_max_count must be a positive integer")
    elif len(resident) > resident_cap:
        errors.append(
            f"Resident tier exceeds cap: {len(resident)} configured, {resident_cap} allowed"
        )

    visible = {
        skill.get("name")
        for skill in skills_snapshot.get("skills", [])
        if skill.get("modelVisible") is True and skill.get("name")
    }
    classified = set(active_names)

    quarantine = config.get("quarantined_external", [])
    if not isinstance(quarantine, list):
        errors.append("quarantined_external must be a list")
        quarantine = []
    quarantine_names: set[str] = set()
    for position, entry in enumerate(quarantine, start=1):
        if not isinstance(entry, dict) or not entry.get("name"):
            errors.append(f"Quarantined entry {position} must have a name")
            continue
        name = entry["name"]
        quarantine_names.add(name)
        if not FULL_GIT_SHA.fullmatch(str(entry.get("revision", ""))):
            errors.append(f"Quarantined skill {name} requires a full 40-character Git SHA")
        if entry.get("execution_allowed") is not False:
            errors.append(f"Quarantined skill {name} must set execution_allowed=false")
        if entry.get("network_allowed") not in (None, False):
            errors.append(f"Quarantined skill {name} must set network_allowed=false")
        if entry.get("promotion_status") != "blocked":
            errors.append(f"Quarantined skill {name} must keep promotion_status=blocked")

    visible_quarantine = sorted(visible & quarantine_names)
    if visible_quarantine:
        errors.append("Quarantined skills are model-visible: " + ", ".join(visible_quarantine))

    unclassified = sorted(visible - classified - quarantine_names)
    if unclassified:
        errors.append("Unclassified model-visible skills: " + ", ".join(unclassified))

    stale = sorted(classified - visible)
    if stale:
        warnings.append("Classified skills not currently model-visible: " + ", ".join(stale))

    return ValidationResult(
        errors=errors,
        warnings=warnings,
        resident_count=len(resident),
        local_on_demand_count=len(local),
        quarantined_count=len(quarantine),
        model_visible_count=len(visible),
        classified_visible_count=len(visible & classified),
    )


def build_index(config: dict[str, Any], result: ValidationResult) -> str:
    lines = [
        "# OpenClaw Skill Lifecycle Index",
        "",
        f"Validation: **{result.verdict}**",
        "",
        "Resident skills are the small safety-critical or high-frequency control set. "
        "Local specialists remain available on demand. External candidates stay inert until separately promoted.",
        "",
        f"## Resident ({result.resident_count}/{config['resident_max_count']})",
        "",
    ]
    for entry in config.get("resident", []):
        lines.append(f"- `{entry['name']}` — {entry['reason']}")

    lines.extend(["", f"## Local on-demand ({result.local_on_demand_count})", ""])
    for lane, names in config.get("local_on_demand", {}).items():
        lines.extend([f"### {lane}", "", ", ".join(f"`{name}`" for name in names), ""])

    lines.extend(["## Quarantined external", ""])
    for entry in config.get("quarantined_external", []):
        lines.append(
            f"- `{entry['name']}` — `{entry['revision']}` — {entry['promotion_status']}"
        )
    lines.extend(
        [
            "",
            "## Promotion gate",
            "",
            "An external candidate needs an immutable revision, provenance review, inert evaluation, "
            "owner and trigger contracts, focused tests, and Ahmed's separate approval before it can enter the local tier.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: str) -> dict[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--skills-json", required=True, help="OpenClaw skills JSON path or -")
    parser.add_argument("--report")
    parser.add_argument("--index")
    args = parser.parse_args(argv)

    config = _load_json(args.config)
    snapshot = _load_json(args.skills_json)
    result = validate(config, snapshot)
    payload = {
        "verdict": result.verdict,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        **asdict(result),
    }

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.index:
        index_path = Path(args.index)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(build_index(config, result), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0 if result.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
