#!/usr/bin/env python3
"""
jobs-review.py — Layer 3: Two-round LLM review of merged jobs.

Round 1 - MiniMax M2.7 (free, fast):
  - Reviews ALL 300 jobs
  - Conservative filter: only SKIPs if career_fit < 3/10 with confidence >= 0.8
  - Everything uncertain passes through to Round 2

Round 2 - Sonnet 4.6 (quality gate, mandatory):
  - Reviews only Round 1 survivors (~100-150 jobs)
  - Makes final SUBMIT / REVIEW / SKIP verdict
  - This is the authoritative output Ahmed sees

Reads: data/jobs-merged.json
Writes: data/jobs-summary.json (final output for Brief Me)
        data/feedback/jobs-recommended.jsonl
"""

import json
import os
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(__file__))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from _imports import agent_common

# Import from agent_common
AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
load_json = agent_common.load_json
now_iso = agent_common.now_iso
DATA_DIR = agent_common.DATA_DIR
FEEDBACK_DIR = agent_common.FEEDBACK_DIR

# Configuration
AGENT_NAME = "jobs-review"
INPUT_FILE = DATA_DIR / "jobs-merged.json"
OUTPUT_FILE = DATA_DIR / "jobs-summary.json"
RECOMMENDED_FILE = FEEDBACK_DIR / "jobs-recommended.jsonl"
OUTCOMES_FILE = FEEDBACK_DIR / "jobs-outcomes.jsonl"

# OpenClaw gateway for LLM
GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"

# Two-round model config
MODEL_ROUND1 = "minimax-portal/MiniMax-M2.7"   # Fast filter — free, reviews all 300
MODEL_ROUND2 = "anthropic/claude-sonnet-4-6"    # Quality gate — mandatory final verdict
REQUIRED_MODEL_R2_PREFIX = "anthropic/claude-sonnet"

# Safety assertion — Round 2 must always be Sonnet
assert MODEL_ROUND2.startswith(REQUIRED_MODEL_R2_PREFIX), (
    f"ABORT: Round 2 model is '{MODEL_ROUND2}' but must be Sonnet 4.6. "
    f"Ahmed requires Sonnet as the final quality gate before jobs reach Notion/Telegram."
)

# Round 1 filter settings
R1_SKIP_THRESHOLD = 3       # MiniMax scores below this are candidates for SKIP
R1_CONFIDENCE_FLOOR = 0.80  # MiniMax must be >= 80% confident to SKIP (conservative)

# Round 2 verdict settings
TOP_N_JOBS = 300
DEFAULT_SUBMIT_THRESHOLD = 7
DEFAULT_REVIEW_THRESHOLD = 5


def load_feedback_thresholds() -> tuple[int, int]:
    """Load and analyze past outcomes to adjust thresholds."""
    submit_threshold = DEFAULT_SUBMIT_THRESHOLD
    review_threshold = DEFAULT_REVIEW_THRESHOLD

    try:
        if not OUTCOMES_FILE.exists():
            return submit_threshold, review_threshold

        outcomes = []
        with open(OUTCOMES_FILE) as f:
            for line in f:
                if line.strip():
                    outcomes.append(json.loads(line))

        if len(outcomes) < 10:
            return submit_threshold, review_threshold

        submitted = [o for o in outcomes if o.get("verdict") == "SUBMIT"]
        if len(submitted) < 5:
            return submit_threshold, review_threshold

        successful = [o for o in submitted if o.get("outcome") in ["interview", "offer"]]
        success_rate = len(successful) / len(submitted)

        if success_rate < 0.2:
            submit_threshold = min(9, submit_threshold + 1)
        elif success_rate > 0.5:
            submit_threshold = max(6, submit_threshold - 1)

        print(f"  Feedback analysis: {len(submitted)} submitted, {len(successful)} successful ({success_rate:.0%})")
        print(f"  Adjusted thresholds: SUBMIT >= {submit_threshold}, REVIEW >= {review_threshold}")

    except Exception as e:
        print(f"  Warning: Could not load feedback: {e}")

    return submit_threshold, review_threshold


def _wait_for_gateway(max_wait: int = 60) -> bool:
    """Wait for gateway to become available. Returns True if healthy."""
    import time as _time
    deadline = _time.time() + max_wait
    attempt = 0
    while _time.time() < deadline:
        try:
            r = requests.get(GATEWAY_URL.replace("/chat/completions", "/models"), timeout=5)
            if r.status_code in (200, 401):
                return True
        except Exception:
            pass
        attempt += 1
        wait = min(2 ** attempt, 15)
        print(f"  Gateway not ready, retrying in {wait}s...")
        _time.sleep(wait)
    return False


