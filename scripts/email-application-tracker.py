#!/usr/bin/env python3
"""
email-application-tracker.py - Gmail Smart Router for job application tracking.

Scans Gmail via Himalaya for recruitment-related emails, matches them to
tracked job applications, and classifies application stage.

Output: coordination/email-tracking.json
"""

import time
import sys
import os
import json
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from difflib import SequenceMatcher

os.environ["PYTHONUNBUFFERED"] = "1"
sys.path.insert(0, str(Path(__file__).parent))

from _imports import agent_common

AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
now_iso = agent_common.now_iso

AGENT_NAME = "email-application-tracker"
WORKSPACE = Path("/root/.openclaw/workspace")
OUTPUT_FILE = WORKSPACE / "coordination" / "email-tracking.json"
PIPELINE_FILE = WORKSPACE / "coordination" / "pipeline.json"
JOBS_MERGED = WORKSPACE / "data" / "jobs-merged.json"

# Himalaya config
HIMALAYA_ACCOUNT = "ahmed"
HIMALAYA_CMD = "himalaya"

# Search window
SEARCH_DAYS = 14
MAX_EMAILS_TO_SCAN = 100

# ===================== STAGE CLASSIFICATION =====================

STAGE_PATTERNS = {
    "rejection": {
        "keywords": [
            "unfortunately", "not moving forward", "other candidates",
            "not selected", "regret to inform", "will not be proceeding",
            "decided not to", "not successful", "gone with another",
            "position has been filled", "not a match", "unable to offer",
            "wish you all the best", "decided to move forward with",
            "after careful consideration", "competitive pool",
            "not be progressing", "won't be moving", "decline",
        ],
        "weight": 1.0,
    },
    "interview_invite": {
        "keywords": [
            "interview", "schedule a call", "availability",
            "meet with", "next steps", "would like to discuss",
            "phone screen", "video call", "zoom link", "teams meeting",
            "calendly", "book a time", "panel interview",
            "technical interview", "behavioral interview",
            "hiring manager", "would love to connect",
            "shortlisted", "progressing your application",
        ],
        "weight": 1.2,  # Slightly higher weight - more actionable
    },
    "recruiter_screen": {
        "keywords": [
            "initial call", "introductory call", "quick chat",
            "learn more about your background", "discuss the role",
            "recruiter call", "screening call", "brief conversation",
            "15 minute", "20 minute", "30 minute",
        ],
        "weight": 1.1,
    },
    "assessment": {
        "keywords": [
            "assessment", "test", "exercise", "case study",
            "coding challenge", "take-home", "presentation",
            "assignment", "complete the following", "aptitude",
            "psychometric", "technical test",
        ],
        "weight": 1.0,
    },
    "offer": {
        "keywords": [
            "offer letter", "congratulations", "pleased to offer",
            "extend an offer", "compensation package", "start date",
            "terms of employment", "welcome aboard",
        ],
        "weight": 1.5,  # Highest weight - most important
    },
    "generic_response": {
        "keywords": [
            "thank you for applying", "received your application",
            "application received", "we will review", "under review",
            "review your profile", "acknowledgement", "confirmation",
        ],
        "weight": 0.5,  # Lower weight - less actionable
    },
}

# Sender patterns that indicate recruitment emails
RECRUITER_SENDER_PATTERNS = [
    r"recruit", r"talent", r"hiring", r"career", r"hr@",
    r"people@", r"jobs@", r"noreply.*career", r"apply",
    r"greenhouse", r"lever", r"workday", r"smartrecruiters",
    r"icims", r"taleo", r"bamboohr", r"ashby", r"breezy",
    r"indeed", r"linkedin", r"bayt", r"naukrigulf",
]


# ===================== HIMALAYA INTERFACE =====================

def run_himalaya(args, timeout=30):
    """Run a himalaya CLI command and return output."""
    # himalaya uses default account, no --account flag needed
    cmd = [HIMALAYA_CMD] + args
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, timeout=timeout
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"  [tracker] himalaya timeout: {' '.join(cmd[:6])}")
        return None
    except FileNotFoundError:
        print("[tracker] ERROR: himalaya not found in PATH")
        return None


