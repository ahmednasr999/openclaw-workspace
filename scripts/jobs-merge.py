#!/usr/bin/env python3
"""
jobs-merge.py — Layer 2: Merge and deduplicate jobs from all source adapters.

Reads: data/jobs-raw/*.json
Writes: data/jobs-merged.json

Features:
  - Checks freshness (skip stale files older than TTL)
  - Merges all jobs into single list
  - Dedup by URL exact match, then title+company fuzzy match (>85%)
  - Cross-reference with applied-job-ids.txt
  - Apply search policy filters
  - Track which sources found each job
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from _imports import agent_common, jobs_source_common

# Import from agent_common
AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
load_json = agent_common.load_json
now_cairo = agent_common.now_cairo
WORKSPACE = agent_common.WORKSPACE
DATA_DIR = agent_common.DATA_DIR
JOBS_RAW_DIR = agent_common.JOBS_RAW_DIR

# Import from jobs_source_common
SKIP_WORDS = jobs_source_common.SKIP_WORDS
EXEC_WORDS = jobs_source_common.EXEC_WORDS

# Configuration
AGENT_NAME = "jobs-merge"
OUTPUT_FILE = DATA_DIR / "jobs-merged.json"
APPLIED_IDS_FILE = WORKSPACE / "jobs-bank" / "applied-job-ids.txt"
SEARCH_POLICY_FILE = WORKSPACE / "jobs-bank" / "search-policy.md"
FRESHNESS_HOURS = 25  # Max age for source files (survives 1 failed pipeline run)
FUZZY_MATCH_THRESHOLD = 0.85  # 85% similarity for title+company dedup

# Cairo timezone
CAIRO_TZ = timezone(timedelta(hours=2))


def load_applied_ids() -> set[str]:
    """Load already-applied job IDs from tracking file.
    
    Stores both the raw ID and any numeric suffix extracted from it,
    so matching works regardless of format (plain number or prefixed).
    """
    applied = set()
    try:
        if APPLIED_IDS_FILE.exists():
            with open(APPLIED_IDS_FILE) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("|")
                    if parts:
                        job_id = parts[0].strip()
                        if job_id and len(job_id) >= 6:
                            # Add the raw ID as-is
                            applied.add(job_id)
                            # Also add just the numeric/hex suffix for prefix-agnostic matching
                            suffix = job_id.split("-")[-1]
                            if suffix != job_id and len(suffix) >= 6:
                                applied.add(suffix)
    except Exception as e:
        print(f"  Warning: Could not load applied IDs: {e}")
    return applied


def is_stale(meta: dict, max_hours: int) -> bool:
    """Check if source file is stale based on generated_at timestamp."""
    try:
        generated_at = meta.get("generated_at", "")
        if not generated_at:
            return True
        
        gen_time = datetime.fromisoformat(generated_at)
        age = now_cairo() - gen_time
        age_hours = age.total_seconds() / 3600
        
        return age_hours > max_hours
    except Exception:
        return True


def fuzzy_match(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def normalize_title_company(title: str, company: str) -> str:
    """Create a normalized key for fuzzy matching."""
    title = title.lower().strip()
    company = company.lower().strip()
    
    title = re.sub(r'\s*[\(\-–]\s*(dubai|uae|saudi|riyadh|qatar|doha|bahrain|kuwait|oman|muscat|abu dhabi|jeddah).*$', '', title, flags=re.IGNORECASE)
    company = re.sub(r'\s*(llc|ltd|inc|corp|corporation|limited|fzc|fze|fz|dmcc|difc)\.?$', '', company, flags=re.IGNORECASE).strip()
    
    return f"{title}|||{company}"


def find_fuzzy_duplicate(job: dict, existing_jobs: list[dict], threshold: float = FUZZY_MATCH_THRESHOLD) -> dict | None:
    """Find if a job is a fuzzy duplicate of any existing job."""
    job_key = normalize_title_company(job.get("title", ""), job.get("company", ""))
    
    for existing in existing_jobs:
        existing_key = normalize_title_company(existing.get("title", ""), existing.get("company", ""))
        
        similarity = fuzzy_match(job_key, existing_key)
        if similarity >= threshold:
            return existing
    
    return None


## Aggregator / listing page patterns to filter out
AGGREGATOR_DOMAINS = {
    "glassdoor.com", "trovit.com", "indeed.com", "linkedin.com/jobs/search",
    "bayt.com/en/jobs", "naukri.com/jobs-in", "monster.com", "ziprecruiter.com",
    "simplyhired.com", "careerbuilder.com", "jooble.org", "jobrapido.com"
}

AGGREGATOR_TITLE_PATTERNS = [
    r'^\d+\s+.+jobs?\s+in\s+',          # "47 Head of digital transformation jobs in Dubai"
    r'.+jobs?\s+in\s+.+\s*[-–]\s*\d+',   # "PMO Director Jobs in Riyadh - 124 Vacancies"
    r'.+vacancies?\s+\w+\s+\d{4}',       # "... Vacancies Mar 2026"
    r'.+job offers?\s+in\s+',             # "Pmo director job offers in dubai"
    r'^top\s+\d+\s+',                     # "Top 10 PMO jobs..."
    r'.+jobs?\s+[-–]\s+\d+\s+vacancies', # "... jobs - 551 Vacancies"
]


def is_aggregator_listing(job: dict) -> tuple[bool, str]:
    """Detect aggregator listing pages masquerading as individual jobs."""
    title = job.get("title", "")
    url = job.get("url", "").lower()
    company = job.get("company", "").lower()
    
    # Check URL domain
    for domain in AGGREGATOR_DOMAINS:
        if domain in url and "/jobs/" not in url.split("?")[0].rsplit("/", 1)[-1]:
            # Allow individual job pages (URL ends with job ID), block listing pages
            if re.search(r'/jobs?/\d+', url) or re.search(r'/job/[a-z0-9-]+$', url):
                continue  # This is an individual job page, keep it
            return True, f"aggregator-domain:{domain}"
    
    # Check title patterns
    for pattern in AGGREGATOR_TITLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return True, f"aggregator-title-pattern"
    
    # Check company name is actually a job board
    job_board_names = ["glassdoor", "trovit", "indeed", "bayt", "linkedin", "naukrigulf", "monster"]
    for board in job_board_names:
        if board in company:
            return True, f"aggregator-company:{board}"
    
    return False, "individual-job"


def is_bad_url(url: str) -> tuple[bool, str]:
    """Detect broken/invalid/non-job URLs."""
    if not url:
        return True, "no-url"
    
    url_lower = url.lower().strip()
    
    # URL is just a domain with no path
    from urllib.parse import urlparse
    parsed = urlparse(url_lower)
    path = parsed.path.strip("/")
    if not path:
        return True, "domain-only-url"
    
    # Profile pages (not jobs)
    profile_patterns = [
        "/me/", "/profile/", "/u/", "/user/", "/cv/", "/resume/",
        "wuzzuf.net/me/", "linkedin.com/in/",
    ]
    for p in profile_patterns:
        if p in url_lower:
            return True, f"profile-page:{p}"
    
    return False, ""


def apply_search_policy(job: dict) -> tuple[bool, str]:
    """Apply search policy filters. Returns (keep, reason)."""
    title = job.get("title", "").lower()
    url = job.get("url", "")
    
    # Filter bad URLs (broken links, profile pages)
    is_bad, bad_reason = is_bad_url(url)
    if is_bad:
        return False, bad_reason
    
    # Filter jobs with person names in title (CV pages indexed as jobs)
    import re
    # Pattern: "FirstName LastName — Title" or "FirstName LastName – Title"
    if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+ [–—-] ', job.get("title", "")):
        return False, "person-name-in-title"
    
    # Filter aggregator listings — only for Exa results
    # Jobs from Indeed/LinkedIn/Bayt/Google are already individual listings
    source = job.get("source", "")
    if source == "exa":
        is_agg, agg_reason = is_aggregator_listing(job)
        if is_agg:
            return False, agg_reason
    
    if not any(w in title for w in EXEC_WORDS):
        return False, "no-seniority"
    
    for skip in SKIP_WORDS:
        if skip in title:
            return False, f"skip-word:{skip}"
    
    return True, "pass"


def run_merge(result: AgentResult):
    """Main merge logic."""
    
    applied_ids = load_applied_ids()
    print(f"Loaded {len(applied_ids)} applied job IDs")
    
    if is_dry_run():
        print("\n=== DRY RUN: Merge Preview ===")
        
        source_files = list(JOBS_RAW_DIR.glob("*.json"))
        print(f"\nSource files in {JOBS_RAW_DIR}:")

        total_jobs = 0
        for f in source_files:
            data = load_json(f, {})
            if isinstance(data, list):
                jobs = data
                meta = {}
            else:
                meta = data.get("meta", {})
                jobs = data.get("jobs", data.get("data", []))
            if isinstance(jobs, list):
                count = len(jobs)
            else:
                count = 0

            status = "✅" if not is_stale(meta, FRESHNESS_HOURS) else "⚠️ STALE"
            print(f"  {status} {f.name}: {count} jobs | {meta.get('source', '?')} | {meta.get('generated_at', '?')}")
            total_jobs += count
        
        print(f"\nTotal jobs across sources: {total_jobs}")
        print(f"Applied IDs to filter: {len(applied_ids)}")
        print(f"Fuzzy match threshold: {FUZZY_MATCH_THRESHOLD * 100}%")
        
        result.set_data([])
        result.set_kpi({
            "source_files": len(source_files),
            "total_raw": total_jobs,
            "applied_ids_loaded": len(applied_ids),
        })
        return
    
    source_files = list(JOBS_RAW_DIR.glob("*.json"))
    print(f"Found {len(source_files)} source files")
    
    all_jobs_raw = []
    sources_loaded = {}
    stale_sources = []
    
    for f in source_files:
        data = load_json(f, {})
        # Handle raw list format (some sources output list directly)
        if isinstance(data, list):
            jobs = data
            source = f.stem
            # Use file mtime as proxy for freshness
            from datetime import datetime
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
            meta = {"generated_at": mtime.isoformat()} if age_hours < 24 else {}
        else:
            meta = data.get("meta", {})
            source = meta.get("source", f.stem)
            jobs = data.get("jobs", data.get("data", []))
        
        if is_stale(meta, FRESHNESS_HOURS):
            print(f"  ⚠️ Skipping stale: {f.name}")
            stale_sources.append(source)
            continue
        
        if not isinstance(jobs, list):
            print(f"  ⚠️ Invalid format: {f.name}")
            continue
        
        for job in jobs:
            job["_source_file"] = source
        
        all_jobs_raw.extend(jobs)
        sources_loaded[source] = len(jobs)
        print(f"  ✅ {f.name}: {len(jobs)} jobs")
    
    print(f"\nTotal raw jobs: {len(all_jobs_raw)}")
    
    # Stage 1: URL exact dedup
    seen_urls = {}
    url_deduped = []
    
    for job in all_jobs_raw:
        url = job.get("url", "")
        if not url:
            continue
        
        if url in seen_urls:
            existing = seen_urls[url]
            existing_sources = existing.get("_sources", [existing.get("_source_file", "")])
            if job.get("_source_file") not in existing_sources:
                existing_sources.append(job.get("_source_file", ""))
            
            # Prefer the record with more data (snippet + keyword_score)
            existing_richness = len(existing.get("raw_snippet", "") or "") + (existing.get("keyword_score") or 0)
            job_richness = len(job.get("raw_snippet", "") or "") + (job.get("keyword_score") or 0)
            if job_richness > existing_richness:
                # Replace with richer record, preserve merged sources
                job["_sources"] = existing_sources
                job["source_count"] = len(existing_sources)
                seen_urls[url] = job
                # Replace in url_deduped list
                for idx, j in enumerate(url_deduped):
                    if j.get("url") == url:
                        url_deduped[idx] = job
                        break
            else:
                existing["_sources"] = existing_sources
                existing["source_count"] = len(existing_sources)
        else:
            job["_sources"] = [job.get("_source_file", "")]
            job["source_count"] = 1
            seen_urls[url] = job
            url_deduped.append(job)
    
    print(f"After URL dedup: {len(url_deduped)} jobs")
    
    # Stage 2: Fuzzy title+company dedup
    fuzzy_deduped = []
    
    for job in url_deduped:
        existing = find_fuzzy_duplicate(job, fuzzy_deduped)
        if existing:
            existing_sources = existing.get("_sources", [])
            job_source = job.get("_source_file", "")
            if job_source and job_source not in existing_sources:
                existing_sources.append(job_source)
                existing["_sources"] = existing_sources
                existing["source_count"] = len(existing_sources)
        else:
            fuzzy_deduped.append(job)
    
    print(f"After fuzzy dedup: {len(fuzzy_deduped)} jobs")
    
    # Stage 3: Filter already-applied jobs
    not_applied = []
    applied_filtered = 0
    
    for job in fuzzy_deduped:
        job_id = job.get("id", "").split("-")[-1]
        url = job.get("url", "")
        
        # Check job ID directly
        if job_id in applied_ids:
            applied_filtered += 1
            continue
        
        # Also extract any numeric ID from URL (LinkedIn URLs contain job IDs)
        import re
        url_ids = re.findall(r'(\d{8,})', url)
        if any(uid in applied_ids for uid in url_ids):
            applied_filtered += 1
            continue
        
        not_applied.append(job)
    
    print(f"After applied filter: {len(not_applied)} jobs (removed {applied_filtered})")
    
    # Stage 4: Apply search policy
    policy_passed = []
    policy_filtered = 0
    
    for job in not_applied:
        keep, reason = apply_search_policy(job)
        if keep:
            job["policy_status"] = "pass"
            policy_passed.append(job)
        else:
            job["policy_status"] = reason
            policy_filtered += 1
    
    print(f"After policy filter: {len(policy_passed)} jobs (removed {policy_filtered})")
    
    # Sort by keyword score (descending)
    policy_passed.sort(key=lambda x: x.get("keyword_score", 0), reverse=True)
    
    multi_source = sum(1 for j in policy_passed if j.get("source_count", 1) > 1)
    
    # Clean up internal fields for output
    final_jobs = []
    for job in policy_passed:
        clean_job = {k: v for k, v in job.items() if not k.startswith("_")}
        clean_job["sources"] = job.get("_sources", [job.get("source", "")])
        final_jobs.append(clean_job)
    
    print(f"\nFinal candidates: {len(final_jobs)}")
    print(f"Multi-source jobs: {multi_source}")
    
    result.set_data(final_jobs)
    result.set_kpi({
        "total_raw": len(all_jobs_raw),
        "sources_loaded": len(sources_loaded),
        "stale_sources": len(stale_sources),
        "unique_after_dedup": len(fuzzy_deduped),
        "applied_filtered": applied_filtered,
        "policy_filtered": policy_filtered,
        "final_candidates": len(final_jobs),
        "multi_source_jobs": multi_source,
        "new_today": len(final_jobs),
    })


def main():
    """Entry point."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(
        agent_name=AGENT_NAME,
        run_func=run_merge,
        output_path=OUTPUT_FILE,
        ttl_hours=6,
        version="1.0.0"
    )


if __name__ == "__main__":
    main()