def _call_minimax_direct(prompt: str, model: str, timeout: int = 240, max_retries: int = 3) -> str | None:
    """Call MiniMax API directly, bypassing the gateway. Used for batch review jobs."""
    import time as _time
    try:
        auth = json.load(open("/root/.openclaw/agents/main/agent/auth.json"))
        token = auth.get("minimax-portal", {}).get("access", "")
    except Exception:
        return None
    if not token:
        return None
    # Strip provider prefix from model name
    model_id = model.split("/")[-1] if "/" in model else model
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                "https://api.minimax.io/anthropic/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": token,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model_id,
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=timeout,
            )
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 10))
                print(f"  MiniMax rate limited, waiting {retry_after}s...")
                _time.sleep(retry_after)
                continue
            if resp.status_code != 200:
                print(f"  MiniMax direct error: HTTP {resp.status_code} - {resp.text[:100]}")
                if attempt < max_retries:
                    _time.sleep(2)
                    continue
                return None
            data = resp.json()
            # Anthropic Messages API format
            content_blocks = data.get("content", [])
            text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
            return "\n".join(text_parts) if text_parts else None
        except Exception as e:
            print(f"  MiniMax direct error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                _time.sleep(2)
                continue
            return None
    return None


def _call_anthropic_direct(prompt: str, model: str, timeout: int = 240, max_retries: int = 3) -> str | None:
    """Call Anthropic API directly, bypassing the gateway."""
    import time as _time
    try:
        with open("/root/.openclaw/openclaw.json") as f:
            import re
            content = f.read()
            m = re.search(r'sk-ant-[^"]+', content)
            api_key = m.group(0) if m else ""
    except Exception:
        return None
    if not api_key:
        return None
    model_id = model.split("/")[-1] if "/" in model else model
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model_id,
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=timeout,
            )
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 15))
                print(f"  Anthropic rate limited, waiting {retry_after}s...", flush=True)
                _time.sleep(retry_after)
                continue
            if resp.status_code != 200:
                print(f"  Anthropic direct error: HTTP {resp.status_code} - {resp.text[:100]}", flush=True)
                if attempt < max_retries:
                    _time.sleep(3)
                    continue
                return None
            data = resp.json()
            content_blocks = data.get("content", [])
            text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
            return "\n".join(text_parts) if text_parts else None
        except Exception as e:
            print(f"  Anthropic direct error (attempt {attempt}/{max_retries}): {e}", flush=True)
            if attempt < max_retries:
                _time.sleep(3)
                continue
            return None
    return None


