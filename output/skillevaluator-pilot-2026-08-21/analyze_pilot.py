#!/usr/bin/env python3
"""Aggregate rubric, routing, latency, and token results for the pilot."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path("/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21")
SKILLS = ("gateway-runtime-safety", "content-publishing-safety", "executive-cv-builder")
ARMS = ("without_skill", "with_skill")


def pct(value: float) -> float:
    return round(value * 100, 1)


def load() -> tuple[dict, dict, dict]:
    datasets = {}
    for skill in SKILLS:
        path = ROOT / "skills" / skill / "evals/evals.json"
        datasets[skill] = json.loads(path.read_text(encoding="utf-8"))["evals"]
    grades = json.loads((ROOT / "manual-grades.json").read_text(encoding="utf-8"))
    manifests = json.loads((ROOT / "runs/run-summary.json").read_text(encoding="utf-8"))
    by_run = {(row["skill"], row["case_id"], row["arm"]): row for row in manifests}
    return datasets, grades, by_run


def main() -> int:
    datasets, grade_doc, by_run = load()
    grades = grade_doc["grades"]
    result = {
        "model": "gpt-5.6-sol",
        "method": grade_doc["method"],
        "skills": {},
        "overall": {},
    }
    totals = {arm: defaultdict(float) for arm in ARMS}
    for skill, cases in datasets.items():
        skill_result = {}
        for arm in ARMS:
            assertion_total = 0
            assertion_pass = 0
            perfect_cases = 0
            routing_pass = 0
            elapsed = 0.0
            input_tokens = 0
            cached_input_tokens = 0
            output_tokens = 0
            for case in cases:
                case_id = case["id"]
                case_grades = grades[case_id][arm]
                assertion_total += len(case_grades)
                assertion_pass += sum(case_grades)
                perfect_cases += int(all(case_grades))
                response_path = ROOT / "runs" / skill / case_id / arm / "response.json"
                response = json.loads(response_path.read_text(encoding="utf-8"))
                routing_pass += int(response.get("skill_used") == case.get("expected_skill"))
                run = by_run[(skill, case_id, arm)]
                elapsed += run["elapsed_seconds"]
                input_tokens += run["usage"]["input_tokens"]
                cached_input_tokens += run["usage"]["cached_input_tokens"]
                output_tokens += run["usage"]["output_tokens"]
            skill_result[arm] = {
                "assertions_passed": assertion_pass,
                "assertions_total": assertion_total,
                "correctness_pct": pct(assertion_pass / assertion_total),
                "perfect_cases": perfect_cases,
                "case_count": len(cases),
                "effectiveness_pct": pct(perfect_cases / len(cases)),
                "routing_passed": routing_pass,
                "discoverability_pct": pct(routing_pass / len(cases)),
                "mean_elapsed_seconds": round(elapsed / len(cases), 3),
                "input_tokens": input_tokens,
                "cached_input_tokens": cached_input_tokens,
                "uncached_input_tokens": input_tokens - cached_input_tokens,
                "output_tokens": output_tokens,
            }
            totals[arm]["assertion_pass"] += assertion_pass
            totals[arm]["assertion_total"] += assertion_total
            totals[arm]["perfect_cases"] += perfect_cases
            totals[arm]["case_count"] += len(cases)
            totals[arm]["routing_pass"] += routing_pass
            totals[arm]["elapsed"] += elapsed
            totals[arm]["input_tokens"] += input_tokens
            totals[arm]["cached_input_tokens"] += cached_input_tokens
            totals[arm]["output_tokens"] += output_tokens
        skill_result["lift_points"] = {
            "correctness": round(skill_result["with_skill"]["correctness_pct"] - skill_result["without_skill"]["correctness_pct"], 1),
            "effectiveness": round(skill_result["with_skill"]["effectiveness_pct"] - skill_result["without_skill"]["effectiveness_pct"], 1),
            "discoverability": round(skill_result["with_skill"]["discoverability_pct"] - skill_result["without_skill"]["discoverability_pct"], 1),
        }
        result["skills"][skill] = skill_result

    for arm in ARMS:
        t = totals[arm]
        result["overall"][arm] = {
            "assertions_passed": int(t["assertion_pass"]),
            "assertions_total": int(t["assertion_total"]),
            "correctness_pct": pct(t["assertion_pass"] / t["assertion_total"]),
            "perfect_cases": int(t["perfect_cases"]),
            "case_count": int(t["case_count"]),
            "effectiveness_pct": pct(t["perfect_cases"] / t["case_count"]),
            "routing_passed": int(t["routing_pass"]),
            "discoverability_pct": pct(t["routing_pass"] / t["case_count"]),
            "mean_elapsed_seconds": round(t["elapsed"] / t["case_count"], 3),
            "input_tokens": int(t["input_tokens"]),
            "cached_input_tokens": int(t["cached_input_tokens"]),
            "uncached_input_tokens": int(t["input_tokens"] - t["cached_input_tokens"]),
            "output_tokens": int(t["output_tokens"]),
            "successful_runs": int(t["case_count"]),
        }
    before = result["overall"]["without_skill"]
    after = result["overall"]["with_skill"]
    result["overall"]["lift_points"] = {
        "correctness": round(after["correctness_pct"] - before["correctness_pct"], 1),
        "effectiveness": round(after["effectiveness_pct"] - before["effectiveness_pct"], 1),
        "discoverability": round(after["discoverability_pct"] - before["discoverability_pct"], 1),
    }
    result["overall"]["cost_change_pct"] = {
        "mean_elapsed": round((after["mean_elapsed_seconds"] / before["mean_elapsed_seconds"] - 1) * 100, 1),
        "input_tokens": round((after["input_tokens"] / before["input_tokens"] - 1) * 100, 1),
        "uncached_input_tokens": round((after["uncached_input_tokens"] / before["uncached_input_tokens"] - 1) * 100, 1),
        "output_tokens": round((after["output_tokens"] / before["output_tokens"] - 1) * 100, 1),
    }
    (ROOT / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
