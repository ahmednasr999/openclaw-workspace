#!/usr/bin/env python3
"""
email-agent.py — Reads Gmail via Himalaya CLI, categorizes emails by pattern matching.

Categories:
  - interview_invite: subject has "interview", "schedule", "availability"
  - recruiter_reach: from known recruiter domains
  - application_ack: "thank you for applying", "application received"
  - rejection: "unfortunately", "not moving forward", "other candidates"
  - assessment: "assessment", "test", "coding challenge", "case study"
  - follow_up_needed: reply to our email with question
"""

import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Import from agent-common.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
common = import_module("agent-common")

AgentResult = common.AgentResult
agent_main = common.agent_main
retry_with_backoff = common.retry_with_backoff
load_json = common.load_json
is_dry_run = common.is_dry_run
now_cairo = common.now_cairo
now_iso = common.now_iso
WORKSPACE = common.WORKSPACE
DATA_DIR = common.DATA_DIR

OUTPUT_PATH = DATA_DIR / "email-summary.json"

# Known recruiter domains (30+)
RECRUITER_DOMAINS = [
    "linkedin.com", "hays.com", "michaelpage.com", "roberthalf.com",
    "kornferry.com", "kpmg.com", "ey.com", "deloitte.com", "pwc.com",
    "bayt.com", "naukrigulf.com", "gulftalent.com", "monstergulf.com",
    "indeed.com", "glassdoor.com", "seek.com", "reed.com",
    "randstad.com", "adecco.com", "manpower.com", "kellyservices.com",
    "pagegroup.com", "egonzehnder.com", "spencerstuart.com", "russellreynolds.com",
    "korn-ferry.com", "heidrick.com", "mckinsey.com", "bain.com", "bcg.com",
    "accenture.com", "capgemini.com", "infosys.com", "wipro.com", "tcs.com",
    "cognizant.com", "mercer.com", "aon.com", "wtwco.com", "gallagher.com",
    "cooperfitch.com", "charterhouse.ae", "linkme.qa", "gisgulf.com",
    "talentarabe.com", "antonycurtis.com", "excelsiorgroup.ae"
]

# Pattern matching rules
INTERVIEW_PATTERNS = [
    r'\binterview\b', r'\bscheduled?\b.*\bcall\b', r'\bavailability\b',
    r'\bmeet\b.*\bteam\b', r'\bcalendar\b.*\blink\b', r'\bschedule\b.*\bmeeting\b',
    r'\bzoom\b.*\blink\b', r'\bteams\b.*\binvite\b', r'\bgoogle meet\b'
]

APPLICATION_ACK_PATTERNS = [
    r'thank\s*you\s*(for)?\s*(your)?\s*appl', r'application\s*(has been)?\s*received',
    r'we\s*(have)?\s*received\s*your', r'confirming\s*(your)?\s*application',
    r'application\s*confirmed', r'successfully\s*applied'
]

REJECTION_PATTERNS = [
    r'unfortunately', r'regret\s*to\s*inform', r'not\s*(be)?\s*moving\s*forward',
    r'other\s*candidates', r'not\s*selected', r'position\s*(has been)?\s*filled',
    r'decided\s*(to)?\s*not\s*proceed', r'will\s*not\s*be\s*continuing',
    r'not\s*a\s*match', r'pursuing\s*other\s*candidates'
]

ASSESSMENT_PATTERNS = [
    r'\bassessment\b', r'\btest\b', r'\bcoding\s*challenge\b', r'\bcase\s*study\b',
    r'\btechnical\s*exercise\b', r'\bhome\s*assignment\b', r'\btake\s*home\b',
    r'\bhackerrank\b', r'\bcodility\b', r'\bleetcode\b'
]


def extract_domain(email_address):
    """Extract domain from email address."""
    if not email_address:
        return ""
    match = re.search(r'@([\w.-]+)', email_address)
    return match.group(1).lower() if match else ""


def is_recruiter_domain(domain):
    """Check if domain is a known recruiter."""
    for rec_domain in RECRUITER_DOMAINS:
        if domain.endswith(rec_domain) or rec_domain in domain:
            return True
    return False


def matches_patterns(text, patterns):
    """Check if text matches any of the patterns."""
    text = text.lower() if text else ""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def categorize_email(subject, from_addr, body=""):
    """Categorize an email based on subject, sender, and body."""
    categories = []
    text = f"{subject} {body}".lower()
    
    # Check interview patterns (highest priority)
    if matches_patterns(text, INTERVIEW_PATTERNS):
        categories.append("interview_invite")
    
    # Check recruiter domain
    domain = extract_domain(from_addr)
    if is_recruiter_domain(domain):
        categories.append("recruiter_reach")
    
    # Check application acknowledgment
    if matches_patterns(text, APPLICATION_ACK_PATTERNS):
        categories.append("application_ack")
    
    # Check rejection
    if matches_patterns(text, REJECTION_PATTERNS):
        categories.append("rejection")
    
    # Check assessment
    if matches_patterns(text, ASSESSMENT_PATTERNS):
        categories.append("assessment")
    
    # Check for follow-up needed (reply with question)
    if re.search(r'\?\s*$', text) or re.search(r'please\s*(let|confirm|reply|respond)', text):
        if not categories:  # Only if no other category
            categories.append("follow_up_needed")
    
    return categories if categories else ["other"]


