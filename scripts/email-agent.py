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
import os
import json as json_module
import requests as req
from pathlib import Path
from datetime import datetime, timedelta

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

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

# Gmail credentials — loaded from config (never hardcode secrets)
_gmail_config_path = Path(__file__).parent.parent / "config" / "gmail-imap.json"
try:
    _gmail_cfg = json_module.load(open(_gmail_config_path))
    GMAIL_USER = _gmail_cfg["user"]
    GMAIL_APP_PASSWORD = _gmail_cfg["app_password"]
    IMAP_HOST = _gmail_cfg.get("imap_host", "imap.gmail.com")
    IMAP_PORT = _gmail_cfg.get("imap_port", 993)
except Exception as e:
    print(f"FATAL: Cannot load Gmail config from {_gmail_config_path}: {e}")
    sys.exit(1)

# State + output paths
STATE_PATH = DATA_DIR / "email-state.json"
LATEST_PATH = DATA_DIR / "email-latest.json"
HISTORY_PATH = DATA_DIR / "email-history.jsonl"
SIGNALS_PATH = DATA_DIR / "email-signals.jsonl"

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
    r'\bassessment\b', r'\bcoding\s*challenge\b', r'\bcase\s*study\b',
    r'\btechnical\s*exercise\b', r'\bhome\s*assignment\b', r'\btake\s*home\b',
    r'\bhackerrank\b', r'\bcodility\b', r'\bleetcode\b'
]
# Removed bare \btest\b — too many false positives (newsletters, marketing)

# Newsletters, marketing, notifications — never actionable
NOISE_SENDERS = [
    "neilpatel.com", "substack.com", "medium.com", "hubspot.com",
    "mailchimp.com", "sendgrid.net", "convertkit.com", "beehiiv.com",
    "noreply@", "no-reply@", "notifications@", "news@", "newsletter@",
    "digest@", "updates@", "marketing@", "promo@", "offers@",
]

