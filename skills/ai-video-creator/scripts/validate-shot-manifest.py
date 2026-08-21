#!/usr/bin/env python3
"""Validate an AI Video Creator shot manifest using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REFERENCE_ID = re.compile(r"^(CHAR|WARD|PROD|ENV|STYLE|CAM|LIGHT|GRADE|AUDIO)-\d{2}$")
SHOT_ID = re.compile(r"^S\d{3}$")
ASPECT_RATIO = re.compile(r"^[1-9]\d*:[1-9]\d*$")
RIGHTS_STATUSES = {
    "owned",
    "approved",
    "licensed",
    "public-domain",
    "not-required",
    "pending",
    "unknown",
}
SHOT_STATUSES = {"planned", "generating", "review", "approved", "rejected", "final"}


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def validate(data: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return ["Manifest root must be a JSON object."], warnings

    if data.get("schema_version") != "1.0":
        errors.append("schema_version must equal '1.0'.")

    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("project must be an object.")
        project = {}
    for field in ("title", "mode", "goal", "aspect_ratio", "platform", "language"):
        if not nonempty_text(project.get(field)):
            errors.append(f"project.{field} must be non-empty text.")
    duration = project.get("duration_seconds")
    if not positive_number(duration):
        errors.append("project.duration_seconds must be a positive number.")
        duration = 0.0
    fps = project.get("fps")
    if not positive_number(fps):
        errors.append("project.fps must be a positive number.")
    if nonempty_text(project.get("aspect_ratio")) and not ASPECT_RATIO.match(project["aspect_ratio"]):
        errors.append("project.aspect_ratio must use W:H format, for example '9:16'.")

    rights = data.get("rights")
    if not isinstance(rights, list):
        errors.append("rights must be an array.")
        rights = []
    for index, item in enumerate(rights):
        prefix = f"rights[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        for field in ("asset_id", "type", "status", "scope", "evidence", "required_disclosure"):
            if not nonempty_text(item.get(field)):
                errors.append(f"{prefix}.{field} must be non-empty text.")
        status = item.get("status")
        if nonempty_text(status) and status not in RIGHTS_STATUSES:
            errors.append(f"{prefix}.status is invalid: {status!r}.")
        if status in {"pending", "unknown"}:
            warnings.append(f"{prefix} is unresolved ({status}); do not treat it as cleared.")

    references = data.get("references")
    if not isinstance(references, list) or not references:
        errors.append("references must be a non-empty array.")
        references = []
    reference_ids: set[str] = set()
    for index, item in enumerate(references):
        prefix = f"references[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        ref_id = item.get("id")
        if not nonempty_text(ref_id) or not REFERENCE_ID.match(ref_id):
            errors.append(f"{prefix}.id must match a supported ID such as PROD-01.")
        elif ref_id in reference_ids:
            errors.append(f"Duplicate reference ID: {ref_id}.")
        else:
            reference_ids.add(ref_id)
        for field in ("category", "path"):
            if not nonempty_text(item.get(field)):
                errors.append(f"{prefix}.{field} must be non-empty text.")
        if not isinstance(item.get("primary"), bool):
            errors.append(f"{prefix}.primary must be true or false.")
        for field in ("locked", "may_vary", "forbidden"):
            values = item.get(field)
            if not isinstance(values, list) or not values or not all(nonempty_text(v) for v in values):
                errors.append(f"{prefix}.{field} must be a non-empty text array.")

    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("shots must be a non-empty array.")
        shots = []
    shot_ids: set[str] = set()
    prior_end = 0.0
    for index, shot in enumerate(shots):
        prefix = f"shots[{index}]"
        if not isinstance(shot, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        shot_id = shot.get("shot_id")
        if not nonempty_text(shot_id) or not SHOT_ID.match(shot_id):
            errors.append(f"{prefix}.shot_id must match S###, for example S001.")
        elif shot_id in shot_ids:
            errors.append(f"Duplicate shot ID: {shot_id}.")
        else:
            shot_ids.add(shot_id)
        start = shot.get("start_seconds")
        shot_duration = shot.get("duration_seconds")
        if not isinstance(start, (int, float)) or isinstance(start, bool) or start < 0:
            errors.append(f"{prefix}.start_seconds must be a non-negative number.")
            start = prior_end
        if not positive_number(shot_duration):
            errors.append(f"{prefix}.duration_seconds must be a positive number.")
            shot_duration = 0.0
        if start < prior_end - 0.001:
            errors.append(f"{prefix} overlaps the previous shot by {prior_end - start:.3f}s.")
        elif start > prior_end + 0.05:
            warnings.append(f"{prefix} begins after a {start - prior_end:.3f}s timeline gap.")
        prior_end = start + shot_duration
        for field in (
            "purpose",
            "action",
            "framing",
            "camera",
            "lighting",
            "transition_in",
            "transition_out",
            "audio",
            "prompt",
            "status",
        ):
            if not nonempty_text(shot.get(field)):
                errors.append(f"{prefix}.{field} must be non-empty text.")
        if nonempty_text(shot.get("status")) and shot["status"] not in SHOT_STATUSES:
            errors.append(f"{prefix}.status is invalid: {shot['status']!r}.")
        refs = shot.get("reference_ids")
        if not isinstance(refs, list) or not refs or not all(nonempty_text(v) for v in refs):
            errors.append(f"{prefix}.reference_ids must be a non-empty text array.")
        else:
            missing = sorted(set(refs) - reference_ids)
            if missing:
                errors.append(f"{prefix} uses undeclared references: {', '.join(missing)}.")
        for field in ("negative_constraints", "acceptance_criteria"):
            values = shot.get(field)
            if not isinstance(values, list) or len(values) < 2 or not all(nonempty_text(v) for v in values):
                errors.append(f"{prefix}.{field} must contain at least two text items.")
        revision = shot.get("revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            errors.append(f"{prefix}.revision must be an integer of 1 or greater.")

    if duration and prior_end > duration + 0.05:
        errors.append(f"Shot timeline ends at {prior_end:.3f}s, beyond project duration {duration:.3f}s.")
    elif duration and abs(prior_end - duration) > 0.05:
        warnings.append(f"Shot timeline ends at {prior_end:.3f}s, not project duration {duration:.3f}s.")

    post = data.get("post")
    if not isinstance(post, dict):
        errors.append("post must be an object.")
    else:
        for field in ("music", "sound_design", "voiceover", "cta", "disclosure", "export_notes"):
            if not nonempty_text(post.get(field)):
                errors.append(f"post.{field} must be non-empty text.")
        texts = post.get("on_screen_text")
        if not isinstance(texts, list) or not texts or not all(nonempty_text(v) for v in texts):
            errors.append("post.on_screen_text must be a non-empty text array.")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to a shot-manifest JSON file")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as validation failures")
    args = parser.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.manifest}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 1

    errors, warnings = validate(data)
    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARNING: {message}")

    if errors or (args.strict and warnings):
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"PASS: {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
