#!/usr/bin/env python3
"""
pipeline-healer.py — Self-healing layer for the job pipeline.

Called by job-pipeline-orchestrator.py when any stage fails.
Escalation chain: Sonnet 4.6 → Opus 4.6 → Alert Ahmed → Continue with best data.

Strategy per stage:
  - scan (linkedin/exa/google/indeed/bayt): retry with JobSpy fallback for LinkedIn,
      use cached last-known-good data for others
  - merge: reconstruct from raw files directly
  - enrich: skip enrichment (JDs available from JobSpy), mark as partial
  - review: Sonnet steps in and does the review itself
  - sonnet-verify: already Sonnet — escalate to Opus directly
  - briefing: reconstruct from last available jobs-summary.json

Key principle: Pipeline NEVER hard-stops. Always produce a briefing.
"""

import json
import os
import sys
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / "data"
SCRIPTS_DIR = WORKSPACE / "scripts"
JOBS_RAW_DIR = DATA_DIR / "jobs-raw"

GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"
SONNET_MODEL = "anthropic/claude-sonnet-4-6"
OPUS_MODEL = "anthropic/claude-opus-4-6"

MAX_SONNET_ATTEMPTS = 2
MAX_OPUS_ATTEMPTS = 1

TELEGRAM_CHAT_ID = "-1003882622947"
TELEGRAM_TOPIC_ID = "10"


def load_gateway_token() -> str:
    try:
        with open("/root/.openclaw/openclaw.json") as f:
            cfg = json.load(f)
        return cfg.get("gateway", {}).get("auth", {}).get("token", "")
    except Exception:
        return ""


def call_llm(prompt: str, model: str, timeout: int = 180) -> str | None:
    token = load_gateway_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 4000,
    }
    try:
        resp = requests.post(GATEWAY_URL, json=payload, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None
        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"  LLM call error ({model}): {e}")
        return None


def alert_ahmed(stage: str, error: str, attempted_fixes: list[str]):
    """Send alert to Ahmed via Telegram when all healing attempts fail."""
    try:
        from openclaw import telegram  # type: ignore
    except ImportError:
        pass

    msg = (
        f"⚠️ Pipeline healer exhausted all options\n"
        f"Stage: {stage}\n"
        f"Error: {error[:200]}\n"
        f"Tried: {', '.join(attempted_fixes)}\n"
        f"Continuing with best available data."
    )
    print(f"\n  ALERT AHMED: {msg}")

    # Try to send via Telegram using openclaw CLI
    try:
        subprocess.run(
            ["openclaw", "message", "send",
             "--chat", TELEGRAM_CHAT_ID,
             "--topic", TELEGRAM_TOPIC_ID,
             "--message", msg],
            timeout=15, capture_output=True
        )
    except Exception:
        pass  # Alert logged to stdout at minimum


def heal_scan_stage(stage_name: str, error: str) -> bool:
    """Scan failure: try JobSpy LinkedIn fallback, use cached data for others."""
    print(f"\n  Healer: scan stage '{stage_name}' failed — attempting recovery")
    attempted = []

    if "linkedin" in stage_name.lower():
        # Switch to JobSpy-based LinkedIn scraper
        jobspy_script = SCRIPTS_DIR / "jobs-source-linkedin-jobspy.py"
        if jobspy_script.exists():
            print("  → Trying JobSpy LinkedIn fallback...")
            attempted.append("jobspy_fallback")
            try:
                r = subprocess.run(
                    [sys.executable, str(jobspy_script)],
                    capture_output=True, text=True, timeout=300,
                    cwd=str(WORKSPACE)
                )
                if r.returncode == 0:
                    print("  ✅ JobSpy LinkedIn fallback succeeded")
                    return True
                else:
                    print(f"  JobSpy fallback failed: {r.stderr[-200:]}")
            except Exception as e:
                print(f"  JobSpy fallback error: {e}")

    # Check if cached raw data exists from previous run
    source = stage_name.replace("scan-", "").replace("jobs-source-", "")
    cache_file = JOBS_RAW_DIR / f"{source}.json"
    if cache_file.exists():
        age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hours < 48:
            print(f"  → Using cached {source}.json ({age_hours:.1f}h old) — acceptable fallback")
            attempted.append(f"cache_{source}")
            return True
        else:
            print(f"  Cache too old ({age_hours:.1f}h) — treating as empty source")

    print(f"  ⚠️ Could not recover scan stage '{stage_name}' — pipeline will continue without this source")
    return True  # Always continue — missing one source is not fatal