def list_recent_emails(days=SEARCH_DAYS, max_count=MAX_EMAILS_TO_SCAN):
    """List recent emails from INBOX using JSON output."""
    output = run_himalaya([
        "envelope", "list", "--folder", "INBOX", "--page-size", str(max_count),
        "-o", "json"
    ], timeout=45)

    if not output:
        return []

    try:
        envelopes = json.loads(output.strip())
    except json.JSONDecodeError:
        print(f"  [tracker] Failed to parse himalaya JSON output: {clean_output[:200]}")
        return []

    emails = []
    for env in envelopes:
        from_info = env.get("from", {})
        sender_name = from_info.get("name", "") or ""
        sender_addr = from_info.get("addr", "") or ""
        sender_str = f"{sender_name} <{sender_addr}>" if sender_name else sender_addr

        emails.append({
            "id": str(env.get("id", "")),
            "flags": " ".join(env.get("flags", [])),
            "from": sender_str,
            "from_addr": sender_addr,
            "subject": env.get("subject", ""),
            "date": env.get("date", ""),
        })

    return emails[:max_count]


def read_email_body(email_id):
    """Read full email body."""
    output = run_himalaya(["message", "read", str(email_id), "--folder", "INBOX"], timeout=15)
    return output or ""


def is_recruitment_email(email_info):
    """Quick filter: is this likely a recruitment-related email?"""
    sender = email_info.get("from", "").lower()
    subject = email_info.get("subject", "").lower()

    # Check sender patterns
    for pattern in RECRUITER_SENDER_PATTERNS:
        if re.search(pattern, sender):
            return True

    # Check subject keywords
    recruitment_subjects = [
        "application", "interview", "position", "role",
        "opportunity", "candidate", "job", "hiring",
        "thank you for your interest", "your application",
        "next steps", "unfortunately",
    ]
    for kw in recruitment_subjects:
        if kw in subject:
            return True

    return False


# ===================== JOB MATCHING =====================

def load_active_applications():
    """Load active job applications from pipeline.json and jobs-merged.json."""
    applications = []

    # Try pipeline.json first (primary source)
    if PIPELINE_FILE.exists():
        try:
            with open(PIPELINE_FILE) as f:
                pipeline = json.load(f)

            # pipeline.json uses: applications.active[], applications.rejected[]
            apps_section = pipeline.get("applications", {})
            if isinstance(apps_section, dict):
                # Structured format: {active: [...], rejected: [...], offers: [...]}
                for category in ("active", "in_progress", "interview"):
                    if category in apps_section and isinstance(apps_section[category], list):
                        for job in apps_section[category]:
                            if isinstance(job, dict):
                                applications.append({
                                    "id": job.get("id", ""),
                                    "title": job.get("title", job.get("role", "")),
                                    "company": job.get("company", job.get("employer", "")),
                                    "url": job.get("url", job.get("link", "")),
                                    "applied_date": job.get("date_applied", job.get("applied_date", job.get("date", ""))),
                                    "status": job.get("status", "applied"),
                                })
            elif isinstance(apps_section, list):
                # Flat list format
                for job in apps_section:
                    if isinstance(job, dict):
                        status = job.get("status", "").lower()
                        if status in ("applied", "interview", "in_progress", "submitted"):
                            applications.append({
                                "id": job.get("id", ""),
                                "title": job.get("title", job.get("role", "")),
                                "company": job.get("company", job.get("employer", "")),
                                "url": job.get("url", job.get("link", "")),
                                "applied_date": job.get("applied_date", job.get("date", "")),
                                "status": status,
                            })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [tracker] Error loading pipeline.json: {e}")

    # Also try jobs-merged.json for broader coverage
    if JOBS_MERGED.exists():
        try:
            with open(JOBS_MERGED) as f:
                merged = json.load(f)
            existing_ids = {a["id"] for a in applications}
            for job in merged.get("jobs", []):
                if job.get("id") in existing_ids:
                    continue
                status = job.get("status", "").lower()
                if status in ("applied", "submitted"):
                    applications.append({
                        "id": job.get("id", ""),
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "url": job.get("url", ""),
                        "applied_date": job.get("applied_date", ""),
                        "status": status,
                    })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [tracker] Error loading jobs-merged.json: {e}")

    return applications


