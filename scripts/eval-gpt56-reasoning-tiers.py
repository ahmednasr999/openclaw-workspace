#!/usr/bin/env python3
"""Bounded GPT-5.6 Sol low-vs-medium reasoning evaluation.

Uses isolated, tool-free sessions and deterministic scoring. It never changes
the live model, cron jobs, or delivery state.
"""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import json
import subprocess
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"
MODEL = "openai/gpt-5.6-sol"
LEVELS = ("low", "medium")

TASKS = [
    {
        "id": "email_ack",
        "prompt": (
            "Do not use tools. Return JSON only with keys classification, urgent, action. "
            "Allowed classification: interview_invite, recruiter_screen, application_acknowledgement, "
            "job_alert, rejection, newsletter_noise. urgent is boolean. action is notify or suppress. "
            "Subject: Your application was received. Body: Thank you for applying. We will review your "
            "application and contact you if selected."
        ),
        "expected": {"classification": "application_acknowledgement", "urgent": False, "action": "suppress"},
    },
    {
        "id": "funding_split",
        "prompt": (
            "Do not use tools. Return JSON only with keys equity_eur_m, debt_facility_eur_m, "
            "equity_round_eur_m, combined_247m_is_equity_round. Aria announced EUR 7 million in equity "
            "and a EUR 240 million debt facility. Use numbers. The last key asks whether the combined "
            "EUR 247 million is an equity round and must be a boolean."
        ),
        "expected": {"equity_eur_m": 7, "debt_facility_eur_m": 240, "equity_round_eur_m": 7, "combined_247m_is_equity_round": False},
    },
    {
        "id": "intel_rank",
        "prompt": (
            "Do not use tools. Rank the decision-relevant fintech items. Return JSON only with key ranked_ids, "
            "an array of exactly 3 ids. Apply these rules in order: exclude entertainment/noise; among remaining "
            "verified fintech items put direct GCC relevance first, then capital significance, then regulation. "
            "Items: A verified Qatar merchant-acquiring partnership; "
            "B unverified celebrity wedding; C verified USD 76m fintech Series C; D opinion about football; "
            "E verified central-bank digital-bank licensing rule."
        ),
        "expected": {"ranked_ids": ["A", "C", "E"]},
    },
    {
        "id": "ops_triage",
        "prompt": (
            "Do not use tools. Return JSON only with keys severity, user_impact, next_action. "
            "Log evidence: gateway probe ok=true degraded=false; Telegram connected=true; config valid; "
            "one warning says a legacy migrated metadata sidecar was retained because conflicting plugin metadata exists. "
            "Allowed severity: healthy, warning, critical. user_impact is boolean. next_action is monitor or repair_now."
        ),
        "expected": {"severity": "warning", "user_impact": False, "next_action": "monitor"},
    },
]


def extract_text(payload: dict) -> str:
    return payload["result"]["payloads"][0]["text"].strip()


def run_case(task: dict, level: str, stamp: str) -> dict:
    key = f"agent:main:gpt56-effort-eval-{stamp}-{task['id']}-{level}-{uuid.uuid4().hex[:8]}"
    command = [
        CLI, "agent", "--agent", "main", "--session-key", key,
        "--message", task["prompt"], "--model", MODEL, "--thinking", level,
        "--json", "--timeout", "180",
    ]
    started = time.monotonic()
    proc = subprocess.run(command, text=True, capture_output=True, timeout=210)
    elapsed_ms = round((time.monotonic() - started) * 1000)
    result = {
        "task": task["id"], "level": level, "elapsed_ms": elapsed_ms,
        "exit_code": proc.returncode, "passed": False,
    }
    if proc.returncode != 0:
        result["error"] = proc.stderr[-1200:]
        return result
    try:
        payload = json.loads(proc.stdout)
        text = extract_text(payload)
        parsed = json.loads(text)
        usage = payload["result"]["meta"]["agentMeta"]["usage"]
        result.update({
            "response": parsed,
            "expected": task["expected"],
            "passed": parsed == task["expected"],
            "input_tokens": usage.get("input"),
            "output_tokens": usage.get("output"),
            "total_tokens": usage.get("total"),
            "model": payload["result"]["meta"]["agentMeta"].get("model"),
            "fallback_used": payload["result"]["meta"].get("executionTrace", {}).get("fallbackUsed"),
        })
    except Exception as exc:
        result["error"] = f"parse failure: {exc}; stdout={proc.stdout[-1200:]}"
    return result


def main() -> int:
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    cases = [(task, level, stamp) for task in TASKS for level in LEVELS]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda args: run_case(*args), cases))
    summary = {}
    for level in LEVELS:
        rows = [row for row in results if row["level"] == level]
        summary[level] = {
            "passed": sum(row["passed"] for row in rows),
            "total": len(rows),
            "avg_elapsed_ms": round(sum(row["elapsed_ms"] for row in rows) / len(rows)),
            "output_tokens": sum((row.get("output_tokens") or 0) for row in rows),
            "fallbacks": sum(bool(row.get("fallback_used")) for row in rows),
        }
    low = summary["low"]
    medium = summary["medium"]
    recommendation = "keep_medium"
    if low["passed"] == low["total"] and medium["passed"] == medium["total"]:
        recommendation = "low_for_deterministic_wrappers"
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": MODEL,
        "scope": "isolated tool-free deterministic fixtures",
        "summary": summary,
        "recommendation": recommendation,
        "results": sorted(results, key=lambda row: (row["task"], row["level"])),
    }
    out_dir = ROOT / "reports" / "reasoning-evals"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"gpt56-effort-{stamp}.json"
    latest_path = out_dir / "gpt56-effort-latest.json"
    report_path = out_dir / f"gpt56-effort-{stamp}.md"
    data = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    json_path.write_text(data)
    latest_path.write_text(data)
    lines = [
        "# GPT-5.6 Sol reasoning-effort evaluation", "",
        f"- Model: `{MODEL}`", f"- Recommendation: **{recommendation}**", "",
        "| Effort | Passed | Avg latency | Output tokens | Fallbacks |",
        "|---|---:|---:|---:|---:|",
    ]
    for level in LEVELS:
        row = summary[level]
        lines.append(f"| {level} | {row['passed']}/{row['total']} | {row['avg_elapsed_ms']} ms | {row['output_tokens']} | {row['fallbacks']} |")
    lines.extend(["", "## Case results", ""])
    for row in payload["results"]:
        lines.append(f"- {row['task']} / {row['level']}: {'PASS' if row['passed'] else 'FAIL'} ({row['elapsed_ms']} ms)")
    report_path.write_text("\n".join(lines) + "\n")
    print(json.dumps({"report": str(report_path), "json": str(json_path), "recommendation": recommendation, "summary": summary}, indent=2))
    return 0 if all(row["passed"] for row in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
