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

EXPECTED_LLM_MODEL = "openai/gpt-5.5"

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
    if not alert.startswith("📬 Email scan: all clear"):
        return ["formatter veto failed for newsletter false positive"]
    return []


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
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: synthetic email harness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
