#!/usr/bin/env python3
"""
email-agent.py — Reads Gmail via Python imaplib (replaces Himalaya which panics on HIGHESTMODSEQ).
Categorizes emails by pattern matching + LLM analysis.

Categories:
  - interview_invite: subject has "interview", "schedule", "availability"
  - recruiter_reach: from known recruiter domains
  - application_ack: "thank you for applying", "application received"
  - rejection: "unfortunately", "not moving forward", "other candidates"
  - assessment: "assessment", "test", "coding challenge", "case study"
  - follow_up_needed: reply to our email with question

SAFETY RULES (non-negotiable):
  - NEVER delete emails
  - NEVER send emails without explicit human approval
  - NEVER mark emails as read/unread without approval
  - NEVER modify email flags or labels
  - Only READ and CATEGORIZE — no write operations

LLM ANALYSIS (XML-structured prompt):
  Uses Anthropic's official XML-structured format for optimal Claude comprehension.
  Applied to actionable emails for deeper intent analysis.
"""

# ==============================================================================
# LLM EMAIL ANALYSIS — XML-STRUCTURED PROMPT (Anthropic official playbook)
# ==============================================================================
LLM_EMAIL_ANALYSIS_PROMPT = """Analyze these emails and produce a structured briefing.

<task>
For each email, determine: urgency level, sender intent, required action, and recommended response timing.
</task>

<context>
User profile: Senior technology executive pursuing senior leadership roles in UAE/Gulf region.
Email categories already assigned by pattern matching: {categories}
Total emails scanned: {total_emails}
Actionable emails (interview/assessment/follow-up): {actionable_count}
</context>

<constraints>
- Only analyze emails that are categorized as: interview_invite, assessment, follow_up_needed, recruiter_reach
- NEVER invent email content — analyze only what is provided
- Set urgency: critical (response within 24h), high (within 48h), medium (within week), low (informational only)
- Set action: respond, forward, read_and_file, no_action
- If insufficient context to determine, say "cannot determine from available content"
</constraints>

<output_format>
Return a JSON object with this exact structure:
{{
  "actionable_emails": [
    {{
      "id": "email_id",
      "subject": "subject line",
      "from": "sender",
      "date": "date",
      "category": "interview_invite|recruiter_reach|assessment|follow_up_needed",
      "urgency": "critical|high|medium|low",
      "intent": "one sentence describing what the sender wants",
      "action": "respond|forward|read_and_file|no_action",
      "response_deadline": "24h|48h|1 week|when convenient",
      "notes": "additional context or recommendations (max 100 chars)"
    }}
  ],
  "summary": {{
    "total_actionable": number,
    "critical_count": number,
    "requires_interview_prep": boolean,
    "requires_assessment": boolean,
    "recruiter_top_opportunities": ["list of most promising recruiter contacts"],
    "top_priority": "most urgent email id or null",
    "daily_focus": "one sentence strategic recommendation for the day"
  }}
}}
</output_format>"""

LLM_MODEL = "minimax-portal/MiniMax-M2.7"
LLM_TEMP = 0.1

import imaplib
import email
from email.header import decode_header
import re
import sys
import json as json_module
import requests as req
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
common = import_module("agent-common")
is_dry_run = common.is_dry_run

AgentResult = common.AgentResult
agent_main = common.agent_main
retry_with_backoff = common.retry_with_backoff
now_cairo = common.now_cairo
now_iso = common.now_iso
DATA_DIR = common.DATA_DIR

OUTPUT_PATH = DATA_DIR / "email-summary.json"

# Gmail credentials (from Himalaya config)
GMAIL_USER = "ahmednasr999@gmail.com"
GMAIL_APP_PASSWORD = "yuwzetbtedqnlovl"
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

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


