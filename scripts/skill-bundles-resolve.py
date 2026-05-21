#!/usr/bin/env python3
"""Resolve a local skill bundle by command or name."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = ROOT / "skill-bundles"
SKILLS_DIR = ROOT / "skills"


def load_bundles() -> list[dict]:
    bundles: list[dict] = []
    for path in sorted(BUNDLE_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data["_path"] = str(path.relative_to(ROOT))
            bundles.append(data)
    return bundles


def skill_entries(skill_ids: list[str]) -> list[dict]:
    entries = []
    for skill_id in skill_ids:
        path = SKILLS_DIR / skill_id / "SKILL.md"
        entries.append(
            {
                "id": skill_id,
                "path": str(path.relative_to(ROOT)),
                "exists": path.exists(),
            }
        )
    return entries


def resolve(target: str) -> dict | None:
    normalized = target.strip()
    for bundle in load_bundles():
        if normalized in {bundle.get("name"), bundle.get("command")}:
            result = dict(bundle)
            result["skill_entries"] = skill_entries(bundle.get("skills", []))
            return result
    return None


def print_markdown(bundle: dict) -> None:
    print(f"# {bundle['command']} - {bundle['description']}")
    print()
    print(f"- Bundle: {bundle['name']}")
    print(f"- Owner: {bundle['owner']}")
    print(f"- Permission: {bundle['permission_profile']}")
    print(f"- Status: {bundle['status']}")
    print(f"- Source: {bundle['_path']}")
    print()
    print("## Skills")
    for entry in bundle["skill_entries"]:
        marker = "OK" if entry["exists"] else "MISSING"
        print(f"- {marker}: {entry['id']} ({entry['path']})")
    print()
    print("## Approval Boundary")
    print(bundle["approval_boundary"].strip())
    print()
    print("## Standing Instruction")
    print(bundle["standing_instruction"].rstrip())
    print()
    print("## Verification")
    for item in bundle["verification"]:
        print(f"- {item}")
    print()
    print("## Forbidden")
    for item in bundle["forbidden"]:
        print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="bundle command or name, for example /cv-pack")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()

    bundle = resolve(args.target)
    if bundle is None:
        print(f"No bundle found for {args.target!r}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(bundle, indent=2, sort_keys=True))
    else:
        print_markdown(bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