def fuzzy_match_company(email_text, company_name):
    """Fuzzy match company name in email text. Returns similarity 0-1."""
    if not company_name or company_name.lower() in ("confidential", "unknown", ""):
        return 0.0

    email_lower = email_text.lower()
    company_lower = company_name.lower()

    # Exact match
    if company_lower in email_lower:
        return 1.0

    # Try common variations
    # Remove common suffixes
    clean_company = re.sub(
        r'\b(inc|ltd|llc|corp|co|group|plc|gmbh|se|sa|fzco|fze)\b\.?',
        '', company_lower
    ).strip()

    if clean_company and clean_company in email_lower:
        return 0.95

    # Fuzzy ratio
    # Check against each word chunk in email
    words = email_lower.split()
    best_ratio = 0.0
    for i in range(len(words)):
        for length in range(1, min(5, len(words) - i + 1)):
            chunk = " ".join(words[i:i+length])
            ratio = SequenceMatcher(None, clean_company, chunk).ratio()
            best_ratio = max(best_ratio, ratio)

    return best_ratio


def match_email_to_application(email_text, subject, sender, applications):
    """
    Try to match an email to a tracked application.
    Returns (best_match, confidence) or (None, 0).
    """
    best_match = None
    best_score = 0.0

    combined_text = f"{subject} {sender} {email_text[:2000]}"

    for app in applications:
        score = 0.0

        # Company match (most important signal)
        company_sim = fuzzy_match_company(combined_text, app["company"])
        score += company_sim * 60  # Up to 60 points

        # Title match
        if app["title"]:
            title_lower = app["title"].lower()
            if title_lower in combined_text.lower():
                score += 25
            else:
                # Partial title match
                title_words = [w for w in title_lower.split() if len(w) > 3]
                matching_words = sum(1 for w in title_words if w in combined_text.lower())
                if title_words:
                    score += (matching_words / len(title_words)) * 15

        # Recency bonus (applied recently = more likely match)
        if app.get("applied_date"):
            try:
                applied = datetime.fromisoformat(app["applied_date"].replace("Z", "+00:00"))
                days_ago = (datetime.now(applied.tzinfo) - applied).days if applied.tzinfo else 30
                if days_ago < 7:
                    score += 10
                elif days_ago < 14:
                    score += 5
            except (ValueError, TypeError):
                pass

        if score > best_score:
            best_score = score
            best_match = app

    # Normalize to 0-100 confidence
    confidence = min(100, int(best_score))

    if confidence < 30:
        return None, 0

    return best_match, confidence


# ===================== STAGE CLASSIFICATION =====================

def classify_stage(email_text, subject):
    """Classify the application stage based on email content."""
    combined = f"{subject} {email_text}".lower()
    scores = {}

    for stage, config in STAGE_PATTERNS.items():
        count = 0
        matched_kws = []
        for kw in config["keywords"]:
            if kw.lower() in combined:
                count += 1
                matched_kws.append(kw)

        if count > 0:
            scores[stage] = {
                "score": count * config["weight"],
                "matched_keywords": matched_kws,
            }

    if not scores:
        return "unknown", 0, []

    # Sort by score descending
    best_stage = max(scores, key=lambda s: scores[s]["score"])
    best_info = scores[best_stage]

    # Confidence based on keyword match count
    confidence = min(95, int(30 + (best_info["score"] * 15)))

    return best_stage, confidence, best_info["matched_keywords"]


# ===================== MAIN RUN =====================

