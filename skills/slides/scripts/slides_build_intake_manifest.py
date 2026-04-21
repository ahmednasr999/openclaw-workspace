#!/usr/bin/env python3
"""Rebuild intake manifest files for a Slides Lane v2 task workspace.

Copyright (c) OpenAI. All rights reserved.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from slides_ingest_lib import build_intake_manifest, ensure_task_dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild intake manifest files for Slides Lane v2.")
    parser.add_argument("task_dir", help="Task-local deck workspace directory.")
    args = parser.parse_args()

    task_dir = Path(args.task_dir).expanduser().resolve()
    ensure_task_dirs(task_dir)
    manifest = build_intake_manifest(task_dir)
    print(f"Updated intake manifest for {manifest['sourceCount']} source(s)")
    print(f"JSON: {task_dir / 'planning' / 'intake.json'}")
    print(f"Markdown: {task_dir / 'planning' / 'intake.md'}")


if __name__ == "__main__":
    main()
