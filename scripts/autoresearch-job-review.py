#!/usr/bin/env python3
"""
autoresearch-job-review.py — Karpathy-style autoresearch loop for job review prompt optimization.

Analyzes job review outcomes (applied vs skipped) to identify miss patterns,
then generates improved prompt candidates to reduce the miss rate.

Run: python3 scripts/autoresearch-job-review.py
Runs weekly via cron (Sundays 2 AM Cairo).

Loss function: miss_rate = skipped_submit_jobs / total_submit_jobs
Target: <10% miss rate (currently 37.5%)
"""

import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# ── Paths ─────────────────────────────────────────────────────────────────────
WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPTS_DIR = WORKSPACE / "scripts"
DATA_DIR = WORKSPACE / "data"
JOBS_BANK_DIR = WORKSPACE / "jobs-bank"

JOBS_SUMMARY_FILE = DATA_DIR / "jobs-summary.json"
APPLIED_IDS_FILE = JOBS_BANK_DIR / "applied-job-ids.txt"
JOBS_REVIEW_SCRIPT = SCRIPTS_DIR / "jobs-review.py"
NOTION_CONFIG_FILE = WORKSPACE / "config" / "notion.json"

AUTORESEARCH_DIR = DATA_DIR / "autoresearch"
LOG_FILE = AUTORESEARCH_DIR / "job-review-log.json"
PROMPT_CANDIDATES_DIR = AUTORESEARCH_DIR / "prompt-candidates"
OUTCOMES_DIR = AUTORESEARCH_DIR / "outcomes"

# ── Notion ────────────────────────────────────────────────────────────────────
NOTION_PIPELINE_DB = "3268d599-a162-81b4-b768-f162adfa4971"

# ── Skip pattern keywords ──────────────────────────────────────────────────────
NATIONALS_ONLY_PATTERNS = [
    "nationals only", "emirati only", "saudi only", "uae national",
    "kuwaiti national", "bahraini national", "qatari national",
    "omani national", "citizen only", "gcc national", "national only",
    "(uae national)", "(uae nationals only)", "– abu dhabi (uae national)",
    "nationals preferred",
]

DEEP_TECHNICAL_PATTERNS = [
    "ai/ml", "gpu cluster", "gpu infrastructure", "robotics",
    "computer vision phd", "machine learning engineer", "deep learning",
    "neural network architect", "llm training", "model training",
    "head of ai engineering", "head of ml", "vp of ai",
    "ai engineering", "ml engineering", "12+ years ai",
    "hands-on ml", "hands-on ai", "coding ai", "python developer",
]

WRONG_FUNCTION_PATTERNS = [
    "sales director", "bd lead", "business development lead",
    "marketing head", "head of sales", "vp sales",
    "chief sales", "chief marketing", "cmo", "cso",
    "head of marketing", "director of sales",
    "commercial director", "revenue director",
]

TOO_JUNIOR_PATTERNS = [
    r"\bmanager\b(?!.*(senior|head|general|program|project|delivery|account|country|area|regional|vp|director|chief|c-))",
    r"\bsenior manager\b",
    r"\bteam lead\b",
    r"\bengineering manager\b",
]


def load_notion_token() -> str:
    """Load Notion API token from config."""
    try:
        with open(NOTION_CONFIG_FILE) as f:
            cfg = json.load(f)
        return cfg.get("token", "")
    except Exception:
        return ""


