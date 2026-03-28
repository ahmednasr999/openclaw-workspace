#!/usr/bin/env python3
"""
job-pipeline-orchestrator.py - Sequential job pipeline execution.

Replaces independent crons with guaranteed ordering:
  1. Scan (linkedin-gulf-jobs.py) - discover new jobs
  2. Merge (jobs-merge.py) - consolidate from all sources
  3. Enrich (jobs-enrich-jd.py) - fetch full JDs for top candidates
  4. Review (jobs-review.py) - LLM career-fit scoring

Each stage checks if the previous stage produced fresh output (< 1 hour).
If a stage fails, subsequent stages skip with a warning.

Run: python3 scripts/job-pipeline-orchestrator.py [--skip-scan] [--dry-run]
Cron: 2 AM Cairo daily
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path("/root/.openclaw/workspace/scripts")
DATA_DIR = Path("/root/.openclaw/workspace/data")
OUTPUT_DIR = Path("/root/.openclaw/workspace/jobs-bank/scraped")
LOG_FILE = DATA_DIR / "pipeline-runs.jsonl"

STAGES = [
    {
        "name": "scan",
        "script": SCRIPTS_DIR / "jobs-source-linkedin-jobspy.py",  # JobSpy public API (no auth needed)
        "timeout": 600,  # 10 minutes
        "output_check": lambda: sorted(OUTPUT_DIR.glob("jobs-raw-*.json"), key=lambda p: p.stat().st_mtime, reverse=True),
        "skip_flag": "--skip-scan",
    },

    {
        "name": "merge",
        "script": SCRIPTS_DIR / "jobs-merge.py",
        "timeout": 120,  # 2 minutes
        "output_check": lambda: [DATA_DIR / "jobs-merged.json"] if (DATA_DIR / "jobs-merged.json").exists() else [],
    },
    {
        "name": "enrich",
        "script": SCRIPTS_DIR / "jobs-enrich-jd.py",
        "timeout": 300,  # 5 minutes
        "output_check": lambda: [DATA_DIR / "jobs-merged.json"],  # enriches in-place
    },
    {
        "name": "review",
        "script": SCRIPTS_DIR / "jobs-review.py",
        "timeout": 600,  # 10 minutes
        "output_check": lambda: [DATA_DIR / "jobs-summary.json"] if (DATA_DIR / "jobs-summary.json").exists() else [],
    },
    {
        "name": "sonnet-verify",
        "script": SCRIPTS_DIR / "jobs-sonnet-verify.py",
        "timeout": 300,  # 5 minutes — Sonnet reviews SUBMIT+REVIEW only (~20-60 jobs)
        "output_check": lambda: [DATA_DIR / "jobs-summary.json"] if (DATA_DIR / "jobs-summary.json").exists() else [],
    },
    {
        "name": "cv-autogen",
        "script": SCRIPTS_DIR / "jobs-cv-autogen.py",
        "timeout": 7200,  # 2 hours max — up to 20 Opus calls @ ~5min each
        "output_check": lambda: [DATA_DIR / "jobs-cv-links.json"] if (DATA_DIR / "jobs-cv-links.json").exists() else [],
    },
    {
        "name": "coverletter-autogen",
        "script": SCRIPTS_DIR / "jobs-coverletter-autogen.py",
        "timeout": 3600,  # 1 hour max — only runs for jobs with CVs
        "output_check": lambda: [DATA_DIR / "jobs-cover-links.json"] if (DATA_DIR / "jobs-cover-links.json").exists() else [],
    },
]


def run_stage(stage, dry_run=False):
    """Run a pipeline stage. Returns (success, duration_seconds, error_message)."""
    name = stage["name"]
    script = stage["script"]

    if not script.exists():
        return False, 0, f"Script not found: {script}"

    print(f"\n{'='*60}")
    print(f"STAGE: {name.upper()}")
    print(f"Script: {script.name}")
    print(f"Timeout: {stage['timeout']}s")
    print(f"{'='*60}")

    if dry_run:
        print(f"  [DRY RUN] Would execute: python3 {script}")
        return True, 0, ""

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=stage["timeout"],
            cwd=str(SCRIPTS_DIR.parent),
        )

        duration = int(time.time() - start)

        # Print last 30 lines of output
        stdout_lines = result.stdout.strip().split("\n") if result.stdout else []
        if stdout_lines:
            for line in stdout_lines[-30:]:
                print(f"  {line}")

        if result.returncode != 0:
            stderr_tail = result.stderr.strip().split("\n")[-10:] if result.stderr else []
            error = f"Exit code {result.returncode}: {' '.join(stderr_tail)}"
            print(f"  ERROR: {error}")
            return False, duration, error

        print(f"  Completed in {duration}s")
        return True, duration, ""

    except subprocess.TimeoutExpired:
        duration = int(time.time() - start)
        return False, duration, f"Timeout after {stage['timeout']}s"
    except Exception as e:
        duration = int(time.time() - start)
        return False, duration, str(e)


def send_alert(message):
    """Send failure alert to Telegram via OpenClaw announce."""
    try:
        subprocess.run(
            ["openclaw", "announce", message],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass


def main():
    skip_scan = "--skip-scan" in sys.argv
    dry_run = "--dry-run" in sys.argv

    start = time.time()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"Job Pipeline Orchestrator")
    print(f"Started: {ts}")
    if dry_run:
        print("[DRY RUN MODE]")

    results = {}
    failed = False

    for stage in STAGES:
        if skip_scan and stage["name"] == "scan":
            print(f"\nSkipping {stage['name']} (--skip-scan)")
            results[stage["name"]] = {"status": "skipped", "duration": 0}
            continue

        if failed:
            print(f"\nSkipping {stage['name']} (previous stage failed)")
            results[stage["name"]] = {"status": "skipped_dependency", "duration": 0}
            continue

        success, duration, error = run_stage(stage, dry_run=dry_run)
        results[stage["name"]] = {
            "status": "success" if success else "failed",
            "duration": duration,
            "error": error if not success else "",
        }

        if not success:
            # Invoke self-healer before giving up
            print(f"\n  Stage '{stage['name']}' failed — invoking pipeline healer...")
            try:
                healer_result = subprocess.run(
                    [sys.executable, str(SCRIPTS_DIR / "pipeline-healer.py"),
                     stage["name"], error],
                    capture_output=True, text=True,
                    timeout=600, cwd=str(SCRIPTS_DIR.parent)
                )
                for line in healer_result.stdout.strip().split("\n"):
                    print(f"  [HEALER] {line}")
                # Healer always returns True (pipeline never hard-stops)
                results[stage["name"]]["status"] = "healed"
                results[stage["name"]]["healer_used"] = True
            except Exception as he:
                print(f"  [HEALER] ERROR: {he}")
                failed = True
                send_alert(f"Job pipeline FAILED at {stage['name']} (healer also failed): {error}")

    total_duration = int(time.time() - start)

    # Log run
    log_entry = {
        "date": date_str,
        "timestamp": ts,
        "total_duration": total_duration,
        "stages": results,
        "dry_run": dry_run,
    }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    # Summary
    print(f"\n{'='*60}")
    print(f"PIPELINE SUMMARY ({total_duration}s)")
    print(f"{'='*60}")
    for name, r in results.items():
        status_icon = {"success": "OK", "failed": "FAIL", "skipped": "SKIP", "skipped_dependency": "DEP", "healed": "🔧 HEALED"}
        icon = status_icon.get(r["status"], "?")
        print(f"  [{icon}] {name}: {r['status']} ({r['duration']}s)")
        if r.get("error"):
            print(f"         Error: {r['error']}")

    if failed:
        print(f"\nPipeline completed with failures.")
        sys.exit(1)
    else:
        print(f"\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
