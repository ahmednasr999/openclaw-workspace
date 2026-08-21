#!/usr/bin/env python3
"""Generate the CEO/NASR weekly operating review.

This is intentionally deterministic: it summarizes current lane evidence,
writes a durable report, and prints a compact Telegram-ready card.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path


ROOT = Path("/root/.openclaw/workspace")
REPORTS = ROOT / "reports"
HEALTH = REPORTS / "health" / "latest.json"
LANES = {
    "HR": Path("/root/.openclaw/workspace-hr/reports/latest.md"),
    "CTO": Path("/root/.openclaw/workspace-cto/reports/latest.md"),
    "CMO": Path("/root/.openclaw/workspace-cmo/reports/latest.md"),
}
JOBZOOM_REPORTS = Path("/root/.openclaw/workspace-jobzoom/reports")
ORCHESTRATION_REPORT = REPORTS / "orchestration-audit" / "latest.json"
ACCOUNT_REGISTRY = ROOT / "data" / "account-experts" / "registry.json"


def read_text(path: Path, limit: int = 5000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return "Missing."
    return text[:limit].strip()


def run_health() -> None:
    script = ROOT / "scripts" / "openclaw-health-dashboard.py"
    if script.exists():
        subprocess.run(
            [str(script), "--write-report"],
            cwd=str(ROOT),
            timeout=90,
            check=False,
            capture_output=True,
            text=True,
        )


def run_orchestration_audit() -> dict:
    script = ROOT / "scripts" / "weekly-orchestration-audit.py"
    if not script.exists():
        return {"ok": False, "error": f"missing audit script: {script}"}
    result = subprocess.run(
        ["python3", str(script)],
        cwd=str(ROOT),
        timeout=90,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "error": result.stderr.strip() or (result.stdout.strip() if result.returncode else ""),
    }


def load_health() -> dict:
    try:
        return json.loads(HEALTH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"overall": "UNKNOWN", "error": str(exc), "checks": []}


def load_json(path: Path, default: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default
    except Exception:
        return default


def first_lines(text: str, keep: int = 10) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:keep]) if lines else "No current report."


def jobzoom_latest() -> list[str]:
    if not JOBZOOM_REPORTS.exists():
        return []
    candidates = {
        *JOBZOOM_REPORTS.glob("JobZoom_Daily_*.pdf"),
        *JOBZOOM_REPORTS.glob("jobzoom-*.pdf"),
    }
    return [str(p) for p in sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)[:3]]


def check_detail(health: dict, name: str) -> str:
    for check in health.get("checks", []):
        if check.get("name") == name:
            return f"{check.get('state', '?')}: {check.get('detail', '')}"
    return "missing"


def build_report(
    now: dt.datetime,
    health: dict,
    lanes: dict[str, str],
    jobs: list[str],
    orchestration: dict,
    accounts: dict,
) -> str:
    date = now.strftime("%Y-%m-%d")
    health_overall = health.get("overall", "UNKNOWN")
    job_lines = "\n".join(f"- {p}" for p in jobs) if jobs else "- No recent JobZoom daily PDFs found."
    orchestration_counts = orchestration.get("counts") or {}
    orchestration_recommendations = orchestration.get("recommendations") or []
    orchestration_lines = "\n".join(f"- {item}" for item in orchestration_recommendations[:8]) or "- Clean-noop: no orchestration action recommended."
    account_rows = accounts.get("accounts") or []
    account_lines = "\n".join(
        f"- {item.get('employer')} - priority {item.get('priority')}; identity {item.get('identity_status')}; {item.get('active_roles')} active role(s)"
        for item in account_rows
    ) or "- No active priority-employer dossiers."

    return f"""# CEO/NASR Operating Review - {date}

Generated: {now.strftime('%Y-%m-%d %H:%M %Z')}
Owner: CEO/NASR
Cadence: weekly, Sunday morning

## Verdict

No emergency action unless the health section says otherwise. CEO/NASR should keep the week focused on decision quality, fewer interruptions, and two proactive lanes: HR opportunity quality and CMO authority output.

## CEO/NASR Score

Current target: 90/100 after one weekly cycle.

Score drivers:
- Raise signal quality: only escalate decisions, material risks, external actions, and strategic opportunities.
- Force cross-agent decisions: turn lane reports into one operating call.
- Reduce Ahmed's cognitive load: no status theater, no duplicate closeouts, no unverified claims.
- Convert repeated misses into durable fixes: memory, workflow rule, skill, script, check, or cron.

## System Health

- Overall: {health_overall}
- Gateway: {check_detail(health, 'gateway')}
- Config: {check_detail(health, 'config')}
- Runtime patches: {check_detail(health, 'runtime_patches')}
- LCM context: {check_detail(health, 'lcm_context')}
- Dashboard: {check_detail(health, 'dashboard_service')}
- Health report: {HEALTH}

## HR Lane

{first_lines(lanes.get('HR', ''), 14)}