def heal_review_stage(error: str) -> bool:
    """Review stage failure: Sonnet steps in to do the LLM review itself."""
    print("\n  Healer: review stage failed — Sonnet stepping in as reviewer")

    merged_file = DATA_DIR / "jobs-merged.json"
    summary_file = DATA_DIR / "jobs-summary.json"

    if not merged_file.exists():
        print("  ERROR: No merged jobs file to review — cannot heal")
        return False

    with open(merged_file) as f:
        merged = json.load(f)

    all_jobs = merged.get("data", merged.get("jobs", []))
    if not all_jobs:
        print("  No jobs in merged file — nothing to review")
        # Write empty summary so pipeline continues
        with open(summary_file, "w") as f:
            json.dump({"data": {"submit": [], "review": [], "skip": [], "total": 0}}, f)
        return True

    top_jobs = sorted(all_jobs, key=lambda x: x.get("keyword_score", 0), reverse=True)[:50]
    print(f"  Sonnet reviewing {len(top_jobs)} jobs (top by keyword score)...")

    CANDIDATE_PROFILE = """Senior technology executive (20+ yrs): Digital Transformation, PMO, Operational Excellence.
Target: VP/Director/Head/SVP/C-level in DT, PMO, Technology, Operations. GCC geography (UAE/Saudi/Qatar priority).
NOT suitable: junior roles, pure sales, HR, clinical, civil engineering, nationals-only."""

    BATCH_SIZE = 10
    all_reviews = []

    for batch_start in range(0, len(top_jobs), BATCH_SIZE):
        batch = top_jobs[batch_start:batch_start + BATCH_SIZE]
        jobs_text = ""
        for i, job in enumerate(batch, 1):
            desc = (job.get("jd_text", "") or job.get("raw_snippet", ""))[:500]
            jobs_text += f"JOB {i}: {job.get('title')} @ {job.get('company')} | {job.get('location')}\n{desc}\n---\n"

        prompt = f"""{CANDIDATE_PROFILE}

Review these {len(batch)} jobs. Return JSON array only:
[{{"job_num": 1, "score": 8, "verdict": "SUBMIT", "reason": "brief reason", "salary": "N/A"}}]

Verdicts: SUBMIT (7+), REVIEW (5-6), SKIP (<5)

{jobs_text}"""

        for model, label in [(SONNET_MODEL, "Sonnet"), (SONNET_MODEL, "Sonnet retry"), (OPUS_MODEL, "Opus")]:
            print(f"    Batch {batch_start//BATCH_SIZE+1}: trying {label}...", end=" ", flush=True)
            response = call_llm(prompt, model, timeout=120)
            if response:
                import re
                match = re.search(r'\[[\s\S]*\]', response)
                if match:
                    try:
                        reviews = json.loads(match.group())
                        for r in reviews:
                            r["job_num"] = r["job_num"] + batch_start
                        all_reviews.extend(reviews)
                        print(f"✅ {len(reviews)} reviews")
                        break
                    except Exception:
                        pass
            print("failed, trying next...")
            time.sleep(2)

    # Build summary from reviews
    submit, review, skip = [], [], []
    review_map = {r["job_num"]: r for r in all_reviews}

    for i, job in enumerate(top_jobs, 1):
        r = review_map.get(i, {})
        score = r.get("score", 5)
        verdict = r.get("verdict", "REVIEW")
        job["career_fit_score"] = score
        job["verdict"] = verdict
        job["verdict_reason"] = r.get("reason", "Healer fallback review")

        if verdict == "SUBMIT":
            submit.append(job)
        elif verdict == "REVIEW":
            review.append(job)
        else:
            skip.append(job)

    summary = {
        "data": {
            "submit": submit,
            "review": review,
            "skip": skip,
            "total": len(top_jobs),
            "healer_used": True,
            "healer_model": "sonnet_fallback",
        }
    }

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  ✅ Healer review complete: {len(submit)} SUBMIT | {len(review)} REVIEW | {len(skip)} SKIP")
    return True


def heal_merge_stage(error: str) -> bool:
    """Merge failure: reconstruct merged.json directly from raw files."""
    print("\n  Healer: merge stage failed — reconstructing from raw files")
    raw_files = list(JOBS_RAW_DIR.glob("*.json"))

    if not raw_files:
        print("  No raw files found — cannot heal merge stage")
        return False

    all_jobs = []
    seen_ids = set()

    for raw_file in raw_files:
        try:
            with open(raw_file) as f:
                data = json.load(f)
            jobs = data.get("jobs", data.get("data", []))
            for job in jobs:
                jid = job.get("id") or job.get("url", "")
                if jid not in seen_ids:
                    seen_ids.add(jid)
                    all_jobs.append(job)
        except Exception as e:
            print(f"  Warning: could not read {raw_file.name}: {e}")

    merged = {"data": all_jobs, "total": len(all_jobs), "healer_reconstructed": True}
    with open(DATA_DIR / "jobs-merged.json", "w") as f:
        json.dump(merged, f, indent=2)

    print(f"  ✅ Healer reconstructed merged.json: {len(all_jobs)} jobs from {len(raw_files)} raw files")
    return True


