#!/usr/bin/env python3
"""
Score all promising jobs from scout results
Fetches full JD via linkedin-jd-fetcher.py, scores with scout-ats.py
Output: /tmp/scout-scored-all.json + table to stdout
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

SKIP_IDS = {
    '4381416802',  # eMagine Head of AI Advisory - Applied 2026-03-05
    '4379857033',  # Nuxera Sr PM AI Healthcare - Applied 2026-03-05
    '4325582215',  # Emdad Director Digital Innovation - Applied 2026-03-05
    '4379328713',  # Confidential Gov Exec Director DT - Applied 2026-03-05
    '4363211150',  # EDB Field CTO EMEA - Applied 2026-03-05
}
SCRIPT_DIR = Path(__file__).parent
JD_FETCHER = SCRIPT_DIR / "linkedin-jd-fetcher.py"
ATS_SCORER = SCRIPT_DIR / "scout-ats.py"


async def fetch_and_score(job):
    """Fetch JD and score a single job"""
    jid = job["id"]
    url = f"https://www.linkedin.com/jobs/view/{jid}"
    
    # Fetch JD
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", str(JD_FETCHER), url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=40)
        jd_data = json.loads(stdout.decode())
        jd = jd_data.get("jd", "")
    except Exception as e:
        return {**job, "ats_score": 0, "verdict": "NO JD", "reason": str(e)[:50]}
    
    if not jd or len(jd) < 100:
        return {**job, "ats_score": 0, "verdict": "NO JD", "reason": "empty"}
    
    # Save JD to temp file
    jd_file = f"/tmp/jd-score-{jid}.txt"
    Path(jd_file).write_text(jd)
    
    # Score
    try:
        loc = job.get("location", "")
        proc2 = await asyncio.create_subprocess_exec(
            "python3", str(ATS_SCORER), jd_file, "--location", loc,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout2, _ = await asyncio.wait_for(proc2.communicate(), timeout=10)
        output = stdout2.decode()
        
        for line in output.split("\n"):
            if line.startswith("__JSON__:"):
                score_data = json.loads(line.replace("__JSON__:", ""))
                return {**job, "ats_score": score_data["score"], "verdict": score_data["verdict"], "breakdown": score_data.get("breakdown", {}), "jd_length": len(jd)}
        
        return {**job, "ats_score": 0, "verdict": "PARSE ERROR", "reason": "no JSON"}
    except Exception as e:
        return {**job, "ats_score": 0, "verdict": "ERROR", "reason": str(e)[:50]}


async def main():
    with open("/tmp/scout-promising.json") as f:
        jobs = json.load(f)
    
    # Deduplicate by company+title
    seen = set()
    unique = []
    for j in jobs:
        key = f"{j['company']}|{j['title']}"
        if key not in seen and j["id"] not in SKIP_IDS:
            seen.add(key)
            unique.append(j)
    
    print(f"Scoring {len(unique)} unique jobs (sequential to avoid LinkedIn rate limits)...")
    
    results = []
    for i, job in enumerate(unique):
        sys.stdout.write(f"\r[{i+1}/{len(unique)}] {job['title'][:50]}...")
        sys.stdout.flush()
        result = await fetch_and_score(job)
        results.append(result)
        # Small delay between fetches
        await asyncio.sleep(0.5)
    
    # Sort by score
    results.sort(key=lambda x: x["ats_score"], reverse=True)
    
    # Save full results
    with open("/tmp/scout-scored-all.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print table
    print(f"\n\n{'='*120}")
    print(f"{'#':>2} | {'Score':>5} | {'Verdict':11} | {'Role':<50} | {'Company':<25} | {'Location':<30}")
    print(f"{'-'*2}-+-{'-'*5}-+-{'-'*11}-+-{'-'*50}-+-{'-'*25}-+-{'-'*30}")
    
    for i, r in enumerate(results, 1):
        emoji = "🟢" if r["verdict"] == "GO" else "🟡" if r["verdict"] == "REVIEW" else "🟠" if r["verdict"] == "CONDITIONAL" else "🔴"
        print(f"{i:2} | {r['ats_score']:4d}% | {emoji} {r['verdict']:9} | {r['title'][:50]:<50} | {r['company'][:25]:<25} | {r.get('location','')[:30]}")
    
    # Summary
    go = sum(1 for r in results if r["verdict"] == "GO")
    review = sum(1 for r in results if r["verdict"] == "REVIEW")
    cond = sum(1 for r in results if r["verdict"] == "CONDITIONAL")
    skip = sum(1 for r in results if r["verdict"] in ("SKIP", "NO JD", "ERROR", "PARSE ERROR"))
    print(f"\n🟢 GO: {go} | 🟡 REVIEW: {review} | 🟠 CONDITIONAL: {cond} | 🔴 SKIP: {skip}")


if __name__ == "__main__":
    asyncio.run(main())
