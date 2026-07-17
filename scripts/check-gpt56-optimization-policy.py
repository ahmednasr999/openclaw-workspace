#!/usr/bin/env python3
"""Read-only audit for GPT-5.6 reasoning-tier and tool-search policy."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


CLI = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"
CONFIG = Path("/root/.openclaw/openclaw.json")
EXPECTED_LOW = {
    "4db2295a-d3ac-4beb-b902-47516c26432e": "Daily Intel Sweep",
    "a6c9a3a6-5fe0-4506-b8df-e9ba4a7c16e2": "Email Agent (Fri-Sat)",
    "145d964f-e2e5-4b49-8058-f9ddac926f45": "Email Agent (Sun-Thu)",
    "837a64eb-981f-4ae0-ac55-60330a14d615": "Weekly Pipeline Audit",
}


def load_crons() -> list[dict]:
    proc = subprocess.run([CLI, "cron", "list", "--json"], text=True, capture_output=True, timeout=60, check=True)
    return json.loads(proc.stdout)["jobs"]


def audit(config: dict, jobs: list[dict]) -> dict:
    failures: list[str] = []
    if config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary") != "openai/gpt-5.6-sol":
        failures.append("default_model_not_gpt56_sol")
    if config.get("tools", {}).get("toolSearch") is not None:
        failures.append("experimental_tool_search_enabled")
    by_id = {job["id"]: job for job in jobs}
    for job_id, name in EXPECTED_LOW.items():
        job = by_id.get(job_id)
        if not job or not job.get("enabled"):
            failures.append(f"missing_or_disabled:{name}")
            continue
        payload = job.get("payload", {})
        if payload.get("model") != "openai/gpt-5.6-sol":
            failures.append(f"wrong_model:{name}")
        if payload.get("thinking") != "low":
            failures.append(f"wrong_effort:{name}")
    counts: dict[str, int] = {}
    for job in jobs:
        payload = job.get("payload", {})
        if job.get("enabled") and payload.get("kind") == "agentTurn":
            effort = payload.get("thinking") or "default"
            counts[effort] = counts.get(effort, 0) + 1
    return {"ok": not failures, "failures": failures, "enabled_agent_turn_efforts": counts}


def main() -> int:
    result = audit(json.loads(CONFIG.read_text()), load_crons())
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