def call_llm(prompt: str, model: str, timeout: int = 240, max_retries: int = 3) -> str | None:
    """Call LLM directly - bypass gateway entirely to avoid connection drops."""
    import time as _time

    # For MiniMax models, call MiniMax API directly
    if "minimax" in model.lower():
        print(f"    → MiniMax direct call ({len(prompt)} chars)...", flush=True)
        result = _call_minimax_direct(prompt, model, timeout, max_retries)
        if result is not None:
            return result
        print("  MiniMax direct failed, falling through to gateway...", flush=True)

    # For Anthropic models, call Anthropic API directly
    if "anthropic" in model.lower() or "claude" in model.lower() or "sonnet" in model.lower():
        print(f"    → Anthropic direct call ({len(prompt)} chars)...", flush=True)
        result = _call_anthropic_direct(prompt, model, timeout, max_retries)
        if result is not None:
            return result
        print("  Anthropic direct failed, falling through to gateway...", flush=True)

    try:
        with open("/root/.openclaw/openclaw.json") as _f:
            _cfg = json.load(_f)
        gw_token = _cfg.get("gateway", {}).get("auth", {}).get("token", "")
    except Exception:
        gw_token = ""

    headers = {"Content-Type": "application/json"}
    if gw_token:
        headers["Authorization"] = f"Bearer {gw_token}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4000,
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(GATEWAY_URL, json=payload, headers=headers, timeout=timeout)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 10))
                print(f"  Rate limited, waiting {retry_after}s...")
                _time.sleep(retry_after)
                continue

            if resp.status_code != 200:
                print(f"  LLM error: HTTP {resp.status_code}")
                return None

            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content

        except requests.exceptions.Timeout:
            print(f"  LLM timeout ({timeout}s), attempt {attempt}/{max_retries}")
            if attempt < max_retries:
                continue
            return None
        except (requests.exceptions.ConnectionError, ConnectionRefusedError) as e:
            print(f"  Gateway connection lost (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                print(f"  Waiting for gateway recovery...")
                if _wait_for_gateway(max_wait=60):
                    print(f"  Gateway recovered, retrying...")
                    continue
                else:
                    print(f"  Gateway did not recover in 60s")
                    return None
            return None
        except Exception as e:
            print(f"  LLM error: {e}")
            return None

    return None


# ── ROUND 1: MiniMax filter prompt ───────────────────────────────────────────

CANDIDATE_PROFILE_SHORT = """
Ahmed Nasr - 20+ year technology executive (VP/Director/Head/C-level).
Core: Digital Transformation, PMO/Program Management, Operational Excellence.
Domains: FinTech, HealthTech, E-commerce, Banking, Telecom, Government.
Target: VP/Director/Head/SVP/C-level roles in GCC (UAE, Saudi, Qatar).
NOT suitable for: pure sales, HR, hands-on coding, civil/mechanical engineering,
oil & gas field ops, teaching, nursing, junior/mid-level (below Director).
"""


def build_round1_prompt(jobs: list[dict]) -> str:
    """Simple, fast Round 1 prompt — conservative filter only."""
    jobs_text = ""
    for i, job in enumerate(jobs, 1):
        nationals_flag = " [NATIONALS ONLY]" if job.get("nationals_only") else ""
        jobs_text += (
            f"\nJOB {i}:{nationals_flag}\n"
            f"- Title: {job.get('title', 'Unknown')}\n"
            f"- Company: {job.get('company', 'Unknown')}\n"
            f"- Location: {job.get('location', 'Unknown')}\n"
            f"- Snippet: {str(job.get('raw_snippet', ''))[:300]}\n"
        )

    return f"""{CANDIDATE_PROFILE_SHORT}

TASK: Quick pre-filter. For each job decide: PASS (needs full review) or SKIP (clearly irrelevant).

RULES:
- SKIP only if you are >= 80% confident this job is COMPLETELY wrong for Ahmed
- SKIP automatically if: nationals-only flag, junior role (analyst/intern/coordinator/specialist), wrong field (nursing/teaching/civil engineering/oil field), wrong geography (outside GCC + relocation-unfriendly)
- PASS everything else — wrong to miss a good job than to review an irrelevant one
- If unsure: PASS

{jobs_text}

OUTPUT FORMAT (JSON array, one entry per job):
[
  {{"job_num": 1, "verdict": "PASS", "confidence": 0.6}},
  {{"job_num": 2, "verdict": "SKIP", "confidence": 0.95, "reason": "nursing role"}},
  ...
]

Return ONLY the JSON array."""


def parse_round1_response(response: str, num_jobs: int) -> list[dict]:
    """Parse Round 1 filter response."""
    import re
    try:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if not json_match:
            return []
        data = json.loads(json_match.group())
        results = []
        for r in data:
            if isinstance(r, dict) and "job_num" in r:
                results.append({
                    "job_num": r["job_num"],
                    "verdict": r.get("verdict", "PASS").upper(),
                    "confidence": float(r.get("confidence", 0.5)),
                    "reason": r.get("reason", ""),
                })
        return results
    except Exception as e:
        print(f"  Round 1 parse error: {e}")
        return []


def run_round1_filter(jobs: list[dict]) -> tuple[list[dict], list[dict], int]:
    """
    Run MiniMax Round 1 filter on all jobs.
    Returns: (pass_jobs, skipped_jobs, failed_batch_count)
    """
    BATCH_SIZE = 10  # Larger batches for R1 — simpler prompt
    print(f"\n--- Round 1: MiniMax M2.7 pre-filter ({len(jobs)} jobs) ---")

    def process_r1_batch(batch_start):
        batch = jobs[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(jobs) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  R1 batch {batch_num}/{total_batches} ({len(batch)} jobs)...", flush=True)
        prompt = build_round1_prompt(batch)
        print(f"    Prompt: {len(prompt)} chars, calling {MODEL_ROUND1}...", flush=True)
        response = call_llm(prompt, model=MODEL_ROUND1, timeout=120)
        if response:
            results = parse_round1_response(response, len(batch))
            # Offset job_num back to global index
            for r in results:
                r["job_num"] = r["job_num"] + batch_start
            return results, False
        else:
            # LLM failed: pass everything through (safe default)
            fallback = [{"job_num": batch_start + j + 1, "verdict": "PASS", "confidence": 0.0, "reason": "R1 batch failed"} for j in range(len(batch))]
            return fallback, True

    batch_starts = list(range(0, len(jobs), BATCH_SIZE))
    all_r1 = []
    failed_batches = 0

    # Sequential to avoid gateway overload (was max_workers=4, crashed gateway)
    for bs in batch_starts:
        results, failed = process_r1_batch(bs)
        all_r1.extend(results)
        if failed:
            failed_batches += 1

    # Build lookup: job_num -> r1_result
    r1_lookup = {r["job_num"]: r for r in all_r1}

    pass_jobs = []
    skipped_jobs = []

    for i, job in enumerate(jobs, 1):
        r1 = r1_lookup.get(i, {"verdict": "PASS", "confidence": 0.0})
        verdict = r1.get("verdict", "PASS")
        confidence = r1.get("confidence", 0.0)

        # Conservative: only SKIP if verdict=SKIP AND confidence >= floor
        if verdict == "SKIP" and confidence >= R1_CONFIDENCE_FLOOR:
            job["r1_verdict"] = "SKIP"
            job["r1_confidence"] = confidence
            job["r1_reason"] = r1.get("reason", "")
            skipped_jobs.append(job)
        else:
            job["r1_verdict"] = "PASS"
            job["r1_confidence"] = confidence
            pass_jobs.append(job)

    skip_pct = len(skipped_jobs) / max(1, len(jobs)) * 100
    print(f"  Round 1 complete: {len(pass_jobs)} PASS, {len(skipped_jobs)} SKIP ({skip_pct:.0f}% filtered)")
    if failed_batches:
        print(f"  Warning: {failed_batches} R1 batches failed (jobs passed through safely)")

    return pass_jobs, skipped_jobs, failed_batches


# ── ROUND 2: Sonnet quality gate ─────────────────────────────────────────────

def build_round2_prompt(jobs: list[dict]) -> str:
    """Full detailed Round 2 prompt for Sonnet quality verdict."""

    candidate_profile = """
CANDIDATE PROFILE:
- 20+ years technology executive experience (VP/Director/Head/C-level)
- Core strengths: Digital Transformation, PMO/Program Management, Operational Excellence, Business Excellence
- Technical: ERP (SAP, Oracle), Agile/Scrum, ITIL, Cloud Migration, AI/ML Strategy, Data Analytics
- Certifications: PMP, PRINCE2, Six Sigma, ITIL
- Domains: FinTech, HealthTech, E-commerce, Payments, Banking, Insurance, Telecom, Government/Smart City
- Leadership: $50M+ budget management, 200+ person teams, multi-country rollouts, stakeholder management
- Target roles: VP/Director/Head/SVP/C-level in Digital Transformation, PMO, Technology, Operations, Business Excellence
- Target locations: GCC (UAE, Saudi Arabia, Qatar preferred), open to Bahrain, Kuwait, Oman
- Relocation: Ready (currently Egypt, open to relocate to GCC)
- NOT suitable for: Pure sales, HR, hands-on coding, civil/mechanical engineering, oil & gas field operations, teaching, nursing
- RED FLAGS: Junior/mid-level roles, intern, associate, analyst, coordinator, specialist (below Director level)
"""

    jobs_text = ""
    for i, job in enumerate(jobs, 1):
        description = job.get("jd_text", "") or job.get("raw_snippet", "N/A")
        desc_label = "Full JD" if job.get("jd_text") else "Snippet"
        max_desc = 2000 if job.get("jd_text") else 200
        nationals_flag = " [NATIONALS-ONLY - AUTO SKIP]" if job.get("nationals_only") else ""
        r1_note = f" [R1 confidence: {job.get('r1_confidence', 0):.0%}]" if job.get("r1_confidence") else ""
        jobs_text += (
            f"\nJOB {i}:{nationals_flag}{r1_note}\n"
            f"- Title: {job.get('title', 'Unknown')}\n"
            f"- Company: {job.get('company', 'Unknown')}\n"
            f"- Location: {job.get('location', 'Unknown')}\n"
            f"- Seniority: {job.get('seniority', 'Unknown')}\n"
            f"- Domain Match: {job.get('domain_match', False)}\n"
            f"- Keyword Score: {job.get('keyword_score', 0)}\n"
            f"- {desc_label}: {description[:max_desc]}\n"
        )

    return f"""{candidate_profile}

TASK: Final quality review. These jobs passed the Round 1 pre-filter. Give each a definitive verdict.

{jobs_text}

For EACH job, provide:
1. Career Fit Score (1-10)
2. Verdict: SUBMIT (score 7+), REVIEW (score 5-6), or SKIP (score 1-4)
3. One-line reason
4. Salary: Extract any mentioned salary/compensation. Use "N/A" if not mentioned.

OUTPUT FORMAT (JSON array):
[
  {{"job_num": 1, "score": 8, "verdict": "SUBMIT", "reason": "Strong DT leadership role in target geography", "salary": "AED 45,000-55,000/month"}},
  {{"job_num": 2, "score": 4, "verdict": "SKIP", "reason": "Hands-on engineering, not strategic", "salary": "N/A"}},
  ...
]

GOLDEN RULES:
- Always score based on TITLE + COMPANY + LOCATION even when no description is available
- A job titled "Director Digital Transformation" at a GCC company is MINIMUM a 7
- NATIONALS ONLY jobs: score 1, SKIP immediately
- Never score 7+ if it contradicts dealbreakers (junior, wrong field, nationals-only)

SCORING GUIDELINES:
- 9-10: Perfect match - exact target role, GCC location, strong domain
- 7-8: Strong match - right seniority (Director+), relevant domain, target geography
- 5-6: Partial match - right seniority but different domain, or right domain but mid-level
- 3-4: Weak match - some relevance but wrong seniority or geography
- 1-2: No match - junior, wrong field, or nationals-only

Return ONLY the JSON array."""


def parse_round2_response(response: str, num_jobs: int) -> list[dict]:
    """Parse Round 2 Sonnet response."""
    import re
    reviews = []
    try:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                reviews = json.loads(json_match.group())
            except json.JSONDecodeError:
                fixed = json_match.group()
                fixed = re.sub(r',\s*]', ']', fixed)
                fixed = re.sub(r',\s*,', ',', fixed)
                fixed = re.sub(r'}\s*{', '},{', fixed)
                reviews = json.loads(fixed)
        else:
            print("  Warning: Could not find JSON array in Round 2 response")
            return []

        valid = []
        for r in reviews:
            if isinstance(r, dict) and "job_num" in r:
                valid.append({
                    "job_num": r.get("job_num", 0),
                    "score": int(r.get("score", 5)),
                    "verdict": r.get("verdict", "REVIEW"),
                    "reason": r.get("reason", ""),
                    "salary": r.get("salary", "N/A"),
                })
        return valid

    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return []
    except Exception as e:
        print(f"  Parse error: {e}")
        return []


def run_round2_review(pass_jobs: list[dict], submit_threshold: int, review_threshold: int) -> list[dict]:
    """
    Run Sonnet Round 2 quality review on Round 1 survivors.
    Returns jobs with final verdict attached.
    """
    BATCH_SIZE = 5
    print(f"\n--- Round 2: Sonnet 4.6 quality gate ({len(pass_jobs)} jobs) ---")

    def process_r2_batch(batch_start):
        batch = pass_jobs[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        print(f"  Sonnet batch {batch_num} ({len(batch)} jobs, {MODEL_ROUND2})...")
        start_time = time.time()
        prompt = build_round2_prompt(batch)
        response = call_llm(prompt, model=MODEL_ROUND2, timeout=240)
        latency_ms = int((time.time() - start_time) * 1000)
        if response:
            reviews = parse_round2_response(response, len(batch))
            for r in reviews:
                r["job_num"] = r["job_num"] + batch_start
            print(f"    Batch {batch_num}: {len(reviews)} reviews in {latency_ms}ms")
            return reviews, latency_ms, 0
        else:
            print(f"    Batch {batch_num}: Sonnet failed, falling back to keyword scoring")
            fallback = []
            for j, job in enumerate(batch, 1):
                score = min(10, max(1, job.get("keyword_score", 50) // 10))
                verdict = "SUBMIT" if score >= submit_threshold else ("REVIEW" if score >= review_threshold else "SKIP")
                fallback.append({
                    "job_num": j + batch_start,
                    "score": score,
                    "verdict": verdict,
                    "reason": f"[FALLBACK] Keyword score {job.get('keyword_score', 0)} (Sonnet batch {batch_num} failed)",
                    "salary": "N/A",
                })
            return fallback, latency_ms, len(batch)

    batch_starts = list(range(0, len(pass_jobs), BATCH_SIZE))
    all_reviews = []
    total_latency = 0
    fallback_count = 0

    # Sequential to avoid gateway overload (was max_workers=2, crashed gateway)
    for bs in batch_starts:
        reviews, latency, fallbacks = process_r2_batch(bs)
        all_reviews.extend(reviews)
        total_latency += latency
        fallback_count += fallbacks

    # Build lookup
    r2_lookup = {r["job_num"]: r for r in all_reviews}

    # Apply reviews back to jobs
    for i, job in enumerate(pass_jobs, 1):
        r2 = r2_lookup.get(i)
        if r2:
            job["career_fit_score"] = r2["score"]
            job["verdict"] = r2["verdict"]
            job["verdict_reason"] = r2["reason"]
            if r2.get("salary") and r2["salary"] != "N/A":
                job["salary"] = r2["salary"]
        else:
            score = min(10, max(1, job.get("keyword_score", 50) // 10))
            job["career_fit_score"] = score
            job["verdict"] = "SUBMIT" if score >= submit_threshold else ("REVIEW" if score >= review_threshold else "SKIP")
            job["verdict_reason"] = "Default (no Sonnet review for this job)"

    print(f"  Round 2 complete: {total_latency}ms total, {fallback_count} fallbacks")
    return pass_jobs, total_latency, fallback_count


def run_review(result: AgentResult):
    """Main review logic — two-round pipeline."""

    merged_data = load_json(INPUT_FILE, {})
    all_jobs = merged_data.get("data", merged_data.get("jobs", []))

    if not all_jobs:
        result.set_error("No jobs found in merged file")
        return

    print(f"Loaded {len(all_jobs)} merged jobs")

    sorted_jobs = sorted(all_jobs, key=lambda x: x.get("keyword_score", 0), reverse=True)
    top_jobs = sorted_jobs[:TOP_N_JOBS]
    print(f"Selected top {len(top_jobs)} jobs for two-round review")

    submit_threshold, review_threshold = load_feedback_thresholds()

    if is_dry_run():
        print("\n=== DRY RUN: Review Preview ===")
        print(f"\nTop {len(top_jobs)} jobs by keyword score:")
        for i, job in enumerate(top_jobs[:10], 1):
            print(f"  {i}. [{job.get('keyword_score', 0)}] {job.get('title')} @ {job.get('company')}")
        if len(top_jobs) > 10:
            print(f"  ... and {len(top_jobs) - 10} more")
        print(f"\nRound 1 model: {MODEL_ROUND1}")
        print(f"Round 2 model: {MODEL_ROUND2}")
        print(f"Thresholds: SUBMIT >= {submit_threshold}, REVIEW >= {review_threshold}")
        result.set_data([])
        result.set_kpi({"jobs_to_review": len(top_jobs)})
        return

    # ── ROUND 1: MiniMax pre-filter ───────────────────────────────────────────
    pass_jobs, r1_skipped, r1_failed = run_round1_filter(top_jobs)

    # ── ROUND 2: Sonnet quality gate ──────────────────────────────────────────
    reviewed_jobs, r2_latency_ms, r2_fallbacks = run_round2_review(
        pass_jobs, submit_threshold, review_threshold
    )

    # Jobs filtered by Round 1 get automatic SKIP (not shown to Ahmed)
    for job in r1_skipped:
        job["career_fit_score"] = 1
        job["verdict"] = "SKIP"
        job["verdict_reason"] = f"[Round 1 filter] {job.get('r1_reason', 'Filtered by MiniMax')} (confidence {job.get('r1_confidence', 0):.0%})"

    # Guardrail: sanity check Sonnet verdicts against hard title patterns
    SKIP_TITLE_WORDS = ["nurse", "doctor", "physician", "chef", "teacher", "accountant",
                        "receptionist", "secretary", "intern", "trainee", "beautician",
                        "pharmacist", "dentist", "veterinary", "physiotherapist"]
    guardrail_overrides = 0
    for job in reviewed_jobs:
        title_lower = job.get("title", "").lower()
        if job.get("career_fit_score", 0) >= 7 and any(w in title_lower for w in SKIP_TITLE_WORDS):
            job["verdict"] = "SKIP"
            job["verdict_reason"] = f"[GUARDRAIL] Sonnet scored {job['career_fit_score']} but title skip word: {title_lower}"
            job["career_fit_score"] = 2
            guardrail_overrides += 1
    if guardrail_overrides:
        print(f"\n  Guardrail: overrode {guardrail_overrides} false-positive Sonnet scores")

    # Load applied IDs for dedup
    import re as _re
    applied_ids = set()
    print(f"\n  Applied/skipped IDs: Notion is authoritative")

    if _pdb:
        try:
            import sqlite3
            conn = sqlite3.connect(str(Path(__file__).parent / "pipeline_db.py").replace("pipeline_db.py", "../data/nasr-pipeline.db"))
            rows = conn.execute("SELECT job_id FROM jobs WHERE status IN ('applied', 'response', 'interview', 'offer')").fetchall()
            for row in rows:
                applied_ids.add(str(row[0]).replace("li-", ""))
            conn.close()
            print(f"  + DB applied IDs: {len(rows)}")
        except Exception as e:
            print(f"  Warning: Could not load DB applied IDs: {e}")

    try:
        import requests as _requests
        notion_conf = json.load(open(Path(__file__).parent.parent / "config/notion.json"))
        notion_token = notion_conf.get("token")
        if notion_token:
            notion_headers = {"Authorization": f"Bearer {notion_token}", "Notion-Version": "2022-06-28"}
            notion_db_id = "3268d599-a162-81b4-b768-f162adfa4971"
            notion_added = 0
            cursor = None
            while True:
                payload = {"page_size": 100}
                if cursor:
                    payload["start_cursor"] = cursor
                nr = _requests.post(
                    f"https://api.notion.com/v1/databases/{notion_db_id}/query",
                    headers=notion_headers, json=payload, timeout=15
                )
                if nr.status_code != 200:
                    break
                nd = nr.json()
                for page in nd.get("results", []):
                    props = page.get("properties", {})
                    stage = props.get("Stage", {})
                    if stage.get("type") != "select":
                        continue
                    if stage.get("select", {}).get("name", "") not in {"Applied", "Applied"}:
                        continue
                    url_prop = props.get("URL", {})
                    if url_prop.get("type") == "url" and url_prop.get("url"):
                        url_val = url_prop["url"]
                        applied_ids.add(url_val)
                        m = _re.search(r'/jobs/view/(\d+)', url_val)
                        if m:
                            applied_ids.add(m.group(1))
                            notion_added += 1
                if not nd.get("has_more") or not nd.get("next_cursor"):
                    break
                cursor = nd["next_cursor"]
            if notion_added:
                print(f"  + Notion applied IDs: {notion_added}")
    except Exception as e:
        print(f"  Warning: Could not load Notion applied IDs: {e}")

    def _is_already_applied(job):
        jid = str(job.get("id", ""))
        url = job.get("url", "")
        url_ids = _re.findall(r'[a-f0-9]{10,}|\d{8,}', url)
        if jid in applied_ids:
            return True
        for uid in url_ids:
            if uid in applied_ids:
                return True
        return False

    # Categorize final verdicts
    submit_jobs = []
    review_jobs = []
    skip_jobs = []
    applied_filtered = 0

    all_final = reviewed_jobs + r1_skipped

    for job in all_final:
        if _is_already_applied(job) and job.get("verdict") in ("SUBMIT", "REVIEW"):
            old_verdict = job["verdict"]
            job["verdict"] = "SKIP"
            job["verdict_reason"] = f"Already applied/skipped (was {old_verdict})"
            applied_filtered += 1

        if job.get("verdict") == "SUBMIT":
            submit_jobs.append(job)
        elif job.get("verdict") == "REVIEW":
            review_jobs.append(job)
        else:
            skip_jobs.append(job)

    if applied_filtered:
        print(f"  Filtered {applied_filtered} already-applied jobs from SUBMIT/REVIEW")

    avg_score = sum(j.get("career_fit_score", 0) for j in reviewed_jobs) / max(1, len(reviewed_jobs))

    print(f"\nFinal results:")
    print(f"  Round 1 filtered: {len(r1_skipped)}")
    print(f"  SUBMIT: {len(submit_jobs)}")
    print(f"  REVIEW: {len(review_jobs)}")
    print(f"  SKIP (Round 2): {len([j for j in skip_jobs if j.get('r1_verdict') != 'SKIP'])}")
    print(f"  Avg Sonnet score: {avg_score:.1f}")

    # ATS scoring for SUBMIT + REVIEW jobs
    print(f"\nRunning ATS scoring on {len(submit_jobs) + len(review_jobs)} jobs...")
    try:
        from importlib.util import spec_from_file_location, module_from_spec
        ats_spec = spec_from_file_location("job_scorer", str(Path(__file__).parent / "job-scorer.py"))
        ats_mod = module_from_spec(ats_spec)
        ats_spec.loader.exec_module(ats_mod)

        for job in submit_jobs + review_jobs:
            content = job.get("jd_page_text", "") or job.get("jd_text", "")
            if content and len(content) > 200:
                ats_result = ats_mod.calculate_score(content)
            else:
                fallback = f"{job.get('title','')} {job.get('raw_snippet','')} {job.get('company','')}"
                ats_result = ats_mod.calculate_score(fallback)
                ats_result["verdict"] = ats_result["verdict"] + "_TITLE_ONLY"

            job["ats_score"] = ats_result.get("score", 0)
            job["ats_verdict"] = ats_result.get("verdict", "?")
            job["ats_matched"] = ats_result.get("matched", [])[:10]
            job["ats_gaps"] = ats_result.get("gaps", [])[:5]
            print(f"  ATS: {job['ats_score']:3d}/100 | {job.get('title','?')[:40]}")

        submit_jobs.sort(key=lambda x: x.get("ats_score", 0), reverse=True)
        review_jobs.sort(key=lambda x: x.get("ats_score", 0), reverse=True)
        print(f"  ATS scoring complete")
    except Exception as e:
        print(f"  ATS scoring failed (non-fatal): {e}")

    # Liveness check
    print(f"\nChecking SUBMIT job liveness...")
    live_submit = []
    expired_count = 0
    for job in submit_jobs:
        if job.get("jd_fetch_status") in ("expired", "stale") or job.get("jd_live") is False:
            expired_count += 1
            print(f"  Expired: {job.get('title','?')[:50]}")
        else:
            live_submit.append(job)
    if expired_count:
        print(f"  Removed {expired_count} expired jobs from SUBMIT")
    submit_jobs = live_submit

    # Write recommended log
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    with open(RECOMMENDED_FILE, "a") as f:
        for job in submit_jobs + review_jobs:
            entry = {
                "timestamp": now_iso(),
                "job_id": job.get("id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "url": job.get("url"),
                "verdict": job.get("verdict"),
                "score": job.get("career_fit_score"),
                "reason": job.get("verdict_reason"),
            }
            f.write(json.dumps(entry) + "\n")

    # Build summary output
    remaining_jobs = sorted_jobs[TOP_N_JOBS:]
    for job in remaining_jobs:
        job["career_fit_score"] = 0
        job["verdict"] = "UNREVIEWED"
        job["verdict_reason"] = "Beyond review limit"

    summary = {
        "generated_at": now_iso(),
        "total_candidates": len(all_jobs),
        "reviewed": len(reviewed_jobs),
        "submit": submit_jobs,
        "review": review_jobs,
        "skip_count": len(skip_jobs),
        "unreviewed_count": len(remaining_jobs),
        "thresholds": {"submit": submit_threshold, "review": review_threshold},
        "pipeline": {
            "r1_model": MODEL_ROUND1,
            "r2_model": MODEL_ROUND2,
            "r1_filtered": len(r1_skipped),
            "r1_passed": len(pass_jobs),
            "r1_failed_batches": r1_failed,
            "r2_latency_ms": r2_latency_ms,
            "r2_fallbacks": r2_fallbacks,
        },
        "kpi": {
            "submit_rate": len(submit_jobs) / max(1, len(reviewed_jobs)),
            "review_rate": len(review_jobs) / max(1, len(reviewed_jobs)),
            "skip_rate": len(skip_jobs) / max(1, len(reviewed_jobs)),
            "avg_fit_score": round(avg_score, 1),
            "r1_filter_rate": round(len(r1_skipped) / max(1, len(top_jobs)) * 100, 1),
        }
    }

    # DB write (non-blocking)
    if _pdb:
        try:
            db_count = 0
            for job in submit_jobs + review_jobs + skip_jobs:
                job_id = str(job.get("id", job.get("job_id", ""))).strip()
                if not job_id:
                    continue
                _pdb.update_score(
                    job_id=job_id,
                    ats_score=int(job["ats_score"]) if job.get("ats_score") is not None else None,
                    fit_score=int(job.get("career_fit_score", 0)),
                    verdict=job.get("verdict"),
                    notes=str(job.get("verdict_reason", ""))[:500],
                )
                db_count += 1
            print(f"  DB: {db_count} scores written")
        except Exception as _e:
            print(f"  DB write failed (non-fatal): {_e}")

    result.set_data(summary)
    result.set_kpi({
        "submit_count": len(submit_jobs),
        "review_count": len(review_jobs),
        "skip_count": len(skip_jobs),
        "r1_filtered": len(r1_skipped),
        "submit_rate": round(len(submit_jobs) / max(1, len(reviewed_jobs)) * 100, 1),
        "avg_fit_score": round(avg_score, 1),
        "r2_latency_ms": r2_latency_ms,
    })


def main():
    """Entry point."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(
        agent_name=AGENT_NAME,
        run_func=run_review,
        output_path=OUTPUT_FILE,
        ttl_hours=6,
        version="2.0.0"
    )


if __name__ == "__main__":
    main()