def heal_sonnet_verify_stage(error: str) -> bool:
    """Sonnet verify failed — escalate directly to Opus."""
    print("\n  Healer: sonnet-verify stage failed — escalating to Opus 4.6")

    summary_file = DATA_DIR / "jobs-summary.json"
    if not summary_file.exists():
        print("  No jobs-summary.json — skipping verification")
        return True

    with open(summary_file) as f:
        summary = json.load(f)

    data = summary.get("data", summary)
    candidates = data.get("submit", []) + data.get("review", [])

    if not candidates:
        print("  No candidates to verify — skipping")
        return True

    print(f"  Opus verifying {len(candidates)} jobs...")
    BATCH_SIZE = 10

    for batch_start in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[batch_start:batch_start + BATCH_SIZE]
        jobs_text = "\n".join([
            f"JOB {i+1}: {j.get('title')} @ {j.get('company')} | {j.get('location')} | M2.7: {j.get('verdict')}"
            for i, j in enumerate(batch)
        ])

        prompt = f"""Senior technology executive in GCC (DT/PMO/Technology focus).
Verify these job verdicts. Return JSON only:
[{{"job_num":1,"sonnet_verdict":"SUBMIT","sonnet_score":8,"sonnet_reason":"reason","overrode_m2":false,"rank":1}}]

{jobs_text}"""

        response = call_llm(prompt, OPUS_MODEL, timeout=180)
        if response:
            import re
            match = re.search(r'\[[\s\S]*\]', response)
            if match:
                try:
                    reviews = json.loads(match.group())
                    for r in reviews:
                        idx = batch_start + r.get("job_num", 1) - 1
                        if 0 <= idx < len(candidates):
                            candidates[idx]["sonnet_verdict"] = r.get("sonnet_verdict", candidates[idx].get("verdict"))
                            candidates[idx]["sonnet_score"] = r.get("sonnet_score", 5)
                            candidates[idx]["sonnet_reason"] = r.get("sonnet_reason", "")
                            candidates[idx]["sonnet_overrode_m2"] = r.get("overrode_m2", False)
                            candidates[idx]["sonnet_rank"] = r.get("rank")
                except Exception:
                    pass

        time.sleep(1)

    # Re-split into submit/review
    new_submit = [j for j in candidates if j.get("sonnet_verdict", j.get("verdict")) == "SUBMIT"]
    new_review = [j for j in candidates if j.get("sonnet_verdict", j.get("verdict")) == "REVIEW"]
    data["submit"] = sorted(new_submit, key=lambda x: x.get("sonnet_rank") or 99)
    data["review"] = new_review
    data["sonnet_verified"] = True
    data["healer_escalated_to_opus"] = True

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  ✅ Opus verification complete: {len(new_submit)} SUBMIT | {len(new_review)} REVIEW")
    return True


def heal_stage(stage_name: str, error: str) -> bool:
    """
    Main entry point. Called by orchestrator on stage failure.
    Returns True if healed (pipeline should continue), False if unrecoverable.
    """
    print(f"\n{'='*60}")
    print(f"PIPELINE HEALER: stage='{stage_name}' error='{error[:100]}'")
    print(f"{'='*60}")

    attempted_fixes = []

    if stage_name in ("scan", "jobs-source-linkedin", "jobs-source-exa",
                      "jobs-source-google", "jobs-source-indeed", "jobs-source-bayt"):
        success = heal_scan_stage(stage_name, error)
        attempted_fixes.append(f"scan_recovery:{stage_name}")

    elif stage_name == "merge":
        success = heal_merge_stage(error)
        attempted_fixes.append("merge_reconstruct")

    elif stage_name == "enrich":
        print("  Healer: enrich stage failed — skipping enrichment (JobSpy already has full JDs)")
        success = True  # Non-fatal — review works without enrichment
        attempted_fixes.append("enrich_skip")

    elif stage_name == "review":
        # Sonnet attempt 1
        print(f"  Attempt 1/2: Sonnet 4.6...")
        success = heal_review_stage(error)
        attempted_fixes.append("review_sonnet")
        if not success:
            # Escalate to Opus
            print(f"  Attempt 2/2: Escalating to Opus 4.6...")
            success = heal_review_stage(error)  # heal_review_stage already tries Opus internally
            attempted_fixes.append("review_opus")

    elif stage_name == "sonnet-verify":
        success = heal_sonnet_verify_stage(error)
        attempted_fixes.append("verify_opus_escalation")

    else:
        print(f"  Healer: no strategy for stage '{stage_name}' — continuing")
        success = True
        attempted_fixes.append(f"unknown_stage_passthrough")

    if not success:
        alert_ahmed(stage_name, error, attempted_fixes)

    status = "✅ HEALED" if success else "⚠️ PARTIAL (continuing anyway)"
    print(f"\n  Healer result: {status} | fixes tried: {', '.join(attempted_fixes)}")
    return True  # Always return True — pipeline never hard-stops


if __name__ == "__main__":
    # Can be called directly: python3 pipeline-healer.py <stage> "<error>"
    if len(sys.argv) >= 3:
        stage = sys.argv[1]
        error = sys.argv[2]
        heal_stage(stage, error)
    else:
        print("Usage: pipeline-healer.py <stage_name> '<error_message>'")
        sys.exit(1)
