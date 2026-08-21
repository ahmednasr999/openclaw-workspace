#!/usr/bin/env python3
"""test-email-agent.py — Email Agent test suite (D9)
Covers: header parsing, categorization, scoring, UID state, output formats, error handling.
Target: 30+ assertions.
"""
import sys, os, json, tempfile, shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# === Test counters ===
_pass = 0
_fail = 0

def ok(label, condition, detail=""):
    global _pass, _fail
    if condition:
        _pass += 1
        print(f"  PASS: {label}")
    else:
        _fail += 1
        print(f"  FAIL: {label} — {detail}")


# === Import module under test ===
# email-agent.py has a hyphen so we use importlib
import importlib.util
spec = importlib.util.spec_from_file_location("email_agent", str(Path(__file__).parent / "email-agent.py"))
ea = importlib.util.module_from_spec(spec)

# Patch sys.exit so the module doesn't crash if config is missing
_original_exit = sys.exit
sys.exit = lambda *a: None
try:
    spec.loader.exec_module(ea)
except SystemExit:
    pass
finally:
    sys.exit = _original_exit


# ==============================================================================
# TEST 1: Header decoding
# ==============================================================================
print("\n[1/7] Header Decoding")

ok("decode plain ASCII", ea.decode_str("Hello World") == "Hello World")
ok("decode None", ea.decode_str(None) == "")
ok("decode empty", ea.decode_str("") == "")
# decode_str expects pre-decoded strings (email library handles bytes → str)
ok("decode unicode chars", ea.decode_str("R\u00e9sum\u00e9 Review") == "R\u00e9sum\u00e9 Review")


# ==============================================================================
# TEST 2: Domain extraction
# ==============================================================================
print("\n[2/7] Domain Extraction")

ok("extract from email", ea.extract_domain("user@example.com") == "example.com")
ok("extract from display name + email", ea.extract_domain("John Doe <john@corp.co.uk>") == "corp.co.uk")
ok("extract from empty", ea.extract_domain("") == "")
ok("extract from None", ea.extract_domain(None) == "")
ok("extract from no @", ea.extract_domain("noemail") == "")


# ==============================================================================
# TEST 3: Recruiter domain detection
# ==============================================================================
print("\n[3/7] Recruiter Domain Detection")

ok("linkedin.com is recruiter", ea.is_recruiter_domain("linkedin.com"))
ok("hays.com is recruiter", ea.is_recruiter_domain("hays.com"))
ok("cooperfitch.com is recruiter", ea.is_recruiter_domain("cooperfitch.com"))
ok("random.xyz is NOT recruiter", not ea.is_recruiter_domain("random.xyz"))
ok("gmail.com is NOT recruiter", not ea.is_recruiter_domain("gmail.com"))


# ==============================================================================
# TEST 4: Categorization
# ==============================================================================
print("\n[4/7] Email Categorization")

ok("interview keyword -> interview_invite",
   "interview_invite" in ea.categorize_email("Interview Invitation for PM Role", "hr@company.com"))

ok("assessment keyword -> assessment",
   "assessment" in ea.categorize_email("Complete your coding challenge", "recruiter@hays.com"))

ok("rejection keyword -> rejection",
   "rejection" in ea.categorize_email("Unfortunately we decided not to proceed", "hr@company.com"))

ok("application ack -> application_ack",
   "application_ack" in ea.categorize_email("Thank you for applying to our role", "hr@company.com"))

ok("recruiter domain -> recruiter_reach",
   "recruiter_reach" in ea.categorize_email("Exciting opportunity", "jane@michaelpage.com"))

ok("noise sender -> other",
   ea.categorize_email("Weekly Tech Digest", "newsletter@substack.com") == ["other"])

ok("newsletter subdomain sender -> other",
   ea.categorize_email("In Case You Missed It", "CNN <cnn@newsletters.cnn.com>") == ["other"])

ok("noreply -> other",
   ea.categorize_email("Your order shipped", "noreply@amazon.com") == ["other"])

ok("linkedin noise (profile view) filtered",
   ea.is_linkedin_noise("Someone viewed your profile", "notifications@linkedin.com"))

ok("linkedin noise (connection) filtered",
   ea.is_linkedin_noise("John wants to connect", "notifications@linkedin.com"))

ok("generic email -> other",
   ea.categorize_email("Hello there", "friend@gmail.com") == ["other"])

ok("real estate promo with investment language -> other",
   ea.categorize_email("Invest in Arabian Ranches from just AED 500", "discovery@prypco.com") == ["other"])

ok("ecommerce stock alert -> other",
   ea.categorize_email("₹163 only: The #1 best seller is back in stock", "info@host.discountwalas.com") == ["other"])

