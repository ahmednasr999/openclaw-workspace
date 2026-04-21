#!/usr/bin/env python3
"""Register source materials for Slides Lane v2 and prepare task-local intake structure.

Copyright (c) OpenAI. All rights reserved.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from slides_ingest_lib import (
    build_intake_manifest,
    ensure_task_dirs,
    is_url,
    register_file_source,
    register_url_source,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import source materials into a Slides Lane v2 task workspace.")
    parser.add_argument("task_dir", help="Task-local deck workspace directory.")
    parser.add_argument("sources", nargs="+", help="One or more file paths or URLs to ingest.")
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move local files into the task workspace instead of copying them.",
    )
    args = parser.parse_args()

    task_dir = Path(args.task_dir).expanduser().resolve()
    ensure_task_dirs(task_dir)

    imported = []
    for item in args.sources:
        if is_url(item):
            imported.append(register_url_source(task_dir, item))
        else:
            imported.append(register_file_source(task_dir, item, move=args.move))

    manifest = build_intake_manifest(task_dir)
    print(f"Imported {len(imported)} source(s) into {task_dir}")
    print(f"Registry: {task_dir / 'sources' / 'sources.json'}")
    print(f"Intake summary: {task_dir / 'planning' / 'intake.json'}")
    print(f"Source count: {manifest['sourceCount']}")


if __name__ == "__main__":
    main()