def run(result):
    """Main run function - scan Gmail and classify emails."""
    print("[tracker] Loading active applications...")
    applications = load_active_applications()
    print(f"[tracker] Found {len(applications)} tracked applications")

    if not applications:
        print("[tracker] WARNING: No active applications found in pipeline")

    print(f"[tracker] Scanning last {SEARCH_DAYS} days of email...")
    all_emails = list_recent_emails(days=SEARCH_DAYS)
    print(f"[tracker] Found {len(all_emails)} recent emails")

    # Filter for recruitment-related emails
    recruitment_emails = [e for e in all_emails if is_recruitment_email(e)]
    print(f"[tracker] {len(recruitment_emails)} appear recruitment-related")

    tracked_results = []
    stats = {
        "total_scanned": len(all_emails),
        "recruitment_related": len(recruitment_emails),
        "matched": 0,
        "unmatched": 0,
        "by_stage": {},
    }

    for i, email_info in enumerate(recruitment_emails):
        email_id = email_info["id"]
        subject = email_info.get("subject", "")
        sender = email_info.get("from", "")

        print(f"  [{i+1}/{len(recruitment_emails)}] Analyzing: {subject[:60]}...")

        # Read full body
        body = read_email_body(email_id)
        if not body:
            print(f"    Skipped - could not read body")
            continue

        # Match to application
        matched_app, match_confidence = match_email_to_application(
            body, subject, sender, applications
        )

        # Classify stage
        stage, stage_confidence, stage_keywords = classify_stage(body, subject)

        entry = {
            "email_id": email_id,
            "subject": subject,
            "from": sender,
            "date": email_info.get("date", ""),
            "stage": stage,
            "stage_confidence": stage_confidence,
            "stage_keywords": stage_keywords,
            "matched_application": None,
            "match_confidence": match_confidence,
            "body_preview": body[:300].replace("\n", " "),
        }

        if matched_app:
            entry["matched_application"] = {
                "id": matched_app["id"],
                "title": matched_app["title"],
                "company": matched_app["company"],
            }
            stats["matched"] += 1
        else:
            stats["unmatched"] += 1

        # Track stage stats
        stats["by_stage"][stage] = stats["by_stage"].get(stage, 0) + 1

        tracked_results.append(entry)

        # Small delay between email reads
        time.sleep(0.3)

    # Sort by actionability: offers > interviews > assessments > screens > rejections > generic
    stage_priority = {
        "offer": 0, "interview_invite": 1, "assessment": 2,
        "recruiter_screen": 3, "rejection": 4, "generic_response": 5,
        "unknown": 6,
    }
    tracked_results.sort(key=lambda x: (
        stage_priority.get(x["stage"], 99),
        -x["match_confidence"],
    ))

    # Build output
    output = {
        "generated_at": now_iso(),
        "scan_window_days": SEARCH_DAYS,
        "stats": stats,
        "active_applications_count": len(applications),
        "results": tracked_results,
        "action_items": _build_action_items(tracked_results),
    }

    result.set_data(output)
    result.set_kpi({
        "emails_scanned": stats["total_scanned"],
        "recruitment_emails": stats["recruitment_related"],
        "matched": stats["matched"],
        "unmatched": stats["unmatched"],
        "stages": stats["by_stage"],
    })

    # Print summary
    print(f"\n[tracker] === RESULTS ===")
    print(f"  Emails scanned: {stats['total_scanned']}")
    print(f"  Recruitment-related: {stats['recruitment_related']}")
    print(f"  Matched to applications: {stats['matched']}")
    print(f"  Unmatched (orphan): {stats['unmatched']}")
    print(f"  Stages: {json.dumps(stats['by_stage'])}")

    if output["action_items"]:
        print(f"\n  🔔 ACTION ITEMS:")
        for item in output["action_items"]:
            print(f"    - [{item['urgency']}] {item['action']}")


def _build_action_items(results):
    """Build action items from tracking results."""
    items = []

    for r in results:
        stage = r["stage"]
        company = r.get("matched_application", {}).get("company", "Unknown") if r.get("matched_application") else "Unknown"
        subject = r["subject"][:50]

        if stage == "offer":
            items.append({
                "urgency": "🔴 CRITICAL",
                "action": f"OFFER received from {company} - Review immediately",
                "email_id": r["email_id"],
                "company": company,
            })
        elif stage == "interview_invite":
            items.append({
                "urgency": "🟠 HIGH",
                "action": f"Interview invite from {company} - Schedule ASAP",
                "email_id": r["email_id"],
                "company": company,
            })
        elif stage == "assessment":
            items.append({
                "urgency": "🟠 HIGH",
                "action": f"Assessment from {company} - Complete by deadline",
                "email_id": r["email_id"],
                "company": company,
            })
        elif stage == "recruiter_screen":
            items.append({
                "urgency": "🟡 MEDIUM",
                "action": f"Recruiter screen request from {company} - Respond",
                "email_id": r["email_id"],
                "company": company,
            })

    return items


if __name__ == "__main__":
    agent_main(AGENT_NAME, run, OUTPUT_FILE, ttl_hours=4)