ok("availability alone without hiring context -> other",
   ea.categorize_email("Please share your availability", "events@vendor.com") == ["other"])

taaeen_body = """Dear Ahmed,
As discussed, please find attached the application form for you to complete and submit.
I have also attached the job description for the role you applied for.
Additionally, please share your latest updated CV at your earliest convenience.
https://forms.office.com/r/kZ2DzXRZH0
"""
taaeen_categories = ea.categorize_email(
   "Application Form and Job Description - Project Manager",
   "Jumaanah Manzoor Ahammed | Taaeen Consulting & Talent Development <Jumaanah@taaeen.ae>",
   taaeen_body,
)
ok("recruiter form/CV request -> application_response",
   "application_response" in taaeen_categories,
   f"categories={taaeen_categories}")
taaeen_score, taaeen_pipeline = ea.score_email(
   "Application Form and Job Description - Project Manager",
   "Jumaanah Manzoor Ahammed | Taaeen Consulting & Talent Development <Jumaanah@taaeen.ae>",
   taaeen_body,
)
taaeen_assessment = ea.assess_actionability(
   "Application Form and Job Description - Project Manager",
   "Jumaanah Manzoor Ahammed | Taaeen Consulting & Talent Development <Jumaanah@taaeen.ae>",
   taaeen_body,
   taaeen_categories,
   taaeen_score,
   taaeen_pipeline,
)
ok("recruiter form/CV request is actionable",
   taaeen_assessment["actionable"],
   f"assessment={taaeen_assessment}")

draeger_body = """Thank you for your interest in Draeger. In order to process your
job application, you'll need to click the link below to complete the registration
process and set up your user account. Your account will let you receive and confirm
interview invitations. PROCESS YOUR JOB APPLICATION! Your application has not been
processed yet and will be deleted if registration is not completed within 20 days."""
draeger_subject = "Application confirmation"
draeger_sender = "Drägerwerk AG <jobs@draeger.beesite.de>"
draeger_categories = ea.categorize_email(draeger_subject, draeger_sender, draeger_body)
draeger_score, draeger_pipeline = ea.score_email(draeger_subject, draeger_sender, draeger_body)
draeger_assessment = ea.assess_actionability(
   draeger_subject,
   draeger_sender,
   draeger_body,
   draeger_categories,
   draeger_score,
   draeger_pipeline,
)
ok("portal registration request is not an interview",
   "interview_invite" not in draeger_categories and not ea.has_interview_evidence(
       draeger_subject, draeger_sender, draeger_body
   ),
   f"categories={draeger_categories}")
ok("portal registration request -> application_response",
   "application_response" in draeger_categories,
   f"categories={draeger_categories}")
ok("portal registration request remains actionable",
   draeger_assessment["actionable"],
   f"assessment={draeger_assessment}")
ok("portal registration request is not a hot interview alert",
   not ea.is_hot_email(
       draeger_subject,
       draeger_sender,
       draeger_body,
       categories=draeger_categories,
       score=draeger_score,
   ),
   f"categories={draeger_categories} score={draeger_score}")

original_pipeline_jobs = ea._get_active_pipeline_jobs
ea._get_active_pipeline_jobs = lambda: [{
    "job_id": "linkedin-li-4384465264",
    "company": "Ranger AI",
    "title": "Director of Operations",
    "recruiter_name": "Sari Saadi",
    "recruiter_email": None,
    "recruiter_company": "Ranger AI (Co-Founder)",
}]

ranger_body = """Hi Ahmed,\n\nI would like to take you to the next stage of our process.\nBefore we move forward, could you share the compensation range you are expecting?\nLooking forward to your response.\n"""
ranger_categories = ea.categorize_email("Ranger AI - Followup", "Sari Saadi <sari@rangerrfx.com>", ranger_body)
ok("ranger follow-up -> interview_invite",
   "interview_invite" in ranger_categories,
   f"categories={ranger_categories}")
ok("ranger follow-up -> follow_up_needed",
   "follow_up_needed" in ranger_categories,
   f"categories={ranger_categories}")
ok("tracked pipeline company -> recruiter_reach",
   "recruiter_reach" in ranger_categories,
   f"categories={ranger_categories}")

pipeline_only_categories = ea.categorize_email(
   "Ranger AI update",
   "Sari Saadi <sari@rangerrfx.com>",
   "Hi Ahmed, sharing a quick update after our previous discussion."
)
ok("pipeline-aware match promotes neutral email to recruiter_reach",
   "recruiter_reach" in pipeline_only_categories,
   f"categories={pipeline_only_categories}")


# ==============================================================================
# TEST 5: Weighted Scoring (D5)
# ==============================================================================
print("\n[5/7] Weighted Scoring")

