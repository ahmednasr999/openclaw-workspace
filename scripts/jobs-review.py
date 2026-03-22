#!/usr/bin/env python3
"""
jobs-review.py — Layer 3: LLM-based career fit review of merged jobs.

Reads: data/jobs-merged.json
Writes: data/jobs-summary.json (final output for Brief Me)
        data/feedback/jobs-recommended.jsonl

Features:
  - Takes top 50 jobs by keyword_score
  - Uses MiniMax-M2.7 via OpenClaw gateway for LLM review
  - Batches all jobs in one prompt
  - Career fit score 1-10 + verdict (SUBMIT/REVIEW/SKIP) + reason
  - Loads past feedback from jobs-outcomes.jsonl to adjust thresholds
"""

import json
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

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
MODEL = "minimax-portal/MiniMax-M2.7"

# Review settings
TOP_N_JOBS = 300  # Review all candidates (MiniMax-M2.7 is free, parallel batches keep it fast)
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


def call_llm(prompt: str, timeout: int = 240) -> str | None:
    """Call OpenClaw gateway with LLM request."""
    try:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }
        
        # Load gateway auth token
        import json as _json
        try:
            with open("/root/.openclaw/openclaw.json") as _f:
                _cfg = _json.load(_f)
            gw_token = _cfg.get("gateway", {}).get("auth", {}).get("token", "")
        except Exception:
            gw_token = ""
        
        headers = {"Content-Type": "application/json"}
        if gw_token:
            headers["Authorization"] = f"Bearer {gw_token}"
        
        resp = requests.post(GATEWAY_URL, json=payload, headers=headers, timeout=timeout)
        
        if resp.status_code != 200:
            print(f"  LLM error: HTTP {resp.status_code}")
            return None
        
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content
        
    except requests.exceptions.Timeout:
        print(f"  LLM timeout ({timeout}s)")
        return None
    except Exception as e:
        print(f"  LLM error: {e}")
        return None


def build_review_prompt(jobs: list[dict]) -> str:
    """Build the LLM review prompt for batch job evaluation."""
    
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
        # Use full JD text if available (from jobs-enrich-jd.py), else fall back to snippet
        description = job.get('jd_text', '') or job.get('raw_snippet', 'N/A')
        desc_label = "Full JD" if job.get('jd_text') else "Snippet"
        # Send more JD context — MiniMax-M2.7 is free, no reason to cut aggressively
        max_desc = 2000 if job.get('jd_text') else 200
        nationals_flag = " ⚠️ NATIONALS-ONLY DETECTED" if job.get('nationals_only') else ""
        jobs_text += f"""
JOB {i}:{nationals_flag}
- Title: {job.get('title', 'Unknown')}
- Company: {job.get('company', 'Unknown')}
- Location: {job.get('location', 'Unknown')}
- Seniority: {job.get('seniority', 'Unknown')}
- Domain Match: {job.get('domain_match', False)}
- Keyword Score: {job.get('keyword_score', 0)}
- {desc_label}: {description[:max_desc]}
"""
    
    prompt = f"""{candidate_profile}

TASK: Review these {len(jobs)} jobs and score each for career fit.

{jobs_text}

For EACH job, provide:
1. Career Fit Score (1-10): How well does this role match the candidate's profile?
2. Verdict: SUBMIT (score 7+), REVIEW (score 5-6), or SKIP (score 1-4)
3. One-line reason
4. Salary: Extract any mentioned salary/compensation (e.g. "$150K-200K", "AED 40,000/month", "competitive"). Use "N/A" if not mentioned.

OUTPUT FORMAT (JSON array):
[
  {{"job_num": 1, "score": 8, "verdict": "SUBMIT", "reason": "Strong DT leadership role in target geography", "salary": "AED 45,000-55,000/month"}},
  {{"job_num": 2, "score": 4, "verdict": "SKIP", "reason": "Hands-on engineering focus, not strategic", "salary": "N/A"}},
  ...
]


═══════════════════════════════════════════════════════════
GOLDEN RULES (DO NOT MODIFY — permanent constraints):
- Always score based on TITLE + COMPANY + LOCATION even when no description is available
- Never penalize a job for missing description — title is the primary signal
- A job titled "Director Digital Transformation" at a GCC company is MINIMUM a 7
- Never score a role 7+ if it contradicts the dealbreakers below
═══════════════════════════════════════════════════════════


AUTO-LEARNED EXCLUSION RULES (v1):

DEALBREAKER — NATIONALS ONLY (AUTOMATIC SKIP):
- If title or description contains ANY of the following, score 1 and SKIP immediately:
  "nationals only", "UAE national", "Emirati only", "Saudi only", "Kuwaiti national",
  "Bahraini national", "Qatari national", "Omani national", "citizen only", "GCC national"
- These roles are legally restricted and cannot be applied for. Do NOT score them 7+.
- Pattern to detect: parenthetical like "(UAE Nationals Only)" or dash like "– UAE National"


SCORING GUIDELINES:
- 9-10: Perfect match - exact target role (DT Director, VP PMO, Head of Technology), target location (GCC), strong domain
- 7-8: Strong match - right seniority (Director/VP/Head/SVP/C-level), relevant domain, target geography
- 5-6: Partial match - right seniority but different domain, or right domain but mid-level title
- 3-4: Weak match - some relevance but wrong seniority or wrong geography
- 1-2: No match - junior role, wrong field entirely, or anti-pattern (pure sales/HR/civil)

IMPORTANT: Score based on TITLE + COMPANY + LOCATION even when no description is available.
A job titled "Director Digital Transformation" at a GCC company is at MINIMUM a 7 based on title alone.
Do NOT penalize jobs for missing descriptions - the title is the primary signal.

Return ONLY the JSON array, no other text."""
    
    return prompt