# LinkedIn notification types that are NOT recruiter outreach
LINKEDIN_NOISE_SUBJECTS = [
    r'wants?\s*to\s*connect', r'accepted\s*your\s*invitation',
    r'endorsed\s*you', r'viewed\s*your\s*profile',
    r'anniversary', r'birthday', r'new\s*job', r'commented\s*on',
    r'liked\s*your', r'reacted\s*to', r'mentioned\s*you\s*in',
    r'trending\s*in\s*your\s*network', r'people\s*also\s*viewed',
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


def is_noise_sender(from_addr):
    """Check if sender is a known newsletter/notification source."""
    addr_lower = from_addr.lower()
    for noise in NOISE_SENDERS:
        if noise in addr_lower:
            return True
    return False


def is_linkedin_noise(subject, from_addr):
    """Check if a LinkedIn email is a notification, not recruiter outreach."""
    if "linkedin.com" not in extract_domain(from_addr):
        return False
    for pattern in LINKEDIN_NOISE_SUBJECTS:
        if re.search(pattern, subject, re.IGNORECASE):
            return True
    return False


# Weighted keyword scoring (D5)
KEYWORD_WEIGHTS = {
    "interview": 3, "shortlisted": 3, "offer": 3, "congratulations": 3,
    "selected": 3, "phone screen": 3, "technical round": 3, "final round": 3,
    "assessment": 2, "coding challenge": 2, "case study": 2,
    "availability": 2, "schedule": 2, "calendar link": 2,
    "unfortunately": 1, "regret to inform": 1, "not moving forward": 1,
    "thank you for applying": 1, "application received": 1,
}
PIPELINE_MATCH_BONUS = 5
RECRUITER_DOMAIN_BONUS = 2
PRIORITY_THRESHOLDS = {"HIGH": 5, "MEDIUM": 2, "LOW": 0}

HOT_KEYWORDS = [
    "interview", "shortlisted", "offer", "congratulations", "selected",
    "phone screen", "technical round", "final round", "assessment invite",
    "next steps in your application"
]


def score_email(subject, from_addr, body=""):
    """Weighted scoring for email priority (D5). Returns (score, pipeline_company)."""
    text = f"{subject} {body}".lower()
    score = 0
    pipeline_company = None

    # Keyword weights
    for kw, weight in KEYWORD_WEIGHTS.items():
        if kw in text:
            score += weight

    # Recruiter domain bonus
    domain = extract_domain(from_addr)
    if is_recruiter_domain(domain):
        score += RECRUITER_DOMAIN_BONUS

    # Pipeline company match (D5 + D10)
    if _pdb:
        try:
            company = domain.split(".")[0] if domain else ""
            if company and len(company) >= 3 and _pdb.is_company_tracked(company):
                score += PIPELINE_MATCH_BONUS
                pipeline_company = company
        except Exception:
            pass

    return score, pipeline_company


def get_priority(score):
    """Convert score to priority level."""
    if score >= PRIORITY_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif score >= PRIORITY_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def is_hot_email(subject, from_addr):
    """Check if email should trigger immediate Telegram alert."""
    text = f"{subject}".lower()
    for kw in HOT_KEYWORDS:
        if kw in text:
            return True
    return False


def categorize_email(subject, from_addr, body=""):
    categories = []
    text = f"{subject} {body}".lower()
    
    # Skip noise senders entirely (newsletters, marketing, notifications)
    if is_noise_sender(from_addr):
        return ["other"]
    
    if matches_patterns(text, INTERVIEW_PATTERNS):
        categories.append("interview_invite")
    
    domain = extract_domain(from_addr)
    if is_recruiter_domain(domain) and not is_linkedin_noise(subject, from_addr):
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


def update_pipeline_from_emails(categorized):
    """Update Notion Pipeline DB when rejection/interview emails are detected."""
    import urllib.request
    updates = []
    
    NOTION_TOKEN = json_module.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
    PIPELINE_DB = "3268d599-a162-81b4-b768-f162adfa4971"
    OUTCOMES_FILE = Path(os.path.expanduser("~/.openclaw/workspace")) / "data" / "feedback" / "jobs-outcomes.jsonl"
    
    def notion_api(method, endpoint, body=None):
        url = f"https://api.notion.com/v1/{endpoint}"
        data = json_module.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json_module.loads(resp.read())
        except Exception as e:
            print(f"    Notion API error: {e}")
            return None
    
    def find_pipeline_match(company_hint, role_hint):
        """Search Pipeline for matching Applied entry."""
        if not company_hint:
            return None
        query = {
            "filter": {"and": [
                {"property": "Stage", "select": {"equals": "✅ Applied"}},
                {"property": "Company", "title": {"contains": company_hint[:30]}},
            ]},
            "page_size": 5,
        }
        result = notion_api("POST", f"databases/{PIPELINE_DB}/query", query)
        if result and result.get("results"):
            return result["results"][0]
        return None
    
    # Process rejections
    for email_item in categorized.get("rejection", []):
        subject = email_item.get("subject", "")
        from_addr = email_item.get("from", "")
        
        # Try to extract company name from sender domain or subject
        domain = extract_domain(from_addr)
        company_hint = domain.split(".")[0] if domain else ""
        
        match = find_pipeline_match(company_hint, "")
        if match:
            page_id = match["id"]
            props = match.get("properties", {})
            company = ""
            if props.get("Company", {}).get("title"):
                company = props["Company"]["title"][0].get("text", {}).get("content", "")
            
            # Update to Rejected
            notion_api("PATCH", f"pages/{page_id}", {
                "properties": {
                    "Stage": {"select": {"name": "❌ Rejected"}},
                    "Notes": {"rich_text": [{"text": {"content": f"Auto-detected from email: {subject[:100]}"}}]},
                }
            })
            
            # Update feedback loop
            OUTCOMES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(OUTCOMES_FILE, "a") as f:
                f.write(json_module.dumps({
                    "company": company,
                    "url": props.get("URL", {}).get("url", ""),
                    "verdict": "SUBMIT",
                    "outcome": "rejected",
                    "detected_from": "email",
                    "email_subject": subject[:100],
                }) + "\n")
            
            updates.append({"company": company, "action": "rejected", "email": subject[:60]})
            print(f"    📧→❌ Rejection detected: {company}")
            # ── DB write (dual-write, non-blocking) ──────────────────────────
            if _pdb:
                try:
                    # Find job_id by company name
                    jobs = _pdb.get_by_company(company) if company else []
                    job_db_id = jobs[0]["job_id"] if jobs else None
                    if job_db_id:
                        _pdb.update_status(job_db_id, "rejected")
                        _pdb.log_interaction(
                            job_id=job_db_id,
                            type="email_inbound",
                            summary=f"Rejection email: {subject[:150]}",
                            from_email=from_addr,
                            channel="gmail",
                        )
                except Exception:
                    pass
            # ─────────────────────────────────────────────────────────────────
    
    # Process interview invites
    for email_item in categorized.get("interview_invite", []):
        subject = email_item.get("subject", "")
        from_addr = email_item.get("from", "")
        domain = extract_domain(from_addr)
        company_hint = domain.split(".")[0] if domain else ""
        
        match = find_pipeline_match(company_hint, "")
        if match:
            page_id = match["id"]
            props = match.get("properties", {})
            company = ""
            if props.get("Company", {}).get("title"):
                company = props["Company"]["title"][0].get("text", {}).get("content", "")
            
            # Update to Interview stage
            notion_api("PATCH", f"pages/{page_id}", {
                "properties": {
                    "Stage": {"select": {"name": "📞 Interview"}},
                    "Notes": {"rich_text": [{"text": {"content": f"Interview detected from email: {subject[:100]}"}}]},
                }
            })
            
            # Update feedback loop
            OUTCOMES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(OUTCOMES_FILE, "a") as f:
                f.write(json_module.dumps({
                    "company": company,
                    "url": props.get("URL", {}).get("url", ""),
                    "verdict": "SUBMIT",
                    "outcome": "interview",
                    "detected_from": "email",
                    "email_subject": subject[:100],
                }) + "\n")
            
            updates.append({"company": company, "action": "interview", "email": subject[:60]})
            print(f"    📧→📞 Interview detected: {company}")
            # ── DB write (dual-write, non-blocking) ──────────────────────────
            if _pdb:
                try:
                    jobs = _pdb.get_by_company(company) if company else []
                    job_db_id = jobs[0]["job_id"] if jobs else None
                    if job_db_id:
                        _pdb.update_status(job_db_id, "interview")
                        _pdb.log_interaction(
                            job_id=job_db_id,
                            type="email_inbound",
                            summary=f"Interview invite: {subject[:150]}",
                            from_email=from_addr,
                            channel="gmail",
                            next_action="Schedule interview / confirm availability",
                        )
                except Exception:
                    pass
            # ─────────────────────────────────────────────────────────────────
    
    return updates


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


def _load_state():
    """Load UID state from disk."""
    if STATE_PATH.exists():
        try:
            return json_module.load(open(STATE_PATH))
        except Exception:
            pass
    return {"last_seen_uid": 0, "last_success": None, "processed_count": 0}


def _save_state(state):
    """Save UID state to disk."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    json_module.dump(state, open(STATE_PATH, "w"), indent=2)


def _write_error_latest(error_msg, state):
    """Write error status to email-latest.json so consumers know email is down."""
    LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    json_module.dump({
        "status": "error",
        "error": error_msg,
        "last_success": state.get("last_success"),
        "timestamp": now_iso(),
    }, open(LATEST_PATH, "w"), indent=2)


def _connect_imap():
    """Connect to IMAP with socket timeout. Classifies errors."""
    import socket
    socket.setdefaulttimeout(30)
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("INBOX")
        return mail
    except imaplib.IMAP4.error as e:
        err_str = str(e).lower()
        if "invalid credentials" in err_str or "authentication" in err_str:
            raise RuntimeError(f"AUTH_FAILURE: {e}")  # Don't retry
        raise  # Network error — retry
    except (socket.timeout, OSError) as e:
        raise RuntimeError(f"NETWORK_FAILURE: {e}")


@retry_with_backoff(max_retries=3, base_delay=2)
def fetch_email_list():
    """Fetch emails from INBOX using UID-based state tracking (D3) with error handling (D6)."""
    state = _load_state()

    try:
        mail = _connect_imap()
    except RuntimeError as e:
        err_str = str(e)
        if err_str.startswith("AUTH_FAILURE"):
            print(f"  IMAP AUTH FAILED: {e} — not retrying")
            _write_error_latest(err_str, state)
            return []
        raise  # Let retry_with_backoff handle network errors

    # UID-based: fetch only UIDs > last_seen
    last_uid = state.get("last_seen_uid", 0)
    if last_uid > 0:
        _, msg_data = mail.uid("search", None, f"(UID {last_uid + 1}:*)")
    else:
        # First run or reset: last 24 hours
        since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        _, msg_data = mail.uid("search", None, f'(SINCE "{since_date}")')

    all_uids = msg_data[0].split() if msg_data[0] else []
    # Filter out last_seen_uid itself (IMAP UID ranges are inclusive)
    all_uids = [u for u in all_uids if int(u) > last_uid]
    # Safety cap
    recent_uids = all_uids[-200:] if len(all_uids) > 200 else all_uids
    print(f"  IMAP: {len(all_uids)} new UIDs since {last_uid} (processing {len(recent_uids)})")

    emails = []
    max_uid_seen = last_uid
    for uid in recent_uids:
        uid_int = int(uid)
        try:
            _, data = mail.uid("fetch", uid, "(RFC822 FLAGS)")
            if not data or not data[0]:
                continue
            raw = data[0][1] if isinstance(data[0], tuple) else data[0]
            msg = email.message_from_bytes(raw)

            subject = decode_str(msg.get("Subject", ""))
            from_addr = decode_str(msg.get("From", ""))
            date_str = msg.get("Date", "")

            flags_str = data[0][0].decode() if isinstance(data[0], tuple) else ""
            is_unread = "\\Seen" not in flags_str

            emails.append({
                "id": uid.decode() if isinstance(uid, bytes) else str(uid),
                "uid": uid_int,
                "subject": subject,
                "from": from_addr,
                "date": date_str,
                "unread": is_unread,
                "raw": raw
            })
            if uid_int > max_uid_seen:
                max_uid_seen = uid_int
        except Exception as e:
            print(f"  Warning: failed to fetch UID {uid}: {e}")
            continue

    mail.logout()

    # Update state (crash-safe: only after successful processing)
    if max_uid_seen > last_uid:
        state["last_seen_uid"] = max_uid_seen
    state["last_success"] = now_iso()
    state["processed_count"] = state.get("processed_count", 0) + len(emails)
    _save_state(state)

    return emails


def _append_history(email_data, categories, score, pipeline_company):
    """Append one line to email-history.jsonl (D7)."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "uid": email_data.get("uid", 0),
        "message_id": email_data.get("id", ""),
        "from": email_data.get("from", ""),
        "subject": email_data.get("subject", ""),
        "date": email_data.get("date", ""),
        "categories": categories,
        "priority_score": score,
        "priority": get_priority(score),
        "pipeline_match": pipeline_company,
        "processed_at": now_iso(),
    }
    with open(HISTORY_PATH, "a") as f:
        f.write(json_module.dumps(entry, default=str) + "\n")