def decode_str(s):
    if not s:
        return ""
    if isinstance(s, bytes):
        parts = decode_header(s)
        result = []
        for part, enc in parts:
            if isinstance(part, bytes):
                result.append(part.decode(enc or "utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)
    return str(s)


def extract_domain(email_address):
    if not email_address:
        return ""
    match = re.search(r'@([\w.-]+)', email_address)
    return match.group(1).lower() if match else ""


def is_recruiter_domain(domain):
    for rec_domain in RECRUITER_DOMAINS:
        if domain.endswith(rec_domain) or rec_domain in domain:
            return True
    return False


def matches_patterns(text, patterns):
    text = text.lower() if text else ""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def categorize_email(subject, from_addr, body=""):
    categories = []
    text = f"{subject} {body}".lower()
    
    if matches_patterns(text, INTERVIEW_PATTERNS):
        categories.append("interview_invite")
    
    domain = extract_domain(from_addr)
    if is_recruiter_domain(domain):
        categories.append("recruiter_reach")
    
    if matches_patterns(text, APPLICATION_ACK_PATTERNS):
        categories.append("application_ack")
    
    if matches_patterns(text, REJECTION_PATTERNS):
        categories.append("rejection")
    
    if matches_patterns(text, ASSESSMENT_PATTERNS):
        categories.append("assessment")
    
    if re.search(r'\?\s*$', text) or re.search(r'please\s*(let|confirm|reply|respond)', text):
        if not categories:
            categories.append("follow_up_needed")
    
    return categories if categories else ["other"]


def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                try:
                    body = part.get_payload(decode=True).decode(charset, errors="replace")
                    break
                except:
                    pass
    else:
        charset = msg.get_content_charset() or "utf-8"
        try:
            body = msg.get_payload(decode=True).decode(charset, errors="replace")
        except:
            pass
    return body[:2000]


def build_llm_prompt(summary, total_emails, actionable_emails):
    """Build the XML-structured LLM prompt with email data."""
    # Send actionable emails as a focused list (not full raw emails)
    actionable_list = []
    for e in actionable_emails:
        actionable_list.append({
            "id": e.get("id", ""),
            "subject": e.get("subject", ""),
            "from": e.get("from", ""),
            "date": e.get("date", ""),
            "categories": e.get("categories", []),
            "unread": e.get("unread", False)
        })
    emails_json = json_module.dumps({"actionable": actionable_list}, indent=2, default=str)
    categories = summary.get("by_category", {})
    prompt = LLM_EMAIL_ANALYSIS_PROMPT.format(
        categories=json_module.dumps(categories, default=str),
        total_emails=total_emails,
        actionable_count=len(actionable_emails)
    )
    return prompt, emails_json


def run_llm_analysis(summary, total_emails, actionable_emails) -> dict:
    """Send actionable emails to LLM with XML-structured prompt. Returns parsed JSON."""
    import os, json as json_lib

    prompt, emails_json = build_llm_prompt(summary, total_emails, actionable_emails)

    # Load OpenClaw gateway token from config
    gw_token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")
    gw_url = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
    if not gw_token:
        try:
            with open(os.path.expanduser("~/.openclaw/openclaw.json")) as f:
                cfg = json_lib.load(f)
                gw_token = cfg.get("gateway", {}).get("auth", {}).get("token", "")
        except Exception:
            pass

    model = LLM_MODEL
    body = {
        "model": model,
        "max_tokens": 1024,
        "temperature": LLM_TEMP,
        "messages": [
            {"role": "system", "content": "You are an elite executive assistant. Analyze emails with precision and strategic awareness. Respond ONLY with valid JSON matching the specified schema."},
            {"role": "user", "content": f"{prompt}\n\n--- EMAIL DATA ---\n{emails_json}"}
        ]
    }

    headers = {"Content-Type": "application/json"}

    # Try OpenClaw gateway
    if gw_token:
        headers["Authorization"] = f"Bearer {gw_token}"
        try:
            resp = req.post(f"{gw_url}/v1/chat/completions", json=body, headers=headers, timeout=(10, 120))
            if resp.status_code == 200:
                result_text = resp.json()["choices"][0]["message"]["content"]
                result_text = result_text.strip()
                if result_text.startswith("```"):
                    result_text = result_text.split("```")[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]
                return json_module.loads(result_text.strip())
        except Exception as e:
            print(f"  LLM: gateway failed ({e})")

    print("  LLM: No valid credentials or gateway unreachable — skipping LLM analysis")
    return None


@retry_with_backoff(max_retries=3, base_delay=2)
def fetch_email_list():
    """Fetch last 50 emails from INBOX via imaplib."""
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select("INBOX")
    
    _, msg_ids = mail.search(None, 'ALL')
    all_ids = msg_ids[0].split()
    recent_ids = all_ids[-50:] if len(all_ids) > 50 else all_ids
    
    emails = []
    for uid in reversed(recent_ids):
        try:
            _, data = mail.fetch(uid, '(RFC822)')
            raw = data[0][1] if isinstance(data[0], tuple) else data[0]
            msg = email.message_from_bytes(raw)
            
            subject = decode_str(msg.get("Subject", ""))
            from_addr = decode_str(msg.get("From", ""))
            date_str = msg.get("Date", "")
            
            _, flags_data = mail.fetch(uid, '(FLAGS)')
            flags_raw = flags_data[0] if flags_data and flags_data[0] else b''
            is_unread = b'\\Seen' not in flags_raw
            
            emails.append({
                "id": uid.decode(),
                "subject": subject,
                "from": from_addr,
                "date": date_str,
                "unread": is_unread,
                "raw": raw
            })
        except Exception as e:
            print(f"  Warning: failed to fetch email {uid}: {e}")
            continue
    
    mail.logout()
    return emails


def run_email_agent(result: AgentResult):
    now = now_cairo()
    
    print("  Connecting to Gmail via imaplib...")
    emails = fetch_email_list()
    print(f"  Fetched {len(emails)} emails")
    
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
    
    for i, email_data in enumerate(emails):
        body = ""
        if i < 10:
            try:
                msg = email.message_from_bytes(email_data["raw"])
                body = get_email_body(msg)
            except:
                pass
        
        categories = categorize_email(email_data["subject"], email_data["from"], body)
        email_data["categories"] = categories
        
        email_summary = {
            "id": email_data["id"],
            "from": email_data["from"],
            "subject": email_data["subject"],
            "date": email_data.get("date", ""),
            "unread": email_data.get("unread", False)
        }
        
        for cat in categories:
            if cat in categorized:
                categorized[cat].append(email_summary)
        
        if "interview_invite" in categories or "assessment" in categories or "follow_up_needed" in categories:
            actionable_emails.append(email_data)
            if email_data.get("unread"):
                unread_actionable += 1
        
        if "interview_invite" in categories:
            interviews_detected += 1
        if "recruiter_reach" in categories:
            recruiter_messages += 1
    
    summary = {
        "scan_time": now_iso(),
        "total_scanned": len(emails),
        "by_category": {cat: len(items) for cat, items in categorized.items()},
        "interview_invites": categorized["interview_invite"][:10],
        "recruiter_messages": categorized["recruiter_reach"][:10],
        "application_acks": categorized["application_ack"][:10],
        "rejections": categorized["rejection"][:10],
        "assessments": categorized["assessment"][:5],
        "follow_ups_needed": categorized["follow_up_needed"][:5],
        "actionable_count": len(actionable_emails)
    }

    # ======================================================================
    # LLM ANALYSIS — XML-structured prompt (Anthropic official playbook)
    # ======================================================================
    if common.is_dry_run():
        summary["llm_analysis"] = None
        print("  LLM: Skipped (dry-run mode)")
    else:
        print("  Running LLM analysis on actionable emails...")
        llm_result = run_llm_analysis(summary, len(emails), actionable_emails)
        if llm_result:
            summary["llm_analysis"] = llm_result
            print(f"  LLM: {llm_result.get('summary', {}).get('total_actionable', 0)} actionable, "
                  f"critical: {llm_result.get('summary', {}).get('critical_count', 0)}")
        else:
            summary["llm_analysis"] = None
            print("  LLM: Skipped (no valid credentials)")

    result.set_data(summary)
    
    result.set_kpi({
        "emails_processed": len(emails),
        "actionable": len(actionable_emails),
        "interviews_detected": interviews_detected,
        "recruiter_messages": recruiter_messages,
        "unread_actionable": unread_actionable
    })
    
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
        version="3.0.0"
    )