CEO/NASR push:
- Maintain salary-first GCC executive opportunity radar.
- Separate Apply Now, Watch, Network First, and Reject.
- Surface roles only when salary probability, title, employer, or strategic access justifies Ahmed's attention.

## CMO Lane

{first_lines(lanes.get('CMO', ''), 14)}

CEO/NASR push:
- Convert drafts into an approval queue with one recommended first post.
- For every post, state why now, what it signals, and the approval risk.
- Keep publishing approval-gated.

## CTO Lane

{first_lines(lanes.get('CTO', ''), 14)}

CEO/NASR push:
- Keep post-change validation packs standard.
- Track warning classes until fixed or accepted as noise.
- Maintain rollback awareness for gateway, browser, Telegram, and Lossless.

## JobZoom Lane

Latest daily artifacts:
{job_lines}

CEO/NASR push:
- Improve salary inference and employer quality ranking.
- Penalize already-applied and low-salary roles earlier.
- Add weekly market signal, not just generated CV count.

## Persistent Account Experts

{account_lines}

Operating rule:
- Keep at most seven active dossiers.
- Refresh on stage change or after 14 days.
- Never infer decision-makers or company identity; unresolved identity blocks networking recommendations.

## Weekly Orchestration Audit

- Audit state: {orchestration.get('terminal_state', 'unknown')}
- Keep: {orchestration_counts.get('KEEP', 0)}
- Fix: {orchestration_counts.get('FIX', 0)}
- Automate: {orchestration_counts.get('AUTOMATE', 0)}
- Combine-review: {orchestration_counts.get('COMBINE-REVIEW', 0)}
- Retire-review: {orchestration_counts.get('RETIRE-REVIEW', 0)}
- Parallelize-review clusters: {len(orchestration.get('parallelize_review') or [])}
- Automatic mutations: {orchestration.get('mutations_performed', 0)}
- Evidence: {ORCHESTRATION_REPORT}

Recommendations:
{orchestration_lines}

## Weekly Decision

Primary focus:
1. HR opportunity quality.
2. CMO authority campaign.

Monitor:
- CTO health and runtime warnings.
- JobZoom scan quality and salary relevance.

## Escalation Rule

Tell Ahmed only when:
- a decision is needed,
- a material risk exists,
- an external action completed or needs approval,
- a system failure affects reliability,
- a high-value opportunity appears,
- or a repeated miss needs a durable fix.

Stay silent when work is routine and no decision changes.
"""


def telegram_card(now: dt.datetime, health: dict, report_path: Path, orchestration: dict, accounts: dict) -> str:
    overall = health.get("overall", "UNKNOWN")
    marker = "OK" if overall == "OK" else overall
    decision = "focus this week on HR opportunity quality and CMO authority output. No emergency action."
    if overall != "OK":
        decision = "review the health warning first, then continue HR opportunity quality and CMO authority output."
    counts = orchestration.get("counts") or {}
    active_accounts = len(accounts.get("accounts") or [])
    return "\n".join(
        [
            f"CEO/NASR Weekly - {now.strftime('%Y-%m-%d')} - {marker}",
            f"Decision: {decision}",
            f"Orchestration: {counts.get('FIX', 0)} fix, {counts.get('AUTOMATE', 0)} automate, {counts.get('COMBINE-REVIEW', 0)} combine-review, {len(orchestration.get('parallelize_review') or [])} parallelize-review cluster(s); advisory only.",
            f"Priority employers: {active_accounts} active evidence-linked dossier(s).",
            "Next: resolve FIX items first, then refresh any stale or ambiguous employer dossier.",
            f"Report: {report_path}",
            "Needs Ahmed: only exact promotion, retirement, or outbound decisions; no automatic changes were made.",
        ]
    )


def main() -> int:
    now = dt.datetime.now().astimezone()
    run_health()
    audit_run = run_orchestration_audit()
    health = load_health()
    lanes = {name: read_text(path) for name, path in LANES.items()}
    jobs = jobzoom_latest()
    if audit_run.get("ok"):
        orchestration = load_json(ORCHESTRATION_REPORT, {"terminal_state": "error", "counts": {}, "recommendations": [], "mutations_performed": 0})
    else:
        orchestration = {
            "terminal_state": "error",
            "counts": {},
            "recommendations": [f"FIX: orchestration audit did not complete - {audit_run.get('error') or 'unknown error'}"],
            "mutations_performed": 0,
            "parallelize_review": [],
        }
    accounts = load_json(ACCOUNT_REGISTRY, {"accounts": []})
    report = build_report(now, health, lanes, jobs, orchestration, accounts)

    REPORTS.mkdir(parents=True, exist_ok=True)
    dated = REPORTS / f"ceo-nasr-operating-review-{now.strftime('%Y-%m-%d')}.md"
    latest = REPORTS / "ceo-nasr-operating-review-latest.md"
    dated.write_text(report, encoding="utf-8")
    latest.write_text(report, encoding="utf-8")

    print(telegram_card(now, health, dated, orchestration, accounts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
