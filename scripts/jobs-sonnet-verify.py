#!/usr/bin/env python3
"""
jobs-sonnet-verify.py - Layer 3.5: GPT-5.5 quality gate for job verdicts.

Reads:  data/jobs-summary.json
Writes: data/jobs-summary.json  (in-place update with verifier fields)

Purpose:
  GPT-5.5 does the final quality check on SUBMIT + REVIEW jobs only.
  GPT-5.5 can:
    - Confirm or override the prior verdict
    - Re-rank SUBMIT jobs by actual strategic fit
    - Add a sharp 1-line reason for each job
    - Catch false positives (IT ops dressed as DT) and false negatives

Only SUBMIT + REVIEW jobs are sent to GPT-5.5 (typically 20-60 jobs/day).
SKIP jobs are never re-evaluated to control cost.
"""

import json
import os
import sys
import time
import requests
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))

# OpenClaw gateway
GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"
GPT56_MODEL = "openai/gpt-5.6-sol"

DATA_DIR = Path(__file__).parent.parent / "data"
INPUT_FILE = DATA_DIR / "jobs-summary.json"

CANDIDATE_PROFILE = """
CANDIDATE: Ahmed Nasr — Senior Technology Executive (20+ years)

STRENGTHS: Digital Transformation, Enterprise PMO, Operational Excellence,
Business Excellence, AI Strategy, Change Management

TECH: SAP, Oracle ERP, Agile/PRINCE2/PMP, ITIL, Cloud Migration,
AI/ML Strategy, Data Analytics, Six Sigma

DOMAINS: FinTech, HealthTech, E-commerce, Banking, Insurance,
Telecom, Government/Smart City, Digital Transformation

SCOPE: $50M+ budgets, 200+ person teams, multi-country programs

TARGET: VP/SVP/Director/Head/C-level roles in DT, PMO, Technology, Operations
GEOGRAPHY: UAE, Saudi Arabia, Qatar (primary) | Bahrain, Kuwait, Oman (ok)

RED FLAGS (auto-SKIP):
- Pure IT operations / infrastructure management with no transformation mandate
- Nationals-only roles
- Below Director level (Manager, Lead, Senior individual contributor)
- Pure sales, HR, civil/mechanical engineering, clinical/medical roles
- "Head of IT" that is clearly helpdesk/infra, not strategic technology leadership
"""

BATCH_SIZE = 10  # GPT-5.5 handles 10 at a time for precise judgment


def load_gateway_token() -> str:
    try:
        with open("/root/.openclaw/openclaw.json") as f:
            cfg = json.load(f)
        return cfg.get("gateway", {}).get("auth", {}).get("token", "")
    except Exception:
        return ""


def call_gpt55(prompt: str, timeout: int = 120) -> str | None:
    token = load_gateway_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "model": GPT56_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 3000,
    }

    try:
        resp = requests.post(GATEWAY_URL, json=payload, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            print(f"  GPT-5.5 error: HTTP {resp.status_code} - {resp.text[:200]}")
            return None
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"  GPT-5.5 call error: {e}")
        return None


def build_verifier_prompt(jobs: list[dict]) -> str:
    jobs_text = ""
    for i, job in enumerate(jobs, 1):
        m2_verdict = job.get("verdict", "?")
        m2_score = job.get("career_fit_score", "?")
        m2_reason = job.get("verdict_reason", "")
        description = (job.get("jd_text", "") or job.get("raw_snippet", ""))[:1500]
        nationals = " ⚠️ NATIONALS-ONLY DETECTED" if job.get("nationals_only") else ""

        jobs_text += f"""
JOB {i}:{nationals}
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Prior verdict: {m2_verdict} (score: {m2_score}) - "{m2_reason}"
JD: {description if description else 'No description available'}
---"""

    return f"""{CANDIDATE_PROFILE}

You are the final quality gate before these jobs reach Ahmed.
Your job is to verify, override if needed, and rank.

JOBS TO VERIFY:
{jobs_text}

For each job:
1. Review the prior verdict - agree or override with your own judgment
2. Give a sharp 1-line reason (be specific: what makes it a fit or not)
3. Final verdict: SUBMIT / REVIEW / SKIP
4. Strategic rank for SUBMIT jobs (1 = apply today, higher = lower priority)

OUTPUT FORMAT (JSON array only, no other text):
[
  {{
    "job_num": 1,
    "sonnet_verdict": "SUBMIT",
    "sonnet_score": 9,
    "sonnet_reason": "Exact target role: VP DT mandate + GCC scope + HealthTech domain",
    "overrode_m2": false,
    "rank": 1
  }},
  {{
    "job_num": 2,
    "sonnet_verdict": "SKIP",
    "sonnet_score": 3,
    "sonnet_reason": "IT infrastructure/helpdesk focus despite DT title - no transformation mandate in JD",
    "overrode_m2": true,
    "rank": null
  }}
]

Return ONLY the JSON array."""


def parse_verifier_response(response: str, num_jobs: int) -> list[dict]:
    import re
    try:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if not json_match:
            print("  GPT-5.5 verifier: Could not find JSON array in response")
            return []
        reviews = json.loads(json_match.group())
        return [r for r in reviews if isinstance(r, dict) and "job_num" in r]
    except Exception as e:
        print(f"  GPT-5.5 verifier parse error: {e}")
        return []


