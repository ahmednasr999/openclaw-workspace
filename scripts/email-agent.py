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
  - application_response: recruiter requests application form/questionnaire/CV update
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
Actionable emails (interview/assessment/application-response/follow-up): {actionable_count}
</context>

<constraints>
- Only analyze emails that are categorized as: interview_invite, assessment, application_response, follow_up_needed, recruiter_reach
- NEVER invent email content — analyze only what is provided
- Use the provided body_excerpt and classification_evidence before assigning urgency
- Set urgency: critical (response within 24h), high (within 48h), medium (within week), low (informational only)
- Set action: respond, forward, read_and_file, no_action
- If the body excerpt does not prove an interview, assessment, recruiter opportunity, or reply need, do not mark it critical
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
      "category": "interview_invite|recruiter_reach|assessment|application_response|follow_up_needed",
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

LLM_MODEL = "openai-codex/gpt-5.5"
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
from functools import lru_cache
from email.utils import parseaddr
from html import unescape

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
PIPELINE_REVIEW_PATH = DATA_DIR / "email-pipeline-review.jsonl"
FEEDBACK_PATH = DATA_DIR / "email-feedback.jsonl"
MAX_UID_BATCH = int(os.environ.get("EMAIL_AGENT_MAX_UID_BATCH", "500"))
MIN_ACTIONABLE_CONFIDENCE = int(os.environ.get("EMAIL_AGENT_MIN_ACTIONABLE_CONFIDENCE", "55"))
MIN_HOT_CONFIDENCE = int(os.environ.get("EMAIL_AGENT_MIN_HOT_CONFIDENCE", "75"))
MIN_SIGNAL_CONFIDENCE = int(os.environ.get("EMAIL_AGENT_MIN_SIGNAL_CONFIDENCE", "70"))
_PENDING_STATE_UPDATE = None

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
    r'\bzoom\b.*\blink\b', r'\bteams\b.*\binvite\b', r'\bgoogle meet\b',
    r'\bnext\s*stage\b', r'\bnext\s*round\b', r'\bmove\s*forward\b',
    r'\bdeeper\s*conversation\b', r'\bpotential\s*next\s*steps\b'
]

STRICT_INTERVIEW_PATTERNS = [
    r'\binterview\b', r'\binterview\s+invitation\b', r'\binterview\s+invite\b',
    r'\bphone\s*screen\b', r'\btechnical\s*round\b', r'\bfinal\s*round\b',
    r'\bpanel\s*interview\b', r'\bhiring\s*manager\s*interview\b'
]

HIRING_CONTEXT_PATTERNS = [
    r'\byour\s+application\b', r'\bapplication\s+for\b', r'\bapplied\s+for\b',
    r'\bposition\b', r'\brole\b', r'\bcandidate\b', r'\bhiring\b',
    r'\brecruiter\b', r'\btalent\s+acquisition\b', r'\bhr\b',
    r'\bhuman\s+resources\b', r'\bjob\b', r'\bvacancy\b',
    r'\bcompensation\s+range\b', r'\bnext\s+steps\s+in\s+your\s+application\b',
    r'\bshortlisted\b', r'\bassessment\b', r'\bcoding\s*challenge\b',
    r'\bcase\s*study\b', r'\bapplication\s+form\b',
    r'\bpre[-\s]*interview\s+questionnaire\b', r'\blatest\s+updated\s+cv\b',
    r'\bupdated\s+cv\b', r'\bforms\.office\.com\b'
]

HIRING_SENDER_MARKERS = [
    "hr", "recruiter", "recruiting", "talent", "hiring", "careers", "jobs"
]

