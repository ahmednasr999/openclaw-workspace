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
TOP_N_JOBS = 50
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


def call_llm(prompt: str, timeout: int = 120) -> str | None:
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
- 20+ years technology executive experience
- Core strengths: Digital Transformation, PMO/Program Management, Operational Excellence
- Domains: FinTech, HealthTech, E-commerce, Payments
- Target roles: VP/Director/Head of Digital Transformation, PMO, Technology
- Target locations: GCC (UAE, Saudi Arabia, Qatar preferred)
- Not suitable for: Pure sales, HR, hands-on coding, civil engineering, oil & gas operations
"""
    
    jobs_text = ""
    for i, job in enumerate(jobs, 1):
        jobs_text += f"""
JOB {i}:
- Title: {job.get('title', 'Unknown')}
- Company: {job.get('company', 'Unknown')}
- Location: {job.get('location', 'Unknown')}
- Seniority: {job.get('seniority', 'Unknown')}
- Domain Match: {job.get('domain_match', False)}
- Keyword Score: {job.get('keyword_score', 0)}
- Snippet: {job.get('raw_snippet', 'N/A')[:200]}
"""
    
    prompt = f"""{candidate_profile}

TASK: Review these {len(jobs)} jobs and score each for career fit.

{jobs_text}

For EACH job, provide:
1. Career Fit Score (1-10): How well does this role match the candidate's profile?
2. Verdict: SUBMIT (score 7+), REVIEW (score 5-6), or SKIP (score 1-4)
3. One-line reason

OUTPUT FORMAT (JSON array):
[
  {{"job_num": 1, "score": 8, "verdict": "SUBMIT", "reason": "Strong DT leadership role in target geography"}},
  {{"job_num": 2, "score": 4, "verdict": "SKIP", "reason": "Hands-on engineering focus, not strategic"}},
  ...
]

SCORING GUIDELINES:
- 9-10: Perfect match - exact target role, target location, strong domain fit
- 7-8: Strong match - right seniority, good domain, minor gaps
- 5-6: Partial match - right seniority but weak domain fit, or stretch role
- 3-4: Weak match - some relevance but significant gaps
- 1-2: No match - wrong domain, wrong seniority, or anti-pattern role

Return ONLY the JSON array, no other text."""
    
    return prompt


def parse_llm_response(response: str, num_jobs: int) -> list[dict]:
    """Parse LLM response into structured reviews."""
    import re
    
    reviews = []
    
    try:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            reviews = json.loads(json_match.group())
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
    
    prompt = build_review_prompt(top_jobs)
    print(f"Calling LLM ({MODEL})...")
    
    start_time = time.time()
    response = call_llm(prompt)
    llm_latency_ms = int((time.time() - start_time) * 1000)
    
    if not response:
        print("  LLM failed, falling back to keyword-based classification")
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
        reviews = parse_llm_response(response, len(top_jobs))
        print(f"  LLM returned {len(reviews)} reviews in {llm_latency_ms}ms")
    
    reviewed_jobs = []
    submit_jobs = []
    review_jobs = []
    skip_jobs = []
    
    for i, job in enumerate(top_jobs, 1):
        review = next((r for r in reviews if r.get("job_num") == i), None)
        
        if review:
            job["career_fit_score"] = review["score"]
            job["verdict"] = review["verdict"]
            job["verdict_reason"] = review["reason"]
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
        
        reviewed_jobs.append(job)
        
        if job["verdict"] == "SUBMIT":
            submit_jobs.append(job)
        elif job["verdict"] == "REVIEW":
            review_jobs.append(job)
        else:
            skip_jobs.append(job)
    
    remaining_jobs = sorted_jobs[TOP_N_JOBS:]
    for job in remaining_jobs:
        job["career_fit_score"] = 0
        job["verdict"] = "UNREVIEWED"
        job["verdict_reason"] = "Below top 50, not LLM reviewed"
    
    avg_score = sum(j.get("career_fit_score", 0) for j in reviewed_jobs) / max(1, len(reviewed_jobs))
    
    print(f"\nReview results:")
    print(f"  SUBMIT: {len(submit_jobs)}")
    print(f"  REVIEW: {len(review_jobs)}")
    print(f"  SKIP: {len(skip_jobs)}")
    print(f"  Avg score: {avg_score:.1f}")
    
    # ATS scoring for SUBMIT + REVIEW jobs
    print(f"\nRunning ATS scoring on {len(submit_jobs) + len(review_jobs)} jobs...")
    try:
        from importlib.util import spec_from_file_location, module_from_spec
        ats_spec = spec_from_file_location("ats_scorer", str(Path(__file__).parent / "ats-scorer.py"))
        ats_mod = module_from_spec(ats_spec)
        ats_spec.loader.exec_module(ats_mod)
        
        import urllib.request as _urllib_req
        
        for job in submit_jobs + review_jobs:
            url = job.get("url", "")
            if not url:
                job["ats_score"] = 0
                job["ats_verdict"] = "NO_URL"
                continue
            try:
                req = _urllib_req.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                })
                with _urllib_req.urlopen(req, timeout=15) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")
                    content = re.sub(r'<script[^>]*>.*?</script>', ' ', raw, flags=re.DOTALL)
                    content = re.sub(r'<style[^>]*>.*?</style>', ' ', content, flags=re.DOTALL)
                    content = re.sub(r'<[^>]+>', ' ', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                if content and len(content) > 200:
                    ats_result = ats_mod.calculate_score(content)
                else:
                    # Fallback: score from title
                    fallback = f"{job.get('title','')} {job.get('raw_snippet','')} {job.get('company','')}"
                    ats_result = ats_mod.calculate_score(fallback)
                    ats_result["verdict"] = ats_result["verdict"] + "_TITLE_ONLY"
                
                job["ats_score"] = ats_result.get("score", 0)
                job["ats_verdict"] = ats_result.get("verdict", "?")
                job["ats_matched"] = ats_result.get("matched", [])[0:10]
                job["ats_gaps"] = ats_result.get("gaps", [])[0:5]
            except Exception:
                # Fallback to title-based scoring
                fallback = f"{job.get('title','')} {job.get('raw_snippet','')} {job.get('company','')}"
                ats_result = ats_mod.calculate_score(fallback)
                job["ats_score"] = ats_result.get("score", 0)
                job["ats_verdict"] = ats_result.get("verdict", "?") + "_TITLE_ONLY"
                job["ats_matched"] = ats_result.get("matched", [])[0:10]
                job["ats_gaps"] = ats_result.get("gaps", [])[0:5]
            
            print(f"  ATS: {job['ats_score']:3d}/100 | {job.get('title','?')[0:40]}")
        
        # Re-sort by ATS score within categories
        submit_jobs.sort(key=lambda x: x.get("ats_score", 0), reverse=True)
        review_jobs.sort(key=lambda x: x.get("ats_score", 0), reverse=True)
        print(f"  ATS scoring complete")
    except Exception as e:
        print(f"  ATS scoring failed (non-fatal): {e}")
    
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