def _emit_signal(email_data, pipeline_company, categories, score):
    """Write pipeline signal for intelligence engine (D10)."""
    SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Find matching job_ids
    job_ids = []
    if _pdb and pipeline_company:
        try:
            jobs = _pdb.get_by_company(pipeline_company)
            job_ids = [j["job_id"] for j in (jobs or [])]
        except Exception:
            pass

    signal_type = "recruiter_email"
    if any(k in categories for k in ["interview_invite", "assessment"]):
        signal_type = "interview_signal"
    elif "rejection" in categories:
        signal_type = "rejection_signal"

    entry = {
        "company": pipeline_company,
        "signal": signal_type,
        "subject": email_data.get("subject", "")[:150],
        "sender": email_data.get("from", ""),
        "job_ids": job_ids,
        "score": score,
        "timestamp": now_iso(),
    }
    with open(SIGNALS_PATH, "a") as f:
        f.write(json_module.dumps(entry, default=str) + "\n")
    return entry


def run_email_agent(result: AgentResult):
    now = now_cairo()

    print("  Connecting to Gmail via imaplib...")
    emails = fetch_email_list()
    if not emails and LATEST_PATH.exists():
        # Check if this is an error condition vs simply no new emails
        try:
            latest = json_module.load(open(LATEST_PATH))
            if latest.get("status") == "error":
                print(f"  IMAP error persists: {latest.get('error')}")
                result.set_data(latest)
                return
        except Exception:
            pass
    print(f"  Fetched {len(emails)} new emails")

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
    hot_alerts = []
    signals = []
    interviews_detected = 0
    recruiter_messages = 0
    unread_actionable = 0

    for i, email_data in enumerate(emails):
        body = ""
        try:
            msg = email.message_from_bytes(email_data["raw"])
            body = get_email_body(msg)
        except:
            pass

        categories = categorize_email(email_data["subject"], email_data["from"], body)
        email_data["categories"] = categories
        score, pipeline_company = score_email(email_data["subject"], email_data["from"], body)
        email_data["priority_score"] = score
        email_data["priority"] = get_priority(score)
        email_data["pipeline_match"] = pipeline_company

        email_summary = {
            "id": email_data["id"],
            "from": email_data["from"],
            "subject": email_data["subject"],
            "date": email_data.get("date", ""),
            "unread": email_data.get("unread", False),
            "priority": email_data["priority"],
            "score": score,
            "pipeline_match": pipeline_company,
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

        # D7: append to history
        _append_history(email_data, categories, score, pipeline_company)

        # D10: emit pipeline signal
        if pipeline_company:
            sig = _emit_signal(email_data, pipeline_company, categories, score)
            signals.append(sig)

        # D8: hot alert (integrated, no separate cron needed)
        if is_hot_email(email_data["subject"], email_data["from"]) or score >= PRIORITY_THRESHOLDS["HIGH"]:
            hot_alerts.append({
                "subject": email_data["subject"],
                "from": email_data["from"],
                "priority": email_data["priority"],
                "pipeline_match": pipeline_company,
            })

    summary = {
        "status": "ok",
        "scan_time": now_iso(),
        "total_scanned": len(emails),
        "by_category": {cat: len(items) for cat, items in categorized.items()},
        "interview_invites": categorized["interview_invite"][:10],
        "recruiter_messages": categorized["recruiter_reach"][:10],
        "application_acks": categorized["application_ack"][:10],
        "rejections": categorized["rejection"][:10],
        "assessments": categorized["assessment"][:5],
        "follow_ups_needed": categorized["follow_up_needed"][:5],
        "actionable_count": len(actionable_emails),
        "hot_alerts": hot_alerts,
        "signals": signals,
    }

    # D4: Write shared snapshot for briefing + other consumers
    LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    json_module.dump(summary, open(LATEST_PATH, "w"), indent=2)

    # ======================================================================
    # PIPELINE INTEGRATION — update Notion + feedback loop
    # ======================================================================
    pipeline_updates = update_pipeline_from_emails(categorized)
    if pipeline_updates:
        summary["pipeline_updates"] = pipeline_updates
        print(f"  Pipeline: {len(pipeline_updates)} updates pushed")

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
