#!/usr/bin/env python3
"""Synthetic regression harness for the Gmail email agent.

Runs fixture emails through the same local classifier used by production, plus
formatter regressions for known false-positive patterns. No Gmail connection and
no file writes outside temporary fixture data.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_PATH = ROOT / "scripts" / "email-agent.py"
FORMATTER_PATH = ROOT / "scripts" / "format-email-alert.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


ea = load_module("email_agent_under_test", AGENT_PATH)
fmt = load_module("format_email_alert_under_test", FORMATTER_PATH)

EXPECTED_LLM_MODEL = "openai/gpt-5.6-sol"

FIXTURES = [
    {
        "name": "explicit interview invite",
        "from": "Recruiter <recruiter@hays.com>",
        "subject": "Interview invitation for Program Director role",
        "body": "We would like to schedule an interview for your application. Please choose a time.",
        "expect_actionable": True,
        "expect_categories": {"interview_invite", "recruiter_reach"},
        "min_confidence": 75,
    },
    {
        "name": "recruiter screen",
        "from": "Talent Acquisition <talent@kornferry.com>",
        "subject": "Leadership role discussion",
        "body": "We are hiring for a transformation leadership role and would like to discuss fit.",
        "expect_actionable": True,
        "expect_categories": {"recruiter_reach"},
        "min_confidence": 55,
    },
    {
        "name": "application rejection",
        "from": "Careers <careers@examplehealth.com>",
        "subject": "Update on your application for VP Digital Transformation",
        "body": "Unfortunately, we will not be moving forward with your application.",
        "expect_actionable": False,
        "expect_categories": {"rejection"},
        "max_confidence": 80,
    },
    {
        "name": "assessment invite",
        "from": "HR <hr@healthcarecorp.com>",
        "subject": "Assessment for your application",
        "body": "Please complete the case study assessment before the deadline.",
        "expect_actionable": True,
        "expect_categories": {"assessment"},
        "min_confidence": 55,
    },
    {
        "name": "newsletter false positive",
        "from": "Editor @ The Paypers <Editor@newsletter.thepaypers.com>",
        "subject": "Monzo enters telecoms with eSIM mobile plan",
        "body": "Daily Banking newsletter with market updates and no request for action.",
        "expect_actionable": False,
        "expect_categories": {"other"},
        "max_confidence": 30,
    },
]


def check_fixture(fx: dict, *, verbose: bool = False) -> list[str]:
    errors: list[str] = []
    cats = set(ea.categorize_email(fx["subject"], fx["from"], fx["body"]))
    score, pipeline = ea.score_email(fx["subject"], fx["from"], fx["body"])
    assessment = ea.assess_actionability(fx["subject"], fx["from"], fx["body"], list(cats), score, pipeline)
    missing = fx.get("expect_categories", set()) - cats
    if missing:
        errors.append(f"{fx['name']}: missing categories {sorted(missing)}, got {sorted(cats)}")
    if bool(assessment["actionable"]) != bool(fx["expect_actionable"]):
        errors.append(f"{fx['name']}: actionable={assessment['actionable']} expected {fx['expect_actionable']}")
    if "min_confidence" in fx and assessment["confidence"] < fx["min_confidence"]:
        errors.append(f"{fx['name']}: confidence {assessment['confidence']} < {fx['min_confidence']}")
    if "max_confidence" in fx and assessment["confidence"] > fx["max_confidence"]:
        errors.append(f"{fx['name']}: confidence {assessment['confidence']} > {fx['max_confidence']}")
    if verbose:
        print(json.dumps({
            "fixture": fx["name"],
            "categories": sorted(cats),
            "score": score,
            "confidence": assessment["confidence"],
            "actionable": assessment["actionable"],
            "why_actionable": assessment["why_actionable"],
        }, ensure_ascii=False))
    return errors


def check_formatter_veto(*, verbose: bool = False) -> list[str]:
    summary = {
        "data": {
            "total_scanned": 1,
            "assessments": [{"id": "1", "from": "Editor @ The Paypers <Editor@newsletter.thepaypers.com>", "subject": "Monzo enters telecoms with eSIM mobile plan", "priority": "HIGH", "confidence": 25}],
            "hot_alerts": [{"id": "1", "from": "Editor @ The Paypers <Editor@newsletter.thepaypers.com>", "subject": "Monzo enters telecoms with eSIM mobile plan", "priority": "HIGH", "confidence": 25}],
            "llm_analysis": {"actionable_emails": [{"id": "1", "from": "Editor @ The Paypers <Editor@newsletter.thepaypers.com>", "subject": "Monzo enters telecoms with eSIM mobile plan", "category": "assessment", "urgency": "low", "action": "read_and_file", "response_deadline": "when convenient"}]},
        }
    }
    alert = fmt.build_alert(summary)
    if verbose:
        print(json.dumps({"formatter_alert": alert}, ensure_ascii=False))
    if not alert.startswith("📬 Email scan: 1 new email(s) processed"):
        return ["formatter veto failed for newsletter false positive"]
    return []


def hiring_summary(
    *,
    email_id: str,
    subject: str,
    category: str,
    action: str,
    urgency: str = "low",
    pipeline: str = "Sprinklr",
    priority: str = "HIGH",
) -> dict:
    raw = {
        "id": email_id,
        "from": "Miriam Marras <miriam.marras@sprinklr.com>",
        "subject": subject,
        "priority": priority,
        "pipeline_match": pipeline,
        "confidence": 95 if category != "rejection" else 40,
    }
    group_name = {
        "interview_invite": "interview_invites",
        "assessment": "assessments",
        "application_response": "application_responses",
        "follow_up_needed": "follow_ups_needed",
        "recruiter_reach": "recruiter_messages",
        "rejection": "rejections",
    }[category]
    data = {
        "total_scanned": 1,
        "interview_invites": [],
        "assessments": [],
        "application_responses": [],
        "follow_ups_needed": [],
        "recruiter_messages": [],
        "rejections": [],
        "hot_alerts": [],
    }
    data[group_name] = [raw]
    data["llm_analysis"] = {
        "actionable_emails": [{
            "id": email_id,
            "from": raw["from"],
            "subject": subject,
            "category": category,
            "urgency": urgency,
            "action": action,
            "intent": "Hiring-team process update.",
        }],
        "summary": {
            "total_actionable": 0 if action in {"no_action", "read_and_file"} else 1,
            "critical_count": 1 if urgency in {"critical", "high"} else 0,
        },
    }
    return {"data": data}


def check_structured_delivery(*, verbose: bool = False) -> list[str]:
    errors: list[str] = []
    update_cases = [
        ("missed Miriam update", "364923", "Re: Sprinklr Interview - Availability Request", "interview_invite"),
        ("interview reschedule", "364924", "Interview rescheduled - calendar updated", "interview_invite"),
        ("interview cancellation", "364925", "Interview cancelled - no action required", "interview_invite"),
        ("interview feedback", "364926", "Feedback after your interview", "recruiter_reach"),
        ("application rejection", "364927", "Update on your application", "rejection"),
    ]
    for name, email_id, subject, category in update_cases:
        plan = fmt.build_delivery(hiring_summary(
            email_id=email_id,
            subject=subject,
            category=category,
            action="no_action",
        ))
        envelopes = plan.get("envelopes") or []
        update = next((item for item in envelopes if item.get("type") == "hiring_process_update"), None)
        if not update:
            errors.append(f"{name}: missing hiring_process_update envelope")
            continue
        if update.get("action_required") is not False or update.get("importance") != "high":
            errors.append(f"{name}: incorrect structured fields {update}")
        if update.get("pipeline_matches") != ["Sprinklr"]:
            errors.append(f"{name}: missing Sprinklr pipeline match")
        if not update.get("message", "").startswith("📌 Hiring process update"):
            errors.append(f"{name}: incorrect update message")

    medium_plan = fmt.build_delivery(hiring_summary(
        email_id="364929",
        subject="A quick update on your interview process",
        category="recruiter_reach",
        action="no_action",
        priority="MEDIUM",
    ))
    if not any(item.get("type") == "hiring_process_update" for item in medium_plan.get("envelopes") or []):
        errors.append("active-pipeline hiring update was suppressed because priority was medium")

    many = hiring_summary(
        email_id="batch-0",
        subject="Batch process update 0",
        category="interview_invite",
        action="no_action",
    )
    many_data = many["data"]
    many_data["interview_invites"] = []
    many_data["llm_analysis"]["actionable_emails"] = []
    for number in range(7):
        raw = {
            "id": f"batch-{number}",
            "from": "Hiring Team <hiring@example.com>",
            "subject": f"Batch process update {number}",
            "priority": "HIGH",
            "pipeline_match": "ExampleCo",
            "confidence": 90,
        }
        many_data["interview_invites"].append(raw)
        many_data["llm_analysis"]["actionable_emails"].append({
            **raw,
            "category": "interview_invite",
            "urgency": "low",
            "action": "no_action",
        })
    many_plan = fmt.build_delivery(many)
    many_keys = [key for item in many_plan.get("envelopes") or [] for key in item.get("email_keys") or []]
    if len(many_plan.get("envelopes") or []) != 2 or len(set(many_keys)) != 7:
        errors.append(f"batched updates did not ledger every email key: envelopes={len(many_plan.get('envelopes') or [])}, keys={many_keys}")

    action_plan = fmt.build_delivery(hiring_summary(
        email_id="364928",
        subject="Please confirm your interview availability",
        category="interview_invite",
        action="respond",
        urgency="high",
    ))
    action = next((item for item in action_plan.get("envelopes") or [] if item.get("type") == "action_required"), None)
    if not action or action.get("action_required") is not True or action.get("pipeline_matches") != ["Sprinklr"]:
        errors.append(f"action request: incorrect structured envelope {action}")

    noise = {
        "data": {
            "total_scanned": 1,
            "job_alerts": [{"id": "noise-1", "from": "LinkedIn <jobs-noreply@linkedin.com>", "subject": "New jobs for you", "priority": "HIGH"}],
            "llm_analysis": {"actionable_emails": [], "summary": {"total_actionable": 0}},
        }
    }
    if fmt.build_delivery(noise).get("envelopes"):
        errors.append("newsletter/job-alert noise produced a delivery envelope")

    if verbose:
        print(json.dumps({"structured_delivery_errors": errors}, ensure_ascii=False))
    return errors


def check_short_pipeline_collision(*, verbose: bool = False) -> list[str]:
    errors: list[str] = []
    original_pipeline_jobs = ea._get_active_pipeline_jobs
    subject = "In Case You Missed It - Pilot scrawls ‘I’m bored’ into UK sky mid-flight"
    sender = "CNN <cnn@newsletters.cnn.com>"
    try:
        ea._get_active_pipeline_jobs = lambda: [{
            "job_id": "tp-active",
            "company": "TP",
            "title": "VP AI Delivery",
            "recruiter_name": "",
            "recruiter_email": None,
            "recruiter_company": "",
        }]
        match = ea._match_pipeline_company(subject, sender, "")
        categories = ea.categorize_email(subject, sender, "")
        score, pipeline = ea.score_email(subject, sender, "")
        if match != (None, 0) or categories != ["other"] or score != 0 or pipeline is not None:
            errors.append(
                "CNN/TP boundary collision survived classifier guard: "
                f"match={match}, categories={categories}, score={score}, pipeline={pipeline}"
            )

        summary = {
            "data": {
                "total_scanned": 1,
                "recruiter_messages": [] if categories == ["other"] else [{
                    "id": "364999",
                    "from": sender,
                    "subject": subject,
                    "priority": "HIGH",
                    "pipeline_match": pipeline,
                    "confidence": 95,
                }],
                "llm_analysis": {"actionable_emails": [], "summary": {"total_actionable": 0}},
            }
        }
        if fmt.build_delivery(summary).get("envelopes"):
            errors.append("CNN/TP boundary collision produced a Telegram delivery envelope")

        tp_link_match = ea._match_pipeline_company(
            "TP-Link Wi-Fi routers clearance sale",
            "Store <sales@example.com>",
            "",
        )
        if tp_link_match != (None, 0):
            errors.append(f"TP-Link product mail matched active company TP: {tp_link_match}")

        valid_match = ea._match_pipeline_company(
            "TP VP AI Delivery application update",
            "Hiring Team <hiring@teleperformance.com>",
            "",
        )
        if valid_match != ("TP", 6):
            errors.append(f"corroborated TP reference stopped matching: {valid_match}")
    finally:
        ea._get_active_pipeline_jobs = original_pipeline_jobs

    if verbose:
        print(json.dumps({"short_pipeline_collision_errors": errors}, ensure_ascii=False))
    return errors


def main() -> int:
    if getattr(ea, "LLM_MODEL", "") != EXPECTED_LLM_MODEL:
        print(f"FAIL: email-agent LLM_MODEL is {getattr(ea, 'LLM_MODEL', None)!r}, expected {EXPECTED_LLM_MODEL!r}")
        return 1

    parser = argparse.ArgumentParser(description="Run synthetic email-agent regressions.")
    parser.add_argument("--verbose", action="store_true", help="Print fixture-level JSON diagnostics.")
    args = parser.parse_args()

    errors: list[str] = []
    for fixture in FIXTURES:
        errors.extend(check_fixture(fixture, verbose=args.verbose))
    errors.extend(check_formatter_veto(verbose=args.verbose))
    errors.extend(check_structured_delivery(verbose=args.verbose))
    errors.extend(check_short_pipeline_collision(verbose=args.verbose))
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: synthetic email harness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
