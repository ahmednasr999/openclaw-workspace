#!/usr/bin/env python3
"""Extract normalized markdown/text from imported Slides Lane v2 sources.

Copyright (c) OpenAI. All rights reserved.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from slides_ingest_lib import build_intake_manifest, extract_all_sources, ensure_task_dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract normalized content from Slides Lane v2 sources.")
    parser.add_argument("task_dir", help="Task-local deck workspace directory.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run extraction even when normalized outputs already exist.",
    )
    args = parser.parse_args()

    task_dir = Path(args.task_dir).expanduser().resolve()
    ensure_task_dirs(task_dir)
    registry = extract_all_sources(task_dir, force=args.force)
    manifest = build_intake_manifest(task_dir)

    completed = manifest.get("statusCounts", {}).get("completed", 0)
    failed = manifest.get("statusCounts", {}).get("failed", 0)
    print(f"Processed {len(registry.get('entries', []))} source(s)")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Intake summary: {task_dir / 'planning' / 'intake.json'}")


if __name__ == "__main__":
    main()
