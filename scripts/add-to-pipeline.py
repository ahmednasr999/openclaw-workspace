#!/usr/bin/env python3
"""
add-to-pipeline.py — Thin CLI to add jobs to the pipeline.

All writes go through pipeline_db (single source of truth).
Notion sync is handled by notion-pipeline-sync.py (separate cron).
Flat files (applied-job-ids.txt, jobs-outcomes.jsonl) are legacy read-only.

Usage:
    python3 add-to-pipeline.py --company "Acme" --role "PM" --url "https://..."
    python3 add-to-pipeline.py --company "Acme" --role "PM" --cv-link "https://..." --verdict SUBMIT
"""

import argparse
import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")

# Import pipeline_db
sys.path.insert(0, str(WORKSPACE / "scripts"))
try:
    import pipeline_db as pdb
except ImportError:
    print("ERROR: pipeline_db.py not found")
    sys.exit(1)


def extract_job_id(url):
    """Extract LinkedIn/Indeed job ID from URL."""
    if not url:
        return None
    m = re.search(r'/view/(\d{8,})', url)
    if m:
        return m.group(1)
    m = re.search(r'-(\d{8,})/?$', url.rstrip('/'))
    if m:
        return m.group(1)
    m = re.search(r'jk=([a-f0-9]+)', url)
    if m:
        return m.group(1)
    return None


def main():
    parser = argparse.ArgumentParser(description="Add job to pipeline (via pipeline_db)")
    parser.add_argument("--company", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--location", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--ats-score", type=int, default=None)
    parser.add_argument("--job-id", default=None, help="Override auto-extracted job ID")
    parser.add_argument("--cv-link", default=None)
    parser.add_argument("--cv-model", default=None)
    parser.add_argument("--verdict", default=None)
    args = parser.parse_args()

    # Generate job_id
    job_id = args.job_id or extract_job_id(args.url)
    if not job_id and args.url:
        job_id = pdb.url_hash(args.url)
    elif not job_id:
        job_id = pdb._generate_job_id(args.source, args.company, args.role, args.url)

    # Register in pipeline_db (single write)
    extra = {}
    if args.ats_score:
        extra["ats_score"] = args.ats_score
    if args.cv_link:
        extra["cv_path"] = args.cv_link
    if args.cv_model:
        extra["cv_cluster"] = args.cv_model
    if args.verdict:
        extra["verdict"] = args.verdict

    pdb.register_job(
        source=args.source.lower(),
        job_id=job_id,
        company=args.company,
        title=args.role,
        location=args.location or None,
        url=args.url or None,
        status="applied",
        **extra,
    )
    print(f"\u2705 Pipeline DB: registered {job_id} ({args.company} | {args.role})")

    # Mark applied with date
    pdb.mark_applied(job_id, applied_date=datetime.now().strftime("%Y-%m-%d"))
    print(f"\u2705 Status: applied ({datetime.now().strftime('%Y-%m-%d')})")

    # Attach CV if provided
    if args.cv_link:
        pdb.attach_cv(job_id, cv_path=args.cv_link, cluster=args.cv_model)
        print(f"\u2705 CV attached: {args.cv_link}")

    # Record outcome for feedback loop (optional, non-blocking)
    try:
        outcomes_file = WORKSPACE / "data" / "feedback" / "jobs-outcomes.jsonl"
        outcomes_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "company": args.company,
            "role": args.role,
            "url": args.url,
            "verdict": args.verdict or "SUBMIT",
            "outcome": "applied",
            "applied_date": datetime.now().strftime("%Y-%m-%d"),
            "ats_score": args.ats_score or 0,
        }
        with open(outcomes_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"  Feedback log failed (non-fatal): {e}")

    print(f"\nDone. Notion sync will pick this up on next cron run.")


if __name__ == "__main__":
    main()