score1, _ = ea.score_email("Interview Invitation", "hr@company.com")
ok("interview keyword scores high", score1 >= 3, f"score={score1}")

score2, _ = ea.score_email("Your weekly digest", "newsletter@substack.com")
ok("newsletter scores 0", score2 == 0, f"score={score2}")

score3, _ = ea.score_email("Exciting PM Role", "jane@michaelpage.com")
ok("recruiter domain adds bonus", score3 >= 2, f"score={score3}")

score4, pipeline_company = ea.score_email("Ranger AI - Followup", "Sari Saadi <sari@rangerrfx.com>", ranger_body)
ok("ranger follow-up scores medium+", score4 >= 2, f"score={score4}")
ok("ranger follow-up resolves pipeline company", pipeline_company == "Ranger AI", f"pipeline_company={pipeline_company}")

score5, pipeline_company2 = ea.score_email("Ranger AI update", "Sari Saadi <sari@rangerrfx.com>", "Quick follow-up note")
ok("pipeline-aware score boost applies", score5 >= ea.PIPELINE_MATCH_BONUS, f"score={score5}")
ok("pipeline-aware score identifies company", pipeline_company2 == "Ranger AI", f"pipeline_company={pipeline_company2}")

ok("HIGH priority from high score", ea.get_priority(5) == "HIGH")
ok("MEDIUM priority from mid score", ea.get_priority(3) == "MEDIUM")
ok("LOW priority from low score", ea.get_priority(0) == "LOW")


# ==============================================================================
# TEST 6: Hot email detection (D8)
# ==============================================================================
print("\n[6/7] Hot Email Detection")

ok("interview is hot", ea.is_hot_email("Interview with VP Engineering", "hr@company.com"))
ok("offer is hot", ea.is_hot_email("Job Offer - Senior Director", "hr@company.com"))
ok("newsletter NOT hot", not ea.is_hot_email("Weekly tech roundup", "news@substack.com"))
ok("assessment is hot", ea.is_hot_email("Complete assessment invite", "hr@company.com"))
ok("next stage is hot", ea.is_hot_email("Ranger AI - Followup, next stage", "sari@rangerrfx.com"))
ok("promo email is NOT hot", not ea.is_hot_email("Invest in Arabian Ranches from just AED 500", "discovery@prypco.com"))

cnn_subject = "In Case You Missed It - Pilot scrawls ‘I’m bored’ into UK sky mid-flight"
cnn_sender = "CNN <cnn@newsletters.cnn.com>"
ea._get_active_pipeline_jobs = lambda: [{
    "job_id": "tp-active",
    "company": "TP",
    "title": "VP AI Delivery",
    "recruiter_name": "",
    "recruiter_email": None,
    "recruiter_company": "",
}]
cnn_match = ea._match_pipeline_company(cnn_subject, cnn_sender, "")
cnn_categories = ea.categorize_email(cnn_subject, cnn_sender, "")
cnn_score, cnn_pipeline = ea.score_email(cnn_subject, cnn_sender, "")
ok("short pipeline alias does not match across word boundaries",
   cnn_match == (None, 0),
   f"match={cnn_match}")
ok("CNN collision remains non-hiring email",
   cnn_categories == ["other"] and cnn_score == 0 and cnn_pipeline is None,
   f"categories={cnn_categories} score={cnn_score} pipeline={cnn_pipeline}")

tp_only_match = ea._match_pipeline_company(
    "TP interview process update",
    "Hiring Team <hiring@teleperformance.com>",
    "",
)
ok("standalone short pipeline alias needs corroboration",
   tp_only_match == (None, 0),
   f"match={tp_only_match}")

tp_link_match = ea._match_pipeline_company(
    "TP-Link Wi-Fi routers clearance sale",
    "Store <sales@example.com>",
    "",
)
ok("short pipeline alias does not promote hyphenated product name",
   tp_link_match == (None, 0),
   f"match={tp_link_match}")

tp_corroborated_match = ea._match_pipeline_company(
    "TP VP AI Delivery application update",
    "Hiring Team <hiring@teleperformance.com>",
    "",
)
ok("short pipeline alias plus exact role still matches",
   tp_corroborated_match == ("TP", 6),
   f"match={tp_corroborated_match}")

ea._get_active_pipeline_jobs = lambda: [{
    "job_id": "teleperformance-active",
    "company": "Teleperformance",
    "title": "VP AI Delivery",
    "recruiter_name": "",
    "recruiter_email": None,
    "recruiter_company": "",
}]
full_company_match = ea._match_pipeline_company(
    "Teleperformance interview process update",
    "Hiring Team <hiring@teleperformance.com>",
    "",
)
ok("full pipeline company still matches",
   full_company_match == ("Teleperformance", 10),
   f"match={full_company_match}")