def load_applied_ids() -> set[str]:
    """Load all applied job IDs from applied-job-ids.txt."""
    applied = set()
    if not APPLIED_IDS_FILE.exists():
        return applied

    with open(APPLIED_IDS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Format: "4366706927 | company | role | date" or bare ID
            parts = line.split("|")
            job_id = parts[0].strip()
            if job_id:
                applied.add(job_id)

    return applied


def load_jobs_summary() -> dict:
    """Load jobs-summary.json."""
    if not JOBS_SUMMARY_FILE.exists():
        return {}
    with open(JOBS_SUMMARY_FILE) as f:
        return json.load(f)


def get_notion_skipped_jobs(notion_token: str) -> list[dict]:
    """Fetch skipped jobs from Notion Pipeline DB."""
    if not notion_token:
        print("  No Notion token — skipping Notion fetch")
        return []

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    # Query for skipped/rejected stage entries
    skip_stages = ["⛔ Skipped", "❌ Rejected", "Skipped", "Rejected", "Not Suitable"]
    filter_conditions = [
        {"property": "Stage", "status": {"equals": stage}}
        for stage in skip_stages
    ] + [
        {"property": "Status", "select": {"equals": stage}}
        for stage in skip_stages
    ]

    payload = {
        "filter": {
            "or": filter_conditions
        },
        "page_size": 100,
    }

    try:
        resp = requests.post(
            f"https://api.notion.com/v1/databases/{NOTION_PIPELINE_DB}/query",
            headers=headers,
            json=payload,
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"  Notion query failed: HTTP {resp.status_code}")
            return []

        results = resp.json().get("results", [])
        skipped = []
        for page in results:
            props = page.get("properties", {})
            title_prop = props.get("Name") or props.get("Title") or props.get("Job Title") or {}
            title_items = title_prop.get("title", [])
            title = "".join(t.get("plain_text", "") for t in title_items)

            skipped.append({
                "id": page["id"],
                "title": title,
                "source": "notion",
            })

        print(f"  Notion: found {len(skipped)} skipped jobs")
        return skipped

    except Exception as e:
        print(f"  Notion error: {e}")
        return []


def extract_job_id_from_job(job: dict) -> str:
    """Extract a normalised ID from a job dict for matching against applied-ids."""
    job_id = job.get("id", "")

    # linkedin-li-4366706927 -> 4366706927
    if job_id.startswith("linkedin-li-"):
        return job_id.replace("linkedin-li-", "")

    # google-in-025f90f1df941203 -> 025f90f1df941203
    if job_id.startswith("google-in-"):
        return job_id.replace("google-in-", "")

    return job_id


def classify_skip_pattern(job: dict) -> list[str]:
    """Detect which skip patterns a job matches."""
    patterns_found = []
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    snippet = (job.get("raw_snippet") or "").lower()
    url = (job.get("url") or "").lower()
    reason = (job.get("verdict_reason") or "").lower()
    full_text = f"{title} {snippet} {url} {reason}"

    # Check nationality-only patterns
    for pat in NATIONALS_ONLY_PATTERNS:
        if pat.lower() in full_text:
            patterns_found.append("nationals_only")
            break

    # Check deep technical patterns
    for pat in DEEP_TECHNICAL_PATTERNS:
        if pat.lower() in full_text:
            patterns_found.append("deep_technical_ai")
            break

    # Check wrong function patterns
    for pat in WRONG_FUNCTION_PATTERNS:
        if pat.lower() in full_text:
            patterns_found.append("wrong_function")
            break

    # Check too junior (regex)
    for pat in TOO_JUNIOR_PATTERNS:
        if re.search(pat, full_text, re.IGNORECASE):
            patterns_found.append("too_junior")
            break

    return patterns_found if patterns_found else ["unknown"]


def load_current_prompt() -> str:
    """Extract the LLM scoring prompt from jobs-review.py."""
    if not JOBS_REVIEW_SCRIPT.exists():
        return ""

    with open(JOBS_REVIEW_SCRIPT) as f:
        content = f.read()

    # Extract the build_review_prompt function content
    match = re.search(
        r'def build_review_prompt\(.*?\).*?"""(.*?)"""',
        content,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    # Fallback: extract SCORING GUIDELINES section
    match = re.search(
        r'(SCORING GUIDELINES:.*?)(?:Return ONLY|$)',
        content,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    return ""


def extract_prompt_block(script_content: str) -> str:
    """Extract the full prompt string from jobs-review.py's build_review_prompt."""
    # Grab everything inside build_review_prompt between the triple-quoted prompt = f"""..."""
    match = re.search(
        r'(prompt\s*=\s*f""")(.*?)(""")',
        script_content,
        re.DOTALL,
    )
    if match:
        return match.group(2)
    return ""


def load_autoresearch_log() -> dict:
    """Load the autoresearch iteration log."""
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"iterations": []}


def save_autoresearch_log(log: dict):
    """Save the autoresearch log."""
    AUTORESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def get_next_version(log: dict) -> int:
    """Get the next version number."""
    if not log["iterations"]:
        return 1
    return max(it["version"] for it in log["iterations"]) + 1


def save_baseline_prompt(current_prompt_block: str):
    """Save the current prompt as v0 baseline if not already saved."""
    baseline = PROMPT_CANDIDATES_DIR / "prompt-v0-baseline.md"
    if not baseline.exists():
        PROMPT_CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
        with open(baseline, "w") as f:
            f.write(f"# Prompt v0 — Baseline (auto-captured {datetime.now().strftime('%Y-%m-%d')})\n\n")
            f.write("## Source\n")
            f.write("Extracted from `scripts/jobs-review.py` `build_review_prompt()` function.\n\n")
            f.write("## Prompt Block\n\n")
            f.write("```\n")
            f.write(current_prompt_block)
            f.write("\n```\n")
        print(f"  Saved baseline prompt to {baseline}")


def generate_improved_prompt(
    current_prompt_block: str,
    skip_patterns: dict,
    metrics: dict,
    version: int,
) -> tuple[str, list[str]]:
    """Generate an improved prompt candidate based on skip patterns.
    
    Guard rails (Karpathy):
    - Max 3 new rules per iteration
    - Never remove existing good rules
    - Keep GOLDEN RULES section untouched
    - Add rules only for confirmed skip patterns
    """
    new_rules = []
    changes_made = []

    # Rule 1: Nationals-only filter
    if skip_patterns.get("nationals_only", 0) > 0:
        nationals_rule = """
DEALBREAKER — NATIONALS ONLY (AUTOMATIC SKIP):
- If title or description contains ANY of the following, score 1 and SKIP immediately:
  "nationals only", "UAE national", "Emirati only", "Saudi only", "Kuwaiti national",
  "Bahraini national", "Qatari national", "Omani national", "citizen only", "GCC national"
- These roles are legally restricted and cannot be applied for. Do NOT score them 7+.
- Pattern to detect: parenthetical like "(UAE Nationals Only)" or dash like "– UAE National"
"""
        new_rules.append(nationals_rule)
        changes_made.append(
            f"Added DEALBREAKER nationals-only filter (caught {skip_patterns['nationals_only']} false positives)"
        )

    # Rule 2: Deep technical AI/ML filter
    if skip_patterns.get("deep_technical_ai", 0) > 0:
        technical_rule = """
DEEP TECHNICAL AI/ML ROLES (SKIP):
- Roles requiring hands-on AI/ML engineering are NOT suitable for this candidate:
  "Head of AI Engineering", "Head of ML", "VP of AI Engineering", "AI/ML Engineer",
  "Machine Learning Engineer", "Deep Learning Researcher", "LLM Training", "GPU Clusters"
- Exception: "AI Strategy", "Head of AI Products", "Chief AI Officer", "Director of AI Transformation"
  are STRATEGIC roles → score normally
- Key distinction: building/training AI models = SKIP. Deploying/governing AI strategy = SUBMIT
"""
        new_rules.append(technical_rule)
        changes_made.append(
            f"Added deep technical AI/ML exclusion (caught {skip_patterns['deep_technical_ai']} false positives)"
        )

    # Rule 3: Wrong function filter (only add if 2+ instances)
    if skip_patterns.get("wrong_function", 0) >= 2:
        function_rule = """
WRONG FUNCTION ROLES (SKIP):
- Sales, Business Development, and Marketing leadership roles are not Ahmed's profile:
  "Head of Sales", "Sales Director", "BD Lead", "VP Sales", "Chief Revenue Officer",
  "Head of Marketing", "CMO", "Commercial Director"
- Exception: if the role explicitly combines with Technology/Digital ("Director Sales Technology Platform")
"""
        new_rules.append(function_rule)
        changes_made.append(
            f"Added wrong-function filter (caught {skip_patterns['wrong_function']} false positives)"
        )

    # Cap at 3 new rules per iteration
    new_rules = new_rules[:3]
    changes_made = changes_made[:3]

    if not new_rules:
        return "", []

    # Build the improved prompt by injecting new rules before SCORING GUIDELINES
    golden_rules_section = """
═══════════════════════════════════════════════════════════
GOLDEN RULES (DO NOT MODIFY — permanent constraints):
- Always score based on TITLE + COMPANY + LOCATION even when no description is available
- Never penalize a job for missing description — title is the primary signal
- A job titled "Director Digital Transformation" at a GCC company is MINIMUM a 7
- Never score a role 7+ if it contradicts the dealbreakers below
═══════════════════════════════════════════════════════════
"""

    new_rules_block = "\n".join(new_rules)

    # Inject after CANDIDATE PROFILE but before SCORING GUIDELINES
    if "SCORING GUIDELINES:" in current_prompt_block:
        improved = current_prompt_block.replace(
            "SCORING GUIDELINES:",
            f"{golden_rules_section}\n\nAUTO-LEARNED EXCLUSION RULES (v{version}):\n{new_rules_block}\n\nSCORING GUIDELINES:",
        )
    else:
        improved = (
            current_prompt_block
            + f"\n\n{golden_rules_section}\n\nAUTO-LEARNED EXCLUSION RULES (v{version}):\n{new_rules_block}"
        )

    return improved, changes_made


def save_prompt_candidate(improved_prompt: str, version: int) -> Path:
    """Save the improved prompt to a versioned file."""
    PROMPT_CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PROMPT_CANDIDATES_DIR / f"prompt-v{version}.md"

    with open(output_file, "w") as f:
        f.write(f"# Prompt v{version} — Auto-generated {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write("## How to apply\n")
        f.write(f"Run: `python3 scripts/apply-autoresearch-prompt.py` to review and apply.\n\n")
        f.write("## Changes from previous version\n")
        f.write("(See job-review-log.json for change details)\n\n")
        f.write("## Improved Prompt Block\n\n")
        f.write("```\n")
        f.write(improved_prompt)
        f.write("\n```\n")

    return output_file


def save_outcomes_snapshot(
    today_submit_jobs: list,
    skipped_jobs: list,
    applied_ids: set,
    date_str: str,
):
    """Save today's outcome data snapshot."""
    OUTCOMES_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_file = OUTCOMES_DIR / f"{date_str}.json"

    snapshot = {
        "date": date_str,
        "total_submit": len(today_submit_jobs),
        "applied": [j for j in today_submit_jobs if any(
            extract_job_id_from_job(j) in applied_ids or j.get("id", "") in applied_ids
            for _ in [None]
        )],
        "skipped": skipped_jobs,
        "applied_ids_count": len(applied_ids),
    }

    with open(snapshot_file, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"  Saved outcomes snapshot to {snapshot_file}")


def git_commit(files: list[Path], message: str):
    """Git commit autoresearch outputs."""
    try:
        str_files = [str(f) for f in files]
        subprocess.run(
            ["git", "-C", str(WORKSPACE), "add"] + str_files,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(WORKSPACE), "commit", "-m", message],
            check=True,
            capture_output=True,
        )
        print(f"  Git committed: {message}")
    except subprocess.CalledProcessError as e:
        print(f"  Git commit failed (non-fatal): {e.stderr.decode()[:200]}")


def main():
    """Main autoresearch loop."""
    print("=" * 60)
    print("AUTORESEARCH: Job Review Prompt Optimizer")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── Step 1: Load input data ───────────────────────────────────────────────
    print("\n[1/6] Loading data sources...")

    applied_ids = load_applied_ids()
    print(f"  Applied IDs: {len(applied_ids)}")

    summary = load_jobs_summary()
    summary_data = summary.get("data", {})
    submit_jobs = summary_data.get("submit", [])
    print(f"  Jobs summary: {len(submit_jobs)} SUBMIT jobs")

    notion_token = load_notion_token()
    notion_skipped = get_notion_skipped_jobs(notion_token)

    # ── Step 2: Calculate metrics ─────────────────────────────────────────────
    print("\n[2/6] Calculating accuracy metrics...")

    # Determine which SUBMIT jobs were actually applied vs skipped
    # A SUBMIT job is "applied" if its ID appears in applied-job-ids.txt
    # A SUBMIT job is "skipped" if:
    #   a) It's in Notion as skipped, OR
    #   b) Its ID is NOT in applied-ids and it was discovered >2 days ago

    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=2)

    applied_in_submit = []
    skipped_in_submit = []
    pending_submit = []  # too recent to know yet

    for job in submit_jobs:
        job_id = extract_job_id_from_job(job)
        raw_id = job.get("id", "")

        is_applied = job_id in applied_ids or raw_id in applied_ids

        # Check if in Notion skipped list (by rough title match)
        job_title_lower = (job.get("title") or "").lower()
        job_company_lower = (job.get("company") or "").lower()
        is_notion_skipped = any(
            job_title_lower in (ns.get("title") or "").lower() or
            job_company_lower in (ns.get("title") or "").lower()
            for ns in notion_skipped
        )

        # Parse posted date
        posted_str = job.get("posted", "")
        try:
            posted_dt = datetime.fromisoformat(posted_str).replace(tzinfo=timezone.utc)
            is_stale = posted_dt < two_days_ago
        except Exception:
            is_stale = False  # treat unknown dates as fresh

        if is_applied:
            applied_in_submit.append(job)
        elif is_notion_skipped:
            skipped_in_submit.append(job)
        elif is_stale:
            # Stale + not applied = inferred skip
            skipped_in_submit.append(job)
        else:
            pending_submit.append(job)

    total_submit = len(submit_jobs)
    total_applied = len(applied_in_submit)
    total_skipped = len(skipped_in_submit)
    total_pending = len(pending_submit)

    accuracy_rate = total_applied / max(1, total_applied + total_skipped)
    miss_rate = total_skipped / max(1, total_applied + total_skipped)

    print(f"  Total SUBMIT: {total_submit}")
    print(f"  Applied: {total_applied}")
    print(f"  Skipped: {total_skipped}")
    print(f"  Pending (recent): {total_pending}")
    print(f"  Accuracy rate: {accuracy_rate:.1%}")
    print(f"  Miss rate: {miss_rate:.1%} (target: <10%)")

    # ── Step 3: Extract skip patterns ─────────────────────────────────────────
    print("\n[3/6] Extracting skip patterns...")

    pattern_counts: dict[str, int] = {}
    skipped_with_patterns = []

    for job in skipped_in_submit:
        patterns = classify_skip_pattern(job)
        skipped_with_patterns.append({"job": job, "patterns": patterns})
        for p in patterns:
            pattern_counts[p] = pattern_counts.get(p, 0) + 1

    print("  Skip pattern breakdown:")
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"    {pattern}: {count} jobs")

    # ── Step 4: Load current prompt ───────────────────────────────────────────
    print("\n[4/6] Reading current prompt from jobs-review.py...")

    with open(JOBS_REVIEW_SCRIPT) as f:
        script_content = f.read()

    current_prompt_block = extract_prompt_block(script_content)
    if not current_prompt_block:
        # Fallback: just capture the build_review_prompt function
        current_prompt_block = load_current_prompt()

    if current_prompt_block:
        print(f"  Extracted prompt block ({len(current_prompt_block)} chars)")
        save_baseline_prompt(current_prompt_block)
    else:
        print("  Warning: Could not extract prompt block")
        current_prompt_block = "# Prompt block not extracted — check jobs-review.py manually"

    # ── Step 5: Generate improved prompt ──────────────────────────────────────
    print("\n[5/6] Generating improved prompt candidate...")

    log = load_autoresearch_log()
    version = get_next_version(log)

    metrics = {
        "total_submit": total_submit,
        "applied": total_applied,
        "skipped": total_skipped,
        "pending": total_pending,
        "accuracy": round(accuracy_rate, 4),
        "miss_rate": round(miss_rate, 4),
    }

    # Check if miss rate is already good
    if miss_rate < 0.10 and total_skipped > 0:
        print(f"  Miss rate {miss_rate:.1%} already below 10% target. Logging but skipping prompt update.")
        improved_prompt = ""
        changes_made = ["No changes needed — miss rate below target"]
    elif total_skipped == 0:
        print("  No skipped jobs found. Nothing to optimize yet.")
        improved_prompt = ""
        changes_made = ["No skipped jobs to analyze"]
    else:
        improved_prompt, changes_made = generate_improved_prompt(
            current_prompt_block, pattern_counts, metrics, version
        )

    prompt_file = f"prompt-v{version}.md"

    if improved_prompt:
        output_path = save_prompt_candidate(improved_prompt, version)
        print(f"  Saved: {output_path}")
        print(f"  Changes:")
        for change in changes_made:
            print(f"    - {change}")
    else:
        prompt_file = "none"
        print("  No prompt candidate generated.")

    # ── Step 6: Log iteration and save outcomes ───────────────────────────────
    print("\n[6/6] Logging iteration and committing...")

    date_str = datetime.now().strftime("%Y-%m-%d")
    save_outcomes_snapshot(submit_jobs, skipped_in_submit, applied_ids, date_str)

    # Update log
    iteration = {
        "version": version,
        "date": date_str,
        "prompt_file": prompt_file,
        "metrics": metrics,
        "skip_patterns_found": list(pattern_counts.keys()),
        "skip_pattern_counts": pattern_counts,
        "changes_made": changes_made,
        "skipped_jobs_analyzed": [
            {
                "title": item["job"].get("title"),
                "company": item["job"].get("company"),
                "patterns": item["patterns"],
            }
            for item in skipped_with_patterns
        ],
    }
    log["iterations"].append(iteration)
    save_autoresearch_log(log)

    # Git commit
    files_to_commit = [LOG_FILE, OUTCOMES_DIR / f"{date_str}.json"]
    if improved_prompt:
        files_to_commit.append(PROMPT_CANDIDATES_DIR / prompt_file)
        if (PROMPT_CANDIDATES_DIR / "prompt-v0-baseline.md").exists():
            files_to_commit.append(PROMPT_CANDIDATES_DIR / "prompt-v0-baseline.md")

    prev_accuracy = None
    if len(log["iterations"]) > 1:
        prev_iter = log["iterations"][-2]
        prev_accuracy = prev_iter.get("metrics", {}).get("accuracy")

    delta_str = ""
    if prev_accuracy is not None:
        delta = accuracy_rate - prev_accuracy
        delta_str = f" (Δ{delta:+.1%})"

    commit_msg = (
        f"autoresearch: prompt v{version} | accuracy {accuracy_rate:.1%}{delta_str} | "
        f"miss rate {miss_rate:.1%} | patterns: {', '.join(pattern_counts.keys()) or 'none'}"
    )
    git_commit(files_to_commit, commit_msg)

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("AUTORESEARCH COMPLETE")
    print("=" * 60)
    print(f"  Version:      v{version}")
    print(f"  Accuracy:     {accuracy_rate:.1%} (target: >90%)")
    print(f"  Miss rate:    {miss_rate:.1%} (target: <10%)")
    print(f"  Skip patterns: {', '.join(pattern_counts.keys()) or 'none'}")
    if improved_prompt:
        print(f"  Prompt candidate: data/autoresearch/prompt-candidates/prompt-v{version}.md")
        print()
        print("  Next step: Review and apply with:")
        print("    python3 scripts/apply-autoresearch-prompt.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
