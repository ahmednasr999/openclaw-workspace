#!/usr/bin/env python3
"""Validate local OpenClaw skill bundle contracts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = ROOT / "skill-bundles"
SKILLS_DIR = ROOT / "skills"

REQUIRED_KEYS = {
    "name",
    "command",
    "description",
    "owner",
    "permission_profile",
    "status",
    "skills",
    "approval_boundary",
    "standing_instruction",
    "verification",
    "forbidden",
}

ALLOWED_PERMISSION_PROFILES = {
    "read-only",
    "local-write",
    "external-write",
    "runtime-change",
    "disruptive",
}

COMMAND_RE = re.compile(r"^/[a-z0-9][a-z0-9-]*$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def fail(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def load_bundle(path: Path, errors: list[str]) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(errors, path, f"cannot parse YAML: {exc}")
        return {}
    if not isinstance(data, dict):
        fail(errors, path, "top-level YAML must be a mapping")
        return {}
    return data


def validate_bundle(path: Path, errors: list[str]) -> None:
    data = load_bundle(path, errors)
    if not data:
        return

    missing = sorted(REQUIRED_KEYS - set(data))
    if missing:
        fail(errors, path, f"missing required keys: {', '.join(missing)}")

    name = data.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        fail(errors, path, "name must be lowercase kebab-case")
    elif path.stem != name:
        fail(errors, path, f"filename stem must match name '{name}'")

    command = data.get("command")
    if not isinstance(command, str) or not COMMAND_RE.match(command):
        fail(errors, path, "command must look like /lowercase-kebab")

    permission_profile = data.get("permission_profile")
    if permission_profile not in ALLOWED_PERMISSION_PROFILES:
        fail(
            errors,
            path,
            "permission_profile must be one of "
            + ", ".join(sorted(ALLOWED_PERMISSION_PROFILES)),
        )

    skills = data.get("skills")
    if not isinstance(skills, list) or not skills:
        fail(errors, path, "skills must be a non-empty list")
    else:
        for item in skills:
            if not isinstance(item, str) or not NAME_RE.match(item):
                fail(errors, path, f"invalid skill id: {item!r}")
                continue
            skill_path = SKILLS_DIR / item / "SKILL.md"
            if not skill_path.exists():
                fail(errors, path, f"missing skill file for '{item}': {skill_path.relative_to(ROOT)}")

    for key in ("standing_instruction", "approval_boundary"):
        if not isinstance(data.get(key), str) or len(data.get(key, "").strip()) < 80:
            fail(errors, path, f"{key} must be a substantive string")

    for key in ("verification", "forbidden"):
        value = data.get(key)
        if not isinstance(value, list) or len(value) < 3 or not all(isinstance(v, str) for v in value):
            fail(errors, path, f"{key} must contain at least three string entries")

    instruction = data.get("standing_instruction", "")
    for section in ("ROLE", "READ SOURCES", "WORKFLOW", "OUTPUT"):
        if section not in instruction:
            fail(errors, path, f"standing_instruction missing section: {section}")


def main() -> int:
    if not BUNDLE_DIR.exists():
        print("skill-bundles directory is missing", file=sys.stderr)
        return 1

    files = sorted(BUNDLE_DIR.glob("*.yaml"))
    if not files:
        print("no bundle YAML files found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in files:
        validate_bundle(path, errors)

    if errors:
        print("Skill bundle validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK: validated {len(files)} skill bundles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