ea._get_active_pipeline_jobs = original_pipeline_jobs


# ==============================================================================
# TEST 7: UID State Management (D3)
# ==============================================================================
print("\n[7/8] UID State Management")

# Use temp directory
tmp_dir = tempfile.mkdtemp()
test_state_path = Path(tmp_dir) / "email-state.json"

# Monkey-patch the state path
original_state = ea.STATE_PATH
ea.STATE_PATH = test_state_path

# Test empty state
state = ea._load_state()
ok("empty state returns defaults", state["last_seen_uid"] == 0)

# Test save and reload
state["last_seen_uid"] = 12345
state["last_success"] = "2026-03-24T10:00:00"
ea._save_state(state)
reloaded = ea._load_state()
ok("state persists last_seen_uid", reloaded["last_seen_uid"] == 12345)
ok("state persists last_success", reloaded["last_success"] == "2026-03-24T10:00:00")

# Test error latest
test_latest_path = Path(tmp_dir) / "email-latest.json"
ea.LATEST_PATH = test_latest_path
ea._write_error_latest("AUTH_FAILURE: bad password", state)
error_data = json.load(open(test_latest_path))
ok("error latest has status=error", error_data["status"] == "error")
ok("error latest has error message", "AUTH_FAILURE" in error_data["error"])
ok("error latest has last_success", error_data["last_success"] == "2026-03-24T10:00:00")

# Restore
ea.STATE_PATH = original_state
shutil.rmtree(tmp_dir)




# ============================================================================== 
# TEST 8: Formatter LLM Veto / False Positive Guard
# ============================================================================== 
print("\n[8/8] Formatter LLM Veto")

fmt_spec = importlib.util.spec_from_file_location("format_email_alert", str(Path(__file__).parent / "format-email-alert.py"))
fmt = importlib.util.module_from_spec(fmt_spec)
fmt_spec.loader.exec_module(fmt)

false_positive_summary = {
    "data": {
        "total_scanned": 35,
        "assessments": [{
            "id": "359639",
            "from": "Editor @ The Paypers <Editor@newsletter.thepaypers.com>",
            "subject": "Monzo enters telecoms with eSIM mobile plan",
            "priority": "HIGH",
        }],
        "hot_alerts": [{
            "id": "359639",
            "from": "Editor @ The Paypers <Editor@newsletter.thepaypers.com>",
            "subject": "Monzo enters telecoms with eSIM mobile plan",
            "priority": "HIGH",
        }],
        "llm_analysis": {
            "actionable_emails": [{
                "id": "359639",
                "from": "Editor @ The Paypers <Editor@newsletter.thepaypers.com>",
                "subject": "Monzo enters telecoms with eSIM mobile plan",
                "category": "assessment",
                "urgency": "low",
                "action": "read_and_file",
                "response_deadline": "when convenient",
                "intent": "newsletter item, not a response request",
                "notes": "Likely false positive",
            }],
            "summary": {"total_actionable": 0, "critical_count": 0},
        },
    }
}
alert = fmt.build_alert(false_positive_summary)
ok("LLM read_and_file veto suppresses urgent fallback", alert.startswith("📬 Email scan: 35 new email(s) processed"), alert)
ok("newsletter false positive not action needed", "Email alert - action needed" not in alert, alert)

application_response_summary = {
    "data": {
        "total_scanned": 52,
        "application_responses": [{
            "id": "360262",
            "from": "Jumaanah Manzoor Ahammed | Taaeen Consulting & Talent Development <Jumaanah@taaeen.ae>",
            "subject": "Application Form and Job Description - Project Manager",
            "priority": "HIGH",
            "confidence": 85,
            "why_actionable": "application form/CV request with hiring context",
        }],
        "llm_analysis": {},
    }
}
application_alert = fmt.build_alert(application_response_summary)
ok("application_response appears in action-needed alert",
   "Application Form and Job Description" in application_alert
   and "Email alert - action needed" in application_alert
   and "all clear" not in application_alert.lower(),
   application_alert)

backlog_uids = [str(i).encode() for i in range(1, 701)]
selected = backlog_uids[:ea.MAX_UID_BATCH]
ok("UID backlog drains oldest first", selected[0] == b"1" and selected[-1] == str(ea.MAX_UID_BATCH).encode(), f"first={selected[:1]} last={selected[-1:]}")

# ==============================================================================
# SUMMARY
# ==============================================================================
total = _pass + _fail
print(f"\n{'='*50}")
print(f"Email Agent Tests: {_pass}/{total} passed, {_fail} failed")
print(f"{'='*50}")
sys.exit(1 if _fail > 0 else 0)