def run_verifier(dry_run: bool = False):
    print("\n=== GPT-5.5 Verification Layer ===")

    if not INPUT_FILE.exists():
        print(f"  ERROR: {INPUT_FILE} not found — run jobs-review.py first")
        return False

    with open(INPUT_FILE) as f:
        summary = json.load(f)

    data = summary.get("data", summary)
    submit_jobs = data.get("submit", [])
    review_jobs = data.get("review", [])
    candidates = submit_jobs + review_jobs

    if not candidates:
        print("  No SUBMIT or REVIEW jobs to verify — skipping")
        return True

    print(f"  Verifying {len(submit_jobs)} SUBMIT + {len(review_jobs)} REVIEW = {len(candidates)} total")

    if dry_run:
        print(f"  DRY RUN: Would send {len(candidates)} jobs to GPT-5.5 in {-(-len(candidates)//BATCH_SIZE)} batches")
        for i, job in enumerate(candidates[:5], 1):
            print(f"    {i}. {job.get('title')} @ {job.get('company')} [{job.get('verdict')}]")
        if len(candidates) > 5:
            print(f"    ... and {len(candidates)-5} more")
        return True

    # Process in batches
    all_verifier_reviews = []
    total_overrides = 0
    batch_count = 0

    for batch_start in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        print(f"  GPT-5.5 batch {batch_num} ({len(batch)} jobs)...")

        prompt = build_verifier_prompt(batch)
        start = time.time()
        response = call_gpt55(prompt)
        elapsed = int((time.time() - start) * 1000)

        if response:
            reviews = parse_verifier_response(response, len(batch))
            # Offset job_num to global index
            for r in reviews:
                r["_global_idx"] = batch_start + r["job_num"] - 1
            all_verifier_reviews.extend(reviews)
            overrides = sum(1 for r in reviews if r.get("overrode_m2"))
            total_overrides += overrides
            print(f"    Got {len(reviews)} reviews in {elapsed}ms | {overrides} overrides")
        else:
            print(f"    GPT-5.5 batch {batch_num} failed - keeping prior verdicts for this batch")

        batch_count += 1
        # Small delay between batches to be respectful
        if batch_start + BATCH_SIZE < len(candidates):
            time.sleep(1)

    # Apply verifier verdicts back to the data. Keep sonnet_* keys for downstream compatibility.
    new_submit = []
    new_review = []
    new_skip_from_submit = []
    new_submit_from_review = []

    review_map = {r["_global_idx"]: r for r in all_verifier_reviews if "_global_idx" in r}

    for idx, job in enumerate(candidates):
        verifier = review_map.get(idx)
        if verifier:
            job["sonnet_verdict"] = verifier.get("sonnet_verdict", job.get("verdict"))
            job["sonnet_score"] = verifier.get("sonnet_score", job.get("career_fit_score"))
            job["sonnet_reason"] = verifier.get("sonnet_reason", "")
            job["sonnet_overrode_m2"] = verifier.get("overrode_m2", False)
            job["sonnet_rank"] = verifier.get("rank")
            final_verdict = job["sonnet_verdict"]
        else:
            # GPT-5.5 did not review this one - keep prior verdict
            job["sonnet_verdict"] = job.get("verdict")
            job["sonnet_reason"] = job.get("verdict_reason", "")
            job["sonnet_overrode_m2"] = False
            final_verdict = job.get("verdict", "REVIEW")

        # Track movements
        original_verdict = job.get("verdict")
        if final_verdict == "SUBMIT":
            new_submit.append(job)
            if original_verdict == "REVIEW":
                new_submit_from_review.append(job)
        elif final_verdict == "REVIEW":
            new_review.append(job)
        else:
            # SKIP — track if it was previously SUBMIT
            if original_verdict == "SUBMIT":
                new_skip_from_submit.append(job)

    # Sort SUBMIT by verifier rank (ranked first, then by score)
    ranked = [j for j in new_submit if j.get("sonnet_rank")]
    unranked = [j for j in new_submit if not j.get("sonnet_rank")]
    ranked.sort(key=lambda x: x.get("sonnet_rank", 99))
    unranked.sort(key=lambda x: (x.get("sonnet_score", 0), x.get("career_fit_score", 0)), reverse=True)
    new_submit = ranked + unranked

    # Update summary data
    data["submit"] = new_submit
    data["review"] = new_review
    data["sonnet_verified"] = True
    data["sonnet_overrides"] = total_overrides
    data["sonnet_promoted"] = len(new_submit_from_review)
    data["sonnet_demoted"] = len(new_skip_from_submit)

    # Write back
    summary["data"] = data
    with open(INPUT_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  === GPT-5.5 Verification Complete ===")
    print(f"  Batches: {batch_count} | Overrides: {total_overrides}")
    print(f"  SUBMIT: {len(submit_jobs)} → {len(new_submit)} ({len(new_submit_from_review)} promoted from REVIEW)")
    print(f"  REVIEW: {len(review_jobs)} → {len(new_review)}")
    print(f"  Demoted to SKIP: {len(new_skip_from_submit)} (were SUBMIT)")

    if new_skip_from_submit:
        print(f"\n  ⚠️  GPT-5.5 demoted these from SUBMIT:")
        for j in new_skip_from_submit[:5]:
            print(f"    - {j.get('title')} @ {j.get('company')} | {j.get('sonnet_reason','')[:80]}")

    if new_submit_from_review:
        print(f"\n  ✅ GPT-5.5 promoted these to SUBMIT:")
        for j in new_submit_from_review[:5]:
            print(f"    + {j.get('title')} @ {j.get('company')} | {j.get('sonnet_reason','')[:80]}")

    return True


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    success = run_verifier(dry_run=dry)
    sys.exit(0 if success else 1)