@retry_with_backoff(max_retries=3, base_delay=2)
def run_himalaya_list():
    """Run himalaya envelope list command."""
    result = subprocess.run(
        ["himalaya", "envelope", "list", "-w", "80", "-s", "50"],
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode != 0:
        raise Exception(f"Himalaya list failed: {result.stderr}")
    return result.stdout


@retry_with_backoff(max_retries=2, base_delay=1)
def run_himalaya_read(email_id):
    """Read a single email by ID."""
    result = subprocess.run(
        ["himalaya", "read", str(email_id)],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        return ""  # Don't fail on individual email read errors
    return result.stdout


def parse_himalaya_list(output):
    """Parse himalaya envelope list output."""
    emails = []
    lines = output.strip().split('\n')
    
    # Skip header lines, warnings, and separators
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip ANSI codes, warnings, headers, separators
        if line.startswith('[') or line.startswith('|--') or 'ID' in line and 'FLAGS' in line:
            continue
        if line.startswith('|') and '|' in line[1:]:
            # Parse table format: | ID | FLAGS | SUBJECT | FROM | DATE |
            parts = [p.strip() for p in line.split('|')]
            # Remove empty parts from leading/trailing |
            parts = [p for p in parts if p]
            
            if len(parts) >= 4:
                try:
                    email_id = parts[0].strip()
                    flags = parts[1].strip() if len(parts) > 1 else ""
                    subject = parts[2].strip() if len(parts) > 2 else ""
                    from_addr = parts[3].strip() if len(parts) > 3 else ""
                    date_str = parts[4].strip() if len(parts) > 4 else ""
                    
                    if email_id and email_id.isdigit():
                        emails.append({
                            "id": email_id,
                            "flags": flags,
                            "from": from_addr,
                            "subject": subject,
                            "date": date_str,
                            "unread": "*" in flags  # * indicates unread in himalaya
                        })
                except Exception:
                    continue
    
    return emails


def run_email_agent(result: AgentResult):
    """Main agent logic."""
    now = now_cairo()
    
    print("  Running himalaya envelope list...")
    list_output = run_himalaya_list()
    emails = parse_himalaya_list(list_output)
    print(f"  Parsed {len(emails)} emails")
    
    # Categorize all emails
    categorized = {
        "interview_invite": [],
        "recruiter_reach": [],
        "application_ack": [],
        "rejection": [],
        "assessment": [],
        "follow_up_needed": [],
        "other": []
    }
    
    actionable_emails = []
    interviews_detected = 0
    recruiter_messages = 0
    unread_actionable = 0
    
    for email in emails[:50]:  # Process up to 50
        # Get full email body for better categorization (first 10 only for speed)
        body = ""
        if emails.index(email) < 10:
            body = run_himalaya_read(email["id"])
        
        categories = categorize_email(email["subject"], email["from"], body)
        email["categories"] = categories
        
        # Add to categorized lists
        for cat in categories:
            if cat in categorized:
                categorized[cat].append({
                    "id": email["id"],
                    "from": email["from"],
                    "subject": email["subject"],
                    "date": email.get("date", ""),
                    "unread": email.get("unread", False)
                })
        
        # Track actionable
        if "interview_invite" in categories or "assessment" in categories or "follow_up_needed" in categories:
            actionable_emails.append(email)
            if email.get("unread"):
                unread_actionable += 1
        
        if "interview_invite" in categories:
            interviews_detected += 1
        if "recruiter_reach" in categories:
            recruiter_messages += 1
    
    # Build summary
    summary = {
        "scan_time": now_iso(),
        "total_scanned": len(emails),
        "by_category": {
            cat: len(items) for cat, items in categorized.items()
        },
        "interview_invites": categorized["interview_invite"][:10],
        "recruiter_messages": categorized["recruiter_reach"][:10],
        "application_acks": categorized["application_ack"][:10],
        "rejections": categorized["rejection"][:10],
        "assessments": categorized["assessment"][:5],
        "follow_ups_needed": categorized["follow_up_needed"][:5],
        "actionable_count": len(actionable_emails)
    }
    
    result.set_data(summary)
    
    # KPIs
    result.set_kpi({
        "emails_processed": len(emails),
        "actionable": len(actionable_emails),
        "interviews_detected": interviews_detected,
        "recruiter_messages": recruiter_messages,
        "unread_actionable": unread_actionable
    })
    
    # Recommendations
    if interviews_detected > 0:
        result.add_recommendation(
            action="respond_immediately",
            target=f"{interviews_detected} interview invite(s)",
            reason="Interview invitations require prompt response",
            urgency="critical"
        )
    
    if recruiter_messages > 0:
        result.add_recommendation(
            action="review_and_respond",
            target=f"{recruiter_messages} recruiter message(s)",
            reason="Recruiter outreach could lead to opportunities",
            urgency="high"
        )
    
    if unread_actionable > 0:
        result.add_recommendation(
            action="check_inbox",
            target=f"{unread_actionable} unread actionable email(s)",
            reason="Unread emails need attention",
            urgency="high"
        )
    
    if categorized["assessment"]:
        result.add_recommendation(
            action="complete_assessment",
            target=f"{len(categorized['assessment'])} assessment(s)",
            reason="Assessments have deadlines",
            urgency="high"
        )


if __name__ == "__main__":
    agent_main(
        agent_name="email-agent",
        run_func=run_email_agent,
        output_path=OUTPUT_PATH,
        ttl_hours=4,
        version="1.0.0"
    )
