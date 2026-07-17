#!/usr/bin/env python3
"""Validate the minimum contract for a durable solution document."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = (
    "Summary",
    "Symptoms",
    "Root cause",
    "Failed approaches",
    "Verified solution",
    "Evidence",
    "Prevention",
    "When to revisit",
)


def fail(messages: list[str]) -> int:
    for message in messages:
        print(f"ERROR: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail(["usage: validate_solution.py <solution.md>"])

    path = Path(sys.argv[1])
    if not path.is_file():
        return fail([f"file not found: {path}"])

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        errors.append("missing YAML frontmatter")
    else:
        frontmatter = text.split("\n---\n", 1)[0][4:]
        for field in ("title", "status", "verified_on", "area", "tags"):
            if not re.search(rf"(?m)^{field}:\s*\S", frontmatter):
                errors.append(f"frontmatter field is missing or empty: {field}")
        if not re.search(r"(?m)^status:\s*verified\s*$", frontmatter):
            errors.append("status must be verified")
        if not re.search(r"(?m)^verified_on:\s*\d{4}-\d{2}-\d{2}\s*$", frontmatter):
            errors.append("verified_on must use YYYY-MM-DD")

    for heading in REQUIRED_HEADINGS:
        match = re.search(rf"(?m)^## {re.escape(heading)}\s*$", text)
        if not match:
            errors.append(f"missing heading: ## {heading}")
            continue
        body_start = match.end()
        next_heading = re.search(r"(?m)^## ", text[body_start:])
        body_end = body_start + next_heading.start() if next_heading else len(text)
        if not text[body_start:body_end].strip():
            errors.append(f"empty section: ## {heading}")

    if re.search(r"(?i)\b(TODO|TBD|FIXME)\b|<[^>]+>", text):
        errors.append("document contains unresolved placeholder text")

    if errors:
        return fail(errors)

    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