def parse_llm_response(response: str, num_jobs: int) -> list[dict]:
    """Parse LLM response into structured reviews."""
    import re
    
    reviews = []
    
    try:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                reviews = json.loads(json_match.group())
            except json.JSONDecodeError:
                # Try fixing common LLM JSON errors
                fixed = json_match.group()
                fixed = re.sub(r',\s*]', ']', fixed)  # trailing comma
                fixed = re.sub(r',\s*,', ',', fixed)   # double comma
                fixed = re.sub(r'}\s*{', '},{', fixed)  # missing comma between objects
                reviews = json.loads(fixed)
        else:
            print("  Warning: Could not find JSON array in LLM response")
            return []
        
        valid_reviews = []
        for r in reviews:
            if isinstance(r, dict) and "job_num" in r:
                valid_reviews.append({
                    "job_num": r.get("job_num", 0),
                    "score": int(r.get("score", 5)),
                    "verdict": r.get("verdict", "REVIEW"),
                    "reason": r.get("reason", ""),
                })
        
        return valid_reviews
        
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return []
    except Exception as e:
        print(f"  Parse error: {e}")
        return []


def run_review(result: AgentResult):
    """Main review logic."""
    
    merged_data = load_json(INPUT_FILE, {})
    all_jobs = merged_data.get("data", merged_data.get("jobs", []))
    
    if not all_jobs:
        result.set_error("No jobs found in merged file")
        return
    
    print(f"Loaded {len(all_jobs)} merged jobs")
    
    sorted_jobs = sorted(all_jobs, key=lambda x: x.get("keyword_score", 0), reverse=True)
    top_jobs = sorted_jobs[:TOP_N_JOBS]
    
    print(f"Selected top {len(top_jobs)} jobs for LLM review")
    
    submit_threshold, review_threshold = load_feedback_thresholds()
    
    if is_dry_run():
        print("\n=== DRY RUN: Review Preview ===")
        print(f"\nTop {len(top_jobs)} jobs by keyword score:")
        for i, job in enumerate(top_jobs[:10], 1):
            print(f"  {i}. [{job.get('keyword_score', 0)}] {job.get('title')} @ {job.get('company')}")
        if len(top_jobs) > 10:
            print(f"  ... and {len(top_jobs) - 10} more")
        
        print(f"\nLLM: {MODEL}")
        print(f"Thresholds: SUBMIT >= {submit_threshold}, REVIEW >= {review_threshold}")
        
        result.set_data([])
        result.set_kpi({
            "jobs_to_review": len(top_jobs),
            "submit_threshold": submit_threshold,
            "review_threshold": review_threshold,
        })
        return
    
    # Split into batches of 25 for more reliable LLM JSON output
    BATCH_SIZE = 25
    
    # Parallelize batches using ThreadPoolExecutor
    def process_batch(batch_start):
        batch = top_jobs[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        print(f"Calling LLM batch {batch_num} ({len(batch)} jobs, {MODEL})...")
        start_time = time.time()
        prompt = build_review_prompt(batch)
        response = call_llm(prompt)
        batch_latency = int((time.time() - start_time) * 1000)
        if response:
            batch_reviews = parse_llm_response(response, len(batch))
            for r in batch_reviews:
                r["job_num"] = r["job_num"] + batch_start
            print(f"  Batch {batch_num}: {len(batch_reviews)} reviews in {batch_latency}ms")
            return batch_reviews, batch_latency, 0
        else:
            # Fallback: keyword-based scoring for this batch (never drop jobs silently)
            print(f"  Batch {batch_num}: LLM failed, falling back to keyword scoring")
            fallback_reviews = []
            for j, job in enumerate(batch, 1):
                score = min(10, max(1, job.get("keyword_score", 50) // 10))
                if score >= 7:
                    verdict = "SUBMIT"
                elif score >= 5:
                    verdict = "REVIEW"
                else:
                    verdict = "SKIP"
                fallback_reviews.append({
                    "job_num": j + batch_start,
                    "score": score,
                    "verdict": verdict,
                    "reason": f"Keyword-based (batch {batch_num} LLM failed): score {job.get('keyword_score', 0)}",
                    "salary": "N/A",
                })
            return fallback_reviews, batch_latency, len(batch)

    batch_starts = list(range(0, len(top_jobs), BATCH_SIZE))
    all_reviews = []
    total_latency = 0
    fallback_count = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(process_batch, bs): bs for bs in batch_starts}
        for future in as_completed(futures):
            batch_reviews, batch_latency, batch_fallbacks = future.result()
            total_latency += batch_latency
            fallback_count += batch_fallbacks
            all_reviews.extend(batch_reviews)
    
    llm_latency_ms = total_latency
    
    # Use all_reviews collected from parallel batches
    reviews = all_reviews
    
    if not reviews:
        print("  All LLM batches failed, falling back to keyword-based classification")
        reviews = []
        for i, job in enumerate(top_jobs, 1):
            score = min(10, max(1, job.get("keyword_score", 50) // 10))
            if score >= submit_threshold:
                verdict = "SUBMIT"
            elif score >= review_threshold:
                verdict = "REVIEW"
            else:
                verdict = "SKIP"
            reviews.append({
                "job_num": i,
                "score": score,
                "verdict": verdict,
                "reason": f"Keyword-based (LLM unavailable): score {job.get('keyword_score', 0)}"
            })
    else:
        print(f"  LLM returned {len(reviews)} reviews in {llm_latency_ms}ms")
    
    # Load applied/skipped IDs for final guard
    import re as _re
    APPLIED_IDS_FILE = Path(__file__).parent.parent / "jobs-bank" / "applied-job-ids.txt"
    applied_ids = set()
    try:
        if APPLIED_IDS_FILE.exists():
            for line in open(APPLIED_IDS_FILE):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("|")
                if parts:
                    aid = parts[0].strip()
                    if aid and len(aid) >= 6:
                        applied_ids.add(aid)
        print(f"\n  Applied/skipped IDs loaded: {len(applied_ids)}")
    except Exception as e:
        print(f"  Warning: Could not load applied IDs: {e}")

    def _is_already_applied(job):
        """Check if job ID or URL numeric IDs match applied list."""
        jid = str(job.get("id", ""))
        url = job.get("url", "")
        # Extract numeric/hex IDs from URL
        url_ids = _re.findall(r'[a-f0-9]{10,}|\d{8,}', url)
        if jid in applied_ids:
            return True
        for uid in url_ids:
            if uid in applied_ids:
                return True
        return False

    reviewed_jobs = []
    submit_jobs = []
    review_jobs = []
    skip_jobs = []
    applied_filtered = 0
    
    for i, job in enumerate(top_jobs, 1):
        review = next((r for r in reviews if r.get("job_num") == i), None)
        
        if review:
            job["career_fit_score"] = review["score"]
            job["verdict"] = review["verdict"]
            job["verdict_reason"] = review["reason"]
            salary = review.get("salary", "N/A")
            if salary and salary != "N/A":
                job["salary"] = salary
        else:
            score = min(10, max(1, job.get("keyword_score", 50) // 10))
            job["career_fit_score"] = score
            if score >= submit_threshold:
                job["verdict"] = "SUBMIT"
            elif score >= review_threshold:
                job["verdict"] = "REVIEW"
            else:
                job["verdict"] = "SKIP"
            job["verdict_reason"] = "Default (no LLM review)"
        
        # Final guard: skip already applied/skipped jobs
        if _is_already_applied(job) and job["verdict"] in ("SUBMIT", "REVIEW"):
            old_verdict = job["verdict"]
            job["verdict"] = "SKIP"
            job["verdict_reason"] = f"Already applied/skipped (was {old_verdict})"
            applied_filtered += 1
        
        reviewed_jobs.append(job)
        
        if job["verdict"] == "SUBMIT":
            submit_jobs.append(job)
        elif job["verdict"] == "REVIEW":
            review_jobs.append(job)
        else:
            skip_jobs.append(job)
    
    if applied_filtered > 0:
        print(f"  Filtered {applied_filtered} already-applied/skipped jobs from SUBMIT/REVIEW")
    
    remaining_jobs = sorted_jobs[TOP_N_JOBS:]
    for job in remaining_jobs:
        job["career_fit_score"] = 0
        job["verdict"] = "UNREVIEWED"
        job["verdict_reason"] = "Beyond review limit, not LLM reviewed"
    
    avg_score = sum(j.get("career_fit_score", 0) for j in reviewed_jobs) / max(1, len(reviewed_jobs))
    
    print(f"\nReview results:")
    print(f"  SUBMIT: {len(submit_jobs)}")
    print(f"  REVIEW: {len(review_jobs)}")
    print(f"  SKIP: {len(skip_jobs)}")
    print(f"  Avg score: {avg_score:.1f}")
    
    # ATS scoring for SUBMIT + REVIEW jobs — uses enriched data from jobs-enrich-jd.py (no re-fetch)
    print(f"\nRunning ATS scoring on {len(submit_jobs) + len(review_jobs)} jobs (using enriched data)...")
    try:
        from importlib.util import spec_from_file_location, module_from_spec
        ats_spec = spec_from_file_location("job_scorer", str(Path(__file__).parent / "job-scorer.py"))
        ats_mod = module_from_spec(ats_spec)
        ats_spec.loader.exec_module(ats_mod)
        
        for job in submit_jobs + review_jobs:
            # Use pre-fetched page text from enrich step (single source of truth)
            content = job.get("jd_page_text", "") or job.get("jd_text", "")
            
            if content and len(content) > 200:
                ats_result = ats_mod.calculate_score(content)
            else:
                # Fallback: score from title + snippet only
                fallback = f"{job.get('title','')} {job.get('raw_snippet','')} {job.get('company','')}"
                ats_result = ats_mod.calculate_score(fallback)
                ats_result["verdict"] = ats_result["verdict"] + "_TITLE_ONLY"
            
            job["ats_score"] = ats_result.get("score", 0)
            job["ats_verdict"] = ats_result.get("verdict", "?")
            job["ats_matched"] = ats_result.get("matched", [])[0:10]
            job["ats_gaps"] = ats_result.get("gaps", [])[0:5]
            
            print(f"  ATS: {job['ats_score']:3d}/100 | {job.get('title','?')[0:40]}")
        
        # Re-sort by ATS score within categories
        submit_jobs.sort(key=lambda x: x.get("ats_score", 0), reverse=True)
        review_jobs.sort(key=lambda x: x.get("ats_score", 0), reverse=True)
        print(f"  ATS scoring complete")
    except Exception as e:
        print(f"  ATS scoring failed (non-fatal): {e}")
    
    # Liveness check — uses enriched data from jobs-enrich-jd.py (no re-fetch)
    print(f"\nChecking SUBMIT job liveness (from enriched data)...")
    live_submit = []
    expired_count = 0
    
    for job in submit_jobs:
        fetch_status = job.get("jd_fetch_status", "")
        jd_live = job.get("jd_live")
        
        if fetch_status in ("expired", "stale"):
            expired_count += 1
            print(f"  ❌ {fetch_status.upper()}: {job.get('title','?')[:50]}")
        elif jd_live is False:
            expired_count += 1
            print(f"  ❌ NOT LIVE: {job.get('title','?')[:50]}")
        else:
            # jd_live=True, or no enrichment data (not in top 50) — keep it
            live_submit.append(job)
    
    if expired_count:
        print(f"  Removed {expired_count} expired/stale jobs from SUBMIT")
    submit_jobs = live_submit
    
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
    
    summary = {
        "generated_at": now_iso(),
        "total_candidates": len(all_jobs),
        "reviewed": len(reviewed_jobs),
        "submit": submit_jobs,
        "review": review_jobs,
        "skip_count": len(skip_jobs),
        "unreviewed_count": len(remaining_jobs),
        "thresholds": {
            "submit": submit_threshold,
            "review": review_threshold,
        },
        "kpi": {
            "submit_rate": len(submit_jobs) / max(1, len(reviewed_jobs)),
            "review_rate": len(review_jobs) / max(1, len(reviewed_jobs)),
            "skip_rate": len(skip_jobs) / max(1, len(reviewed_jobs)),
            "avg_fit_score": round(avg_score, 1),
            "llm_latency_ms": llm_latency_ms,
            "fallback_count": fallback_count,
            "fallback_pct": round(fallback_count / max(1, len(reviewed_jobs)) * 100, 1),
        }
    }
    
    result.set_data(summary)
    result.set_kpi({
        "submit_count": len(submit_jobs),
        "review_count": len(review_jobs),
        "skip_count": len(skip_jobs),
        "submit_rate": round(len(submit_jobs) / max(1, len(reviewed_jobs)) * 100, 1),
        "review_rate": round(len(review_jobs) / max(1, len(reviewed_jobs)) * 100, 1),
        "skip_rate": round(len(skip_jobs) / max(1, len(reviewed_jobs)) * 100, 1),
        "avg_fit_score": round(avg_score, 1),
        "llm_latency_ms": llm_latency_ms,
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
        version="1.0.0"
    )


if __name__ == "__main__":
    main()