MEETING_INVITE_PATTERNS = [
    r'\bmicrosoft teams meeting\b', r'https://teams\.microsoft\.com/meet',
    r'\bmeeting id\b', r'\bjoin with google meet\b', r'\bzoom meeting\b',
    r'\bwebex\b', r'\btext/calendar\b', r'\bcontent-class:\s*urn:content-classes:calendarmessage\b',
    r'\bmethod:(request|cancel|reply)\b', r'\borganizer:\b', r'\bjoin:\s*https?://'
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

APPLICATION_RESPONSE_PATTERNS = [
    r'\bapplication\s+form\b',
    r'\bcomplete\s+and\s+submit\b',
    r'\bcomplete\s+the\s+application\s+form\b',
    r'\bsubmit\s+the\s+application\s+form\b',
    r'\bpre[-\s]*interview\s+questionnaire\b',
    r'\bshort\s+questionnaire\b',
    r'\bforms\.office\.com\b',
    r'\blatest\s+updated\s+cv\b',
    r'\blatest\s+cv\b',
    r'\bupdated\s+cv\b',
    r'\bshare\s+your\s+.*cv\b',
    r'\bjob\s+description\b.*\battached\b',
]

FOLLOW_UP_PATTERNS = [
    r'please\s*(let|confirm|reply|respond)',
    r'could\s+you\s+share',
    r'would\s+you\s+be\s+able\s+to',
    r'looking\s+forward\s+to\s+your\s+response',
    r'before\s+we\s+move\s+forward'
]

# Newsletters, marketing, notifications — never actionable
NOISE_SENDERS = [
    "neilpatel.com", "substack.com", "medium.com", "hubspot.com",
    "mailchimp.com", "sendgrid.net", "convertkit.com", "beehiiv.com",
    "noreply@", "no-reply@", "notifications@", "news@", "newsletter@",
    "digest@", "updates@", "marketing@", "promo@", "offers@",
    "newsletter.", "newsletters@", "mail.beehiiv.com",
    "mindstream.news", "newsletter.thepaypers.com", "arabianbusiness.com",
    "email.fintechfutures.com", "mail.theankler.com", "productschool.com",
    "workinpro.io",
]

# LinkedIn notification types that are NOT recruiter outreach
LINKEDIN_NOISE_SUBJECTS = [
    r'wants?\s*to\s*connect', r'accepted\s*your\s*invitation',
    r'endorsed\s*you', r'viewed\s*your\s*profile',
    r'anniversary', r'birthday', r'new\s*job', r'commented\s*on',
    r'liked\s*your', r'reacted\s*to', r'mentioned\s*you\s*in',
    r'trending\s*in\s*your\s*network', r'people\s*also\s*viewed',
    r'thought\s*leader\s*ad', r'take\s*it\s*to\s*the\s*next\s*level',
    r'promoted\s*post', r'sponsored',
]

# Automated job-board alerts are useful market signals, but not recruiter outreach
# and never interview/follow-up evidence on their own.
JOB_ALERT_DOMAINS = [
    "bayt.com", "naukrigulf.com", "gulftalent.com", "monstergulf.com",
    "foundit", "indeed.com", "glassdoor.com", "linkedin.com",
]

JOB_ALERT_PATTERNS = [
    r'\bjob\s*alert\b', r'\bnew\s+[\w\s-]{0,50}\s+jobs?\b',
    r'\bhot\s+job\s+opportunit', r'\bjob\s+opportunit.*waiting\s+for\s+you\b',
    r'\bcheck\s+out\s+jobs?\b', r'\bjobs?\s+applied\s+by\b',
    r'\bsimilar\s+jobs?\b', r'\bmatched\s+jobs?\b',
    r'\brecommended\s+jobs?\b', r'\bneeds\s+a\s+[\w\s/-]{2,80}\b',
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


def _normalize_key(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (text or '').lower())


def _keyword_tokens(text: str) -> list:
    return [t for t in re.findall(r'[a-z0-9]+', (text or '').lower()) if len(t) >= 4]


@lru_cache(maxsize=1)
def _get_active_pipeline_jobs():
    if not _pdb:
        return []
    jobs = []
    seen = set()
    try:
        for status in ACTIVE_PIPELINE_STATUSES:
            for job in _pdb.search(status=status, limit=500):
                job_id = job.get("job_id") or f"{job.get('company')}|{job.get('title')}|{status}"
                if job_id in seen:
                    continue
                seen.add(job_id)
                jobs.append(job)
    except Exception:
        return []
    return jobs


def _match_pipeline_company(subject: str, from_addr: str, body: str = ""):
    sender_name, sender_email = parseaddr(from_addr or "")
    sender_domain = extract_domain(sender_email or from_addr or "")
    subject_norm = _normalize_key(subject)
    body_norm = _normalize_key(body[:4000])
    sender_name_norm = _normalize_key(sender_name)
    sender_email_norm = (sender_email or "").strip().lower()
    sender_domain_norm = _normalize_key(sender_domain)

    best_company = None
    best_score = 0

    for job in _get_active_pipeline_jobs():
        company = job.get("company") or ""
        recruiter_name = job.get("recruiter_name") or ""
        recruiter_email = (job.get("recruiter_email") or "").strip().lower()
        recruiter_company = job.get("recruiter_company") or ""
        title = job.get("title") or ""

        company_norm = _normalize_key(company)
        recruiter_name_norm = _normalize_key(recruiter_name)
        recruiter_company_norm = _normalize_key(recruiter_company)
        title_norm = _normalize_key(title)

        score = 0
        if recruiter_email and recruiter_email == sender_email_norm:
            score += 10
        if recruiter_name_norm and recruiter_name_norm in sender_name_norm:
            score += 8
        if company_norm and company_norm in subject_norm:
            score += 8
        elif company_norm and company_norm in body_norm:
            score += 4
        if recruiter_company_norm and recruiter_company_norm in subject_norm:
            score += 6
        elif recruiter_company_norm and recruiter_company_norm in body_norm:
            score += 3
        if title_norm and title_norm in subject_norm:
            score += 3

        for token in _keyword_tokens(company) + _keyword_tokens(recruiter_company):
            if token and token in sender_domain_norm:
                score += 2
                break

        if score > best_score:
            best_company = company
            best_score = score

    if best_score >= 6:
        return best_company, best_score
    return None, 0


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


def is_job_alert(subject, from_addr, body=""):
    """Detect automated job-board alerts separately from recruiter outreach."""
    sender_email = parseaddr(from_addr or "")[1]
    domain = extract_domain(sender_email or from_addr)
    text = f"{subject} {body}".lower()

    domain_match = any(marker in domain for marker in JOB_ALERT_DOMAINS)
    pattern_match = matches_patterns(text, JOB_ALERT_PATTERNS)

    # LinkedIn marketing/notification emails are noise, not job alerts.
    if is_linkedin_noise(subject, from_addr):
        return False

    return domain_match and pattern_match


def has_interview_evidence(subject, from_addr, body=""):
    """Require body/sender-backed evidence before escalating an interview."""
    subject_text = subject or ""
    body_text = body or ""
    combined = f"{subject_text} {body_text}"
    sender_email = parseaddr(from_addr or "")[1]
    domain = extract_domain(sender_email or from_addr)

    if is_noise_sender(from_addr) or is_job_alert(subject, from_addr, body):
        return False

    if is_external_meeting_invite(subject, from_addr, body):
        return True

    # A subject with explicit interview language is acceptable from a real company
    # or recruiting domain, but not from generic automated job-alert senders.
    if matches_patterns(subject_text, STRICT_INTERVIEW_PATTERNS) and is_recruiter_domain(domain):
        return True

    return matches_patterns(combined, STRICT_INTERVIEW_PATTERNS) and has_hiring_context(subject, from_addr, body)


# Weighted keyword scoring (D5)
KEYWORD_WEIGHTS = {
    "interview": 3, "shortlisted": 3, "offer": 3, "congratulations": 3,
    "selected": 3, "phone screen": 3, "technical round": 3, "final round": 3,
    "next stage": 3, "next round": 3, "move forward": 3,
    "assessment": 2, "coding challenge": 2, "case study": 2,
    "application form": 3, "latest updated cv": 3, "updated cv": 3,
    "pre interview questionnaire": 3, "forms.office.com": 2,
    "availability": 2, "schedule": 2, "calendar link": 2,
    "deeper conversation": 2, "looking forward to your response": 2,
    "microsoft teams meeting": 2, "join with google meet": 2, "zoom meeting": 2,
    "meeting id": 1, "text/calendar": 2,
    "unfortunately": 1, "regret to inform": 1, "not moving forward": 1,
    "thank you for applying": 1, "application received": 1,
}
PIPELINE_MATCH_BONUS = 5
RECRUITER_DOMAIN_BONUS = 2
PRIORITY_THRESHOLDS = {"HIGH": 5, "MEDIUM": 2, "LOW": 0}
ACTIVE_PIPELINE_STATUSES = ("applied", "cv_built", "response", "interview", "offer")

HOT_KEYWORDS = [
    "interview", "shortlisted", "offer", "congratulations", "selected",
    "phone screen", "technical round", "final round", "assessment invite",
    "next steps in your application", "next stage", "next round",
    "move forward"
]


def score_email(subject, from_addr, body=""):
    """Weighted scoring for email priority (D5). Returns (score, pipeline_company)."""
    text = f"{subject} {body}".lower()
    score = 0
    pipeline_company = None

    if is_noise_sender(from_addr):
        return 0, None

    job_alert = is_job_alert(subject, from_addr, body)

    # Pipeline company match (D5 + D10)
    pipeline_company, pipeline_match_score = _match_pipeline_company(subject, from_addr, body)

    job_context = has_hiring_context(subject, from_addr, body, pipeline_company=pipeline_company)

    # Keyword weights only count when this actually looks job-related.
    if job_context:
        for kw, weight in KEYWORD_WEIGHTS.items():
            if kw in text:
                score += weight

    # Recruiter domain bonus
    sender_email = parseaddr(from_addr or "")[1]
    domain = extract_domain(sender_email or from_addr)
    if is_recruiter_domain(domain) and not job_alert:
        score += RECRUITER_DOMAIN_BONUS

    if job_context and is_external_meeting_invite(subject, from_addr, body):
        score += 4

    if pipeline_company and not job_alert:
        score += PIPELINE_MATCH_BONUS + min(3, pipeline_match_score // 4)

    if job_alert:
        score = min(score, PRIORITY_THRESHOLDS["MEDIUM"])
        pipeline_company = None

    return score, pipeline_company


def get_priority(score):
    """Convert score to priority level."""
    if score >= PRIORITY_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif score >= PRIORITY_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def is_hot_email(subject, from_addr, body="", categories=None, score=0):
    """Check if email should trigger immediate Telegram alert.

    Production callers pass precomputed categories/score. Tests and small
    scripts may call this helper directly, so derive them when omitted.
    """
    if is_noise_sender(from_addr) or is_job_alert(subject, from_addr, body):
        return False
    if categories is None:
        categories = categorize_email(subject, from_addr, body)
    if not score:
        score, _ = score_email(subject, from_addr, body)
    if "interview_invite" in categories or "assessment" in categories:
        return True
    if "follow_up_needed" in categories and score >= PRIORITY_THRESHOLDS["HIGH"]:
        return True
    subject_text = subject or ""
    if matches_patterns(subject_text, [r"\boffer\b"]) and has_hiring_context(subject, from_addr, body):
        return True
    return False


def has_hiring_context(subject, from_addr, body="", pipeline_company=None):
    """Require job/recruiting context before classifying sensitive email types."""
    if is_noise_sender(from_addr):
        return False

    if is_job_alert(subject, from_addr, body):
        return False

    sender_name, sender_email = parseaddr(from_addr or "")
    domain = extract_domain(sender_email or from_addr)
    if is_recruiter_domain(domain) and not is_linkedin_noise(subject, from_addr):
        return True

    sender_local = (sender_email.split('@', 1)[0] if sender_email and '@' in sender_email else sender_email or '').lower()
    sender_name_lower = (sender_name or '').lower()
    sender_context = f"{sender_local} {sender_name_lower}"
    if any(marker in sender_context for marker in HIRING_SENDER_MARKERS):
        return True

    if pipeline_company:
        return True

    text = f"{subject} {body}".lower()
    return matches_patterns(text, HIRING_CONTEXT_PATTERNS)


def categorize_email(subject, from_addr, body=""):
    categories = []
    text = f"{subject} {body}".lower()
    pipeline_company, _pipeline_score = _match_pipeline_company(subject, from_addr, body)
    hiring_context = has_hiring_context(subject, from_addr, body, pipeline_company=pipeline_company)
    
    # Skip noise senders entirely (newsletters, marketing, notifications)
    if is_noise_sender(from_addr):
        return ["other"]

    if is_job_alert(subject, from_addr, body):
        return ["job_alert"]
    
    domain = extract_domain(from_addr)

    if has_interview_evidence(subject, from_addr, body):
        categories.append("interview_invite")
    elif hiring_context and matches_patterns(text, INTERVIEW_PATTERNS) and (
        pipeline_company or is_recruiter_domain(domain)
    ):
        # Pipeline/recruiter messages about next stage / next round are actionable
        # even before a calendar invite appears. Keep this gated by hiring context
        # to avoid promoting newsletters or job-board alerts.
        categories.append("interview_invite")

    if is_recruiter_domain(domain) and not is_linkedin_noise(subject, from_addr):
        categories.append("recruiter_reach")
    
    if hiring_context and matches_patterns(text, APPLICATION_ACK_PATTERNS):
        categories.append("application_ack")

    if pipeline_company and "recruiter_reach" not in categories:
        categories.append("recruiter_reach")
    
    if hiring_context and matches_patterns(text, REJECTION_PATTERNS):
        categories.append("rejection")
    
    if hiring_context and matches_patterns(text, ASSESSMENT_PATTERNS):
        categories.append("assessment")

    if hiring_context and matches_patterns(text, APPLICATION_RESPONSE_PATTERNS):
        categories.append("application_response")
    
    if hiring_context and (re.search(r'\?\s*$', text) or matches_patterns(text, FOLLOW_UP_PATTERNS)):
        if "follow_up_needed" not in categories:
            categories.append("follow_up_needed")
    
    return categories if categories else ["other"]


def _strip_html(text):
    text = unescape(text or "")
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_external_meeting_invite(subject, from_addr, body=""):
    text = f"{subject} {body}".lower()
    sender_email = parseaddr(from_addr or "")[1]
    domain = extract_domain(sender_email or from_addr)
    if not domain:
        return False
    if domain in {"gmail.com", "googlemail.com"}:
        return False
    if is_noise_sender(from_addr):
        return False
    return matches_patterns(text, MEETING_INVITE_PATTERNS)


def get_email_body(msg):
    snippets = []
    calendar_detected = False

    if msg.is_multipart():
        for part in msg.walk():
            ctype = (part.get_content_type() or "").lower()
            charset = part.get_content_charset() or "utf-8"
            payload = part.get_payload(decode=True)
            filename = decode_str(part.get_filename() or "")
            disposition = (part.get("Content-Disposition") or "").lower()
            content_class = (part.get("Content-Class") or "").lower()

            if ctype == "text/plain" and payload:
                try:
                    snippets.append(payload.decode(charset, errors="replace"))
                except Exception:
                    pass
            elif ctype == "text/html" and payload:
                try:
                    snippets.append(_strip_html(payload.decode(charset, errors="replace")))
                except Exception:
                    pass
            elif ctype == "text/calendar":
                calendar_detected = True
                if payload:
                    try:
                        snippets.append(payload.decode(charset, errors="replace"))
                    except Exception:
                        pass

            if filename.lower().endswith('.ics') or 'attachment' in disposition and 'ics' in filename.lower():
                calendar_detected = True
            if 'calendarmessage' in content_class:
                calendar_detected = True
    else:
        charset = msg.get_content_charset() or "utf-8"
        payload = msg.get_payload(decode=True)
        ctype = (msg.get_content_type() or "").lower()
        if payload:
            try:
                decoded = payload.decode(charset, errors="replace")
                snippets.append(_strip_html(decoded) if ctype == "text/html" else decoded)
            except Exception:
                pass
        if ctype == "text/calendar":
            calendar_detected = True

    if calendar_detected:
        snippets.append("text/calendar calendar invite meeting invite")

    body = "\n".join(s for s in snippets if s)
    body = re.sub(r'\s+', ' ', body).strip()
    return body[:4000]



def load_feedback_rules():
    """Load lightweight feedback labels for future local scoring."""
    rules = {"wrong_alert_senders": set(), "important_senders": set(), "wrong_alert_subjects": set()}
    if not FEEDBACK_PATH.exists():
        return rules
    try:
        with open(FEEDBACK_PATH) as f:
            for line in f:
                if not line.strip():
                    continue
                item = json_module.loads(line)
                label = (item.get("label") or "").lower()
                sender = (item.get("from") or item.get("sender") or "").lower()
                subject = (item.get("subject") or "").lower()
                if label in {"wrong_alert", "not_job", "noise"}:
                    if sender:
                        rules["wrong_alert_senders"].add(sender)
                    if subject:
                        rules["wrong_alert_subjects"].add(subject[:80])
                elif label in {"important", "missed", "critical"} and sender:
                    rules["important_senders"].add(sender)
    except Exception:
        pass
    return rules


def _confidence_label(score: int) -> str:
    if score >= 85:
        return "high"
    if score >= 60:
        return "medium"
    if score >= 35:
        return "low"
    return "very_low"


def assess_actionability(subject, from_addr, body, categories, score, pipeline_company):
    """Return confidence, evidence, and rationale for the classification."""
    categories = categories or []
    evidence = []
    confidence = 10
    text = f"{subject} {body}".lower()
    sender_l = (from_addr or "").lower()

    if categories == ["other"] or "other" in categories:
        confidence = 5
        evidence.append("classified as other/noise")
    if "job_alert" in categories:
        confidence = max(confidence, 25)
        evidence.append("automated job alert")
    if pipeline_company:
        confidence += 25
        evidence.append(f"matched active pipeline company: {pipeline_company}")
    if is_recruiter_domain(extract_domain(from_addr)):
        confidence += 20
        evidence.append("known recruiter/job domain")
    sender_context = sender_l
    if any(marker in sender_context for marker in HIRING_SENDER_MARKERS):
        confidence += 15
        evidence.append("hiring sender context")
    if has_hiring_context(subject, from_addr, body, pipeline_company):
        confidence += 10
        evidence.append("hiring/application context")
    if has_interview_evidence(subject, from_addr, body):
        confidence += 45
        evidence.append("calendar or explicit interview evidence")
    elif matches_patterns(text, STRICT_INTERVIEW_PATTERNS) and has_hiring_context(subject, from_addr, body, pipeline_company):
        confidence += 35
        evidence.append("explicit interview wording with hiring context")
    if "assessment" in categories:
        confidence += 25
        evidence.append("assessment keyword with hiring context")
    if "application_response" in categories:
        confidence += 35
        evidence.append("application form/CV request with hiring context")
    if "follow_up_needed" in categories:
        confidence += 20
        evidence.append("reply/follow-up wording with hiring context")
    if "recruiter_reach" in categories:
        confidence += 20
        evidence.append("recruiter outreach classification")
    if score >= PRIORITY_THRESHOLDS["HIGH"]:
        confidence += 10
        evidence.append(f"high priority score: {score}")
    elif score >= PRIORITY_THRESHOLDS["MEDIUM"]:
        confidence += 5
        evidence.append(f"medium priority score: {score}")

    if is_noise_sender(from_addr) or is_linkedin_noise(subject, from_addr) or is_job_alert(subject, from_addr, body):
        confidence = min(confidence, 25)
        evidence.append("noise/job-alert guard applied")

    rules = load_feedback_rules()
    if any(sender_l and marker in sender_l for marker in rules["wrong_alert_senders"]):
        confidence = min(confidence, 20)
        evidence.append("Ahmed feedback: sender previously marked wrong/noise")
    if any((subject or "").lower().startswith(marker) for marker in rules["wrong_alert_subjects"]):
        confidence = min(confidence, 20)
        evidence.append("Ahmed feedback: subject previously marked wrong/noise")
    if any(sender_l and marker in sender_l for marker in rules["important_senders"]):
        confidence = max(confidence, 80)
        evidence.append("Ahmed feedback: sender previously marked important")

    confidence = max(0, min(100, confidence))
    actionable_categories = {"interview_invite", "assessment", "application_response", "follow_up_needed", "recruiter_reach"}
    actionable = bool(actionable_categories.intersection(categories)) and confidence >= MIN_ACTIONABLE_CONFIDENCE
    why = " | ".join(evidence[:4]) if evidence else "no strong hiring evidence"
    return {
        "confidence": confidence,
        "confidence_label": _confidence_label(confidence),
        "evidence": evidence[:8],
        "why_actionable": why if actionable else f"not actionable: {why}",
        "actionable": actionable,
    }


def update_pipeline_from_emails(categorized):
    """Create review-gated pipeline candidates from email findings.

    This intentionally does not update Notion or the local pipeline DB. Email
    classification is useful signal, but stage changes such as rejection or
    interview must stay human-reviewable unless a separate approved workflow
    confirms them from the full email body.
    """
    review_categories = {
        "rejection": "possible_rejection",
        "interview_invite": "possible_interview",
        "assessment": "possible_assessment",
        "application_response": "possible_application_response",
        "follow_up_needed": "possible_follow_up",
        "recruiter_reach": "possible_recruiter_outreach",
    }
    updates = []
    seen = set()
    for category, review_type in review_categories.items():
        for email_item in categorized.get(category, []):
            subject = email_item.get("subject", "")
            from_addr = email_item.get("from", "")
            key = (str(email_item.get("id") or ""), subject, from_addr, review_type)
            if key in seen:
                continue
            seen.add(key)
            entry = {
                "timestamp": now_iso(),
                "review_type": review_type,
                "category": category,
                "email_id": str(email_item.get("id") or ""),
                "subject": subject[:200],
                "from": from_addr[:200],
                "priority": email_item.get("priority") or email_item.get("urgency") or "",
                "pipeline_match": email_item.get("pipeline_match"),
                "status": "needs_human_review",
            }
            updates.append(entry)

    if updates and not common.is_dry_run():
        PIPELINE_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PIPELINE_REVIEW_PATH, "a") as f:
            for entry in updates:
                f.write(json_module.dumps(entry, default=str) + "\n")
        print(f"  Pipeline review: {len(updates)} candidate(s) queued, no auto-update performed")
    return updates

def safe_body_excerpt(body: str, limit: int = 1200) -> str:
    """Return a compact body excerpt for classification evidence, not full email storage."""
    body = re.sub(r"\s+", " ", body or "").strip()
    if len(body) <= limit:
        return body
    return body[: limit - 1].rstrip() + "…"


def build_llm_prompt(summary, total_emails, actionable_emails):
    """Build the XML-structured LLM prompt with email data."""
    # Send actionable emails as a focused list with enough body evidence to avoid subject-only escalation.
    actionable_list = []
    for e in actionable_emails:
        actionable_list.append({
            "id": e.get("id", ""),
            "subject": e.get("subject", ""),
            "from": e.get("from", ""),
            "date": e.get("date", ""),
            "categories": e.get("categories", []),
            "unread": e.get("unread", False),
            "classification_evidence": {
                "priority": e.get("priority", ""),
                "priority_score": e.get("priority_score", 0),
                "pipeline_match": e.get("pipeline_match"),
                "confidence": e.get("confidence"),
                "confidence_label": e.get("confidence_label"),
                "evidence": e.get("evidence", []),
                "why_actionable": e.get("why_actionable", ""),
            },
            "body_excerpt": e.get("body_excerpt", ""),
        })
    emails_json = json_module.dumps({"actionable": actionable_list}, indent=2, default=str)
    categories = summary.get("by_category", {})
    prompt = LLM_EMAIL_ANALYSIS_PROMPT.format(
        categories=json_module.dumps(categories, default=str),
        total_emails=total_emails,
        actionable_count=len(actionable_emails)
    )
    return prompt, emails_json


def _resolve_secret_ref(value):
    """Resolve the local SecretRef shape used by OpenClaw config."""
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ""
    ref_id = value.get("id") or ""
    if not ref_id.startswith("/"):
        return ""
    try:
        secrets_path = Path(os.path.expanduser("~/.openclaw/config/secrets.json"))
        secrets = json_module.load(open(secrets_path))
        cursor = secrets
        for part in [p for p in ref_id.split("/") if p]:
            cursor = cursor[part]
        return cursor if isinstance(cursor, str) else ""
    except Exception:
        return ""


def run_llm_analysis(summary, total_emails, actionable_emails) -> dict:
    """Send actionable emails to LLM with XML-structured prompt. Returns parsed JSON."""
    import os, json as json_lib

    if not actionable_emails:
        return {
            "actionable_emails": [],
            "summary": {
                "total_actionable": 0,
                "critical_count": 0,
                "requires_interview_prep": False,
                "requires_assessment": False,
                "recruiter_top_opportunities": [],
                "top_priority": None,
                "daily_focus": "No email action needed from this batch.",
            },
        }

    prompt, emails_json = build_llm_prompt(summary, total_emails, actionable_emails)

    # Load OpenClaw gateway token from config, resolving SecretRefs when present.
    gw_token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")
    gw_url = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
    if not gw_token:
        try:
            with open(os.path.expanduser("~/.openclaw/openclaw.json")) as f:
                cfg = json_lib.load(f)
                gw_token = _resolve_secret_ref(cfg.get("gateway", {}).get("auth", {}).get("token", ""))
        except Exception:
            pass

    body = {
        "model": "openclaw",
        "max_tokens": 1024,
        "temperature": LLM_TEMP,
        "messages": [
            {"role": "system", "content": "You are an elite executive assistant. Analyze emails with precision and strategic awareness. Respond ONLY with valid JSON matching the specified schema."},
            {"role": "user", "content": f"{prompt}\n\n--- EMAIL DATA ---\n{emails_json}"}
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "x-openclaw-model": LLM_MODEL,
    }

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
            print(f"  LLM: gateway returned {resp.status_code} {resp.reason}: {resp.text[:500]}")
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
            if not common.is_dry_run():
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
    # Process the oldest pending UIDs first so downtime backlogs are drained
    # across runs without skipping unprocessed messages.
    recent_uids = all_uids[:MAX_UID_BATCH]
    backlog = max(0, len(all_uids) - len(recent_uids))
    suffix = f", backlog remaining {backlog}" if backlog else ""
    print(f"  IMAP: {len(all_uids)} new UIDs since {last_uid} (processing {len(recent_uids)}{suffix})")

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

    # Defer UID checkpoint until agent_main has written the final summary.
    # This prevents a mid-run crash from marking emails as processed before
    # the user-visible report and review artifacts exist.
    global _PENDING_STATE_UPDATE
    _PENDING_STATE_UPDATE = {
        "state": state,
        "last_uid": last_uid,
        "max_uid_seen": max_uid_seen,
        "processed_count": len(emails),
    }
    if common.is_dry_run():
        print("  DRY RUN: not updating email UID state")

    return emails


def _commit_pending_state():
    """Persist the deferred UID checkpoint after successful output write."""
    global _PENDING_STATE_UPDATE
    pending = _PENDING_STATE_UPDATE
    if not pending or common.is_dry_run():
        return
    state = dict(pending.get("state") or {})
    last_uid = int(pending.get("last_uid") or 0)
    max_uid_seen = int(pending.get("max_uid_seen") or last_uid)
    if max_uid_seen > last_uid:
        state["last_seen_uid"] = max_uid_seen
    state["last_success"] = now_iso()
    state["processed_count"] = state.get("processed_count", 0) + int(pending.get("processed_count") or 0)
    _save_state(state)
    _PENDING_STATE_UPDATE = None


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
        "application_response": [],
        "follow_up_needed": [],
        "job_alert": [],
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
        email_data["body_excerpt"] = safe_body_excerpt(body)
        score, pipeline_company = score_email(email_data["subject"], email_data["from"], body)
        email_data["priority_score"] = score
        email_data["priority"] = get_priority(score)
        email_data["pipeline_match"] = pipeline_company
        assessment = assess_actionability(email_data["subject"], email_data["from"], body, categories, score, pipeline_company)
        email_data.update(assessment)

        email_summary = {
            "id": email_data["id"],
            "from": email_data["from"],
            "subject": email_data["subject"],
            "date": email_data.get("date", ""),
            "unread": email_data.get("unread", False),
            "priority": email_data["priority"],
            "score": score,
            "pipeline_match": pipeline_company,
            "confidence": email_data.get("confidence"),
            "confidence_label": email_data.get("confidence_label"),
            "evidence": email_data.get("evidence", []),
            "why_actionable": email_data.get("why_actionable", ""),
        }

        for cat in categories:
            if cat in categorized:
                categorized[cat].append(email_summary)

        if email_data.get("actionable"):
            actionable_emails.append(email_data)
            if email_data.get("unread"):
                unread_actionable += 1

        if email_data.get("actionable") and "interview_invite" in categories:
            interviews_detected += 1
        if email_data.get("actionable") and "recruiter_reach" in categories:
            recruiter_messages += 1

        # D7: append to history
        if not common.is_dry_run():
            _append_history(email_data, categories, score, pipeline_company)

        # D10: emit pipeline signal only for confident job-process categories.
        if pipeline_company and not common.is_dry_run() and email_data.get("actionable") and email_data.get("confidence", 0) >= MIN_SIGNAL_CONFIDENCE:
            sig = _emit_signal(email_data, pipeline_company, categories, score)
            signals.append(sig)

        # D8: hot alert (integrated, no separate cron needed)
        if email_data.get("confidence", 0) >= MIN_HOT_CONFIDENCE and is_hot_email(email_data["subject"], email_data["from"], body, categories, score):
            hot_alerts.append({
                "id": email_data["id"],
                "subject": email_data["subject"],
                "from": email_data["from"],
                "priority": email_data["priority"],
                "pipeline_match": pipeline_company,
                "confidence": email_data.get("confidence"),
                "evidence": email_data.get("evidence", []),
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
        "application_responses": categorized["application_response"][:10],
        "follow_ups_needed": categorized["follow_up_needed"][:5],
        "job_alerts": categorized["job_alert"][:10],
        "actionable_count": len(actionable_emails),
        "hot_alerts": hot_alerts,
        "signals": signals,
    }

    # ======================================================================
    # PIPELINE INTEGRATION — review-gated candidates only, no auto stage writes
    # ======================================================================
    if common.is_dry_run():
        print("  DRY RUN: not writing pipeline review candidates")
    else:
        pipeline_updates = update_pipeline_from_emails(categorized)
        if pipeline_updates:
            summary["pipeline_review_candidates"] = pipeline_updates

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

    # D4: Write shared snapshot only after classification, pipeline review, and
    # LLM analysis are complete, so formatter/briefing consumers see one coherent result.
    if common.is_dry_run():
        print("  DRY RUN: not writing email-latest.json")
    else:
        LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        json_module.dump(summary, open(LATEST_PATH, "w"), indent=2)

    result.set_data(summary)
    result.post_write_hook = _commit_pending_state
    
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
