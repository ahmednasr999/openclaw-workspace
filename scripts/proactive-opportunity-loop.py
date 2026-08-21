#!/usr/bin/env python3
"""Bounded proactive opportunity loop for NASR.

The producer may only record cited proposals. A separate evaluator must verify
every citation. Finalization can create local action briefs or owner handoffs;
all other actions remain approval-required. The script never sends messages,
publishes, changes runtime/config, writes outside the main workspace, or calls
an arbitrary executor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


DEFAULT_WORKSPACE = Path("/root/.openclaw/workspace")
CONFIG_REL = Path("config/proactive-opportunity-loop.json")
DATA_REL = Path("data/proactive-opportunity-loop")
REPORT_REL = Path("reports/proactive-opportunity-loop")


class LoopError(RuntimeError):
    pass


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def now_cairo(value: str | None = None) -> datetime:
    zone = ZoneInfo("Africa/Cairo")
    if value:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=zone)
        return parsed.astimezone(zone)
    return datetime.now(zone)


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", value.lower()).strip()


def compact(value: Any, limit: int = 500) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit].rstrip()


def evidence_id(kind: str, source: str, locator: str) -> str:
    raw = f"{kind}|{source}|{locator}".encode()
    return "ev-" + hashlib.sha256(raw).hexdigest()[:12]


def add_file_evidence(items: list[dict[str, Any]], path: Path, kind: str,
                      summary: str, details: Any, locator: str, now: datetime) -> None:
    if not path.exists():
        return
    modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone(now.tzinfo)
    source = str(path)
    items.append({
        "evidence_id": evidence_id(kind, source, locator),
        "kind": kind,
        "source": source,
        "locator": locator,
        "observed_at": now.isoformat(),
        "source_modified_at": modified.isoformat(),
        "freshness_hours": round(max(0.0, (now - modified).total_seconds() / 3600), 2),
        "summary": compact(summary, 300),
        "details": details,
    })


def active_task_excerpt(path: Path) -> tuple[str, list[str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    selected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") or re.match(r"^- (Priority|Status|Next|Real warning):", stripped):
            selected.append(stripped)
        if len(selected) >= 28:
            break
    return f"{sum(1 for line in lines if line.startswith('## '))} tracked task sections", selected


def collect_cron_evidence(now: datetime) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unavailable", "reason": compact(exc)}
    if result.returncode != 0:
        return {"status": "unavailable", "reason": compact(result.stderr or result.stdout)}
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"status": "unavailable", "reason": f"invalid JSON: {exc}"}
    failures = []
    for job in payload.get("jobs", []):
        state = job.get("state") or {}
        errors = int(state.get("consecutiveErrors") or 0)
        status = job.get("status") or state.get("lastRunStatus")
        if errors or status == "error":
            failures.append({
                "id": job.get("id"),
                "name": job.get("name"),
                "agent_id": job.get("agentId"),
                "status": status,
                "consecutive_errors": errors,
                "last_error": compact(state.get("lastError") or state.get("lastDiagnosticSummary"), 300),
                "next_run_at_ms": state.get("nextRunAtMs"),
            })
    return {
        "status": "ok",
        "observed_at": now.isoformat(),
        "total_jobs": len(payload.get("jobs", [])),
        "failures": failures,
    }


def collect(args: argparse.Namespace) -> int:
    workspace = args.workspace.resolve()
    config = load_json(workspace / CONFIG_REL, {})
    now = now_cairo(args.now)
    run_id = args.run_id or now.strftime("%Y%m%dT%H%M%S%z")
    items: list[dict[str, Any]] = []

    active = workspace / "memory/active-tasks.md"
    if active.exists():
        summary, details = active_task_excerpt(active)
        add_file_evidence(items, active, "active_tasks", summary, details, "tracked sections and status lines", now)

    daily = workspace / "memory" / f"{now.date().isoformat()}.md"
    if daily.exists():
        lines = daily.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = [line for line in lines[-120:] if line.strip()][-40:]
        add_file_evidence(items, daily, "daily_context", f"{len(lines)} lines in today's note", tail,
                          "last 40 non-empty lines", now)

    resolver = workspace / "reports/open-work-resolver/briefing.json"
    resolver_data = load_json(resolver, {})
    if isinstance(resolver_data, dict):
        counts = {key: len(resolver_data.get(key) or []) for key in ("progress", "intervention", "closures")}
        add_file_evidence(items, resolver, "open_work", f"Resolver buckets: {counts}", resolver_data,
                          "progress/intervention/closures", now)

    intelligence = workspace / "data/executive-intelligence-latest.json"
    intelligence_data = load_json(intelligence, {})
    if isinstance(intelligence_data, dict):
        top = intelligence_data.get("top_signals") or intelligence_data.get("signals") or []
        add_file_evidence(items, intelligence, "executive_intelligence",
                          f"status={intelligence_data.get('status')} top_signals={len(top)}",
                          {"generated_at": intelligence_data.get("generated_at"), "top_signals": top[:8]},
                          "generated_at and top signals", now)

    intel_md = workspace / "intel/DAILY-INTEL.md"
    if intel_md.exists():
        lines = intel_md.read_text(encoding="utf-8", errors="replace").splitlines()
        selected = [line for line in lines[:180] if line.startswith(("#", "- [", "**"))][:45]
        add_file_evidence(items, intel_md, "daily_intel", f"{len(lines)} lines", selected,
                          "first 45 headings/signals", now)

    calendar = Path("/tmp") / f"calendar-events-{now.date().isoformat()}.json"
    calendar_data = load_json(calendar, None)
    if isinstance(calendar_data, list):
        add_file_evidence(items, calendar, "calendar", f"{len(calendar_data)} events today",
                          calendar_data[:12], "today's event array", now)

    cron = collect_cron_evidence(now)
    items.append({
        "evidence_id": evidence_id("cron_health", "command:openclaw cron list --json", "error jobs"),
        "kind": "cron_health",
        "source": "command:openclaw cron list --json",
        "locator": "jobs with status=error or consecutiveErrors>0",
        "observed_at": now.isoformat(),
        "source_modified_at": now.isoformat(),
        "freshness_hours": 0,
        "summary": f"status={cron.get('status')} failures={len(cron.get('failures') or [])}",
        "details": cron,
    })

    snapshot = {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": now.isoformat(),
        "status": "ok" if items else "blocked",
        "contract": {
            "question": "Given Ahmed's goals and current context, what valuable action is being missed?",
            "max_candidates": int(config.get("max_candidates", 3)),
            "allowed_auto_actions": config.get("allowed_auto_actions", []),
            "approval_boundary": "All external, public, financial, credential, destructive, runtime/config, and third-party messaging actions require Ahmed's approval.",
        },
        "evidence": items,
    }
    data_dir = workspace / DATA_REL
    atomic_write(data_dir / "snapshots" / f"{run_id}.json", dump_json(snapshot))
    atomic_write(data_dir / "latest-snapshot.json", dump_json(snapshot))
    atomic_write(data_dir / "latest-run-id.txt", run_id + "\n")
    print(dump_json({
        "status": snapshot["status"],
        "run_id": run_id,
        "evidence_count": len(items),
        "evidence": [{"evidence_id": x["evidence_id"], "kind": x["kind"], "summary": x["summary"]} for x in items],
    }).rstrip())
    return 0 if items else 2


def snapshot_for(workspace: Path, run_id: str) -> dict[str, Any]:
    path = workspace / DATA_REL / "snapshots" / f"{run_id}.json"
    data = load_json(path)
    if not isinstance(data, dict):
        raise LoopError(f"missing snapshot for run {run_id}")
    return data


def latest_run_id(workspace: Path) -> str:
    path = workspace / DATA_REL / "latest-run-id.txt"
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise LoopError("no current proactive-loop run") from exc


def propose(args: argparse.Namespace) -> int:
    workspace = args.workspace.resolve()
    run_id = args.run_id or latest_run_id(workspace)
    snapshot = snapshot_for(workspace, run_id)
    evidence = {row["evidence_id"]: row for row in snapshot.get("evidence", [])}
    cited = list(dict.fromkeys(args.evidence_id or []))
    missing = [value for value in cited if value not in evidence]
    if not cited or missing:
        raise LoopError(f"proposal must cite valid evidence; missing={missing}")
    config = load_json(workspace / CONFIG_REL, {})
    proposals_path = workspace / DATA_REL / "proposals" / f"{run_id}.json"
    payload = load_json(proposals_path, {"run_id": run_id, "proposals": []})
    proposals = payload.get("proposals") or []
    key = normalized(args.title + " " + args.action_summary)
    for row in proposals:
        if normalized(row.get("title", "") + " " + row.get("action_summary", "")) == key:
            print(dump_json({"status": "duplicate", "proposal_id": row["proposal_id"]}).rstrip())
            return 0
    maximum = int(config.get("max_candidates", 3))
    if len(proposals) >= maximum:
        raise LoopError(f"candidate cap reached ({maximum})")
    raw_id = f"{run_id}|{key}".encode()
    proposal_id = "opp-" + hashlib.sha256(raw_id).hexdigest()[:14]
    row = {
        "proposal_id": proposal_id,
        "run_id": run_id,
        "created_at": now_cairo().isoformat(),
        "title": compact(args.title, 180),
        "priority": args.priority,
        "action_kind": args.action_kind,
        "action_summary": compact(args.action_summary, 600),
        "why_now": compact(args.why_now, 600),
        "owner": compact(args.owner, 80),
        "evidence_ids": cited,
        "approval_reason": compact(args.approval_reason, 400),
        "producer_status": "proposed",
    }
    proposals.append(row)
    atomic_write(proposals_path, dump_json({"run_id": run_id, "proposals": proposals}))
    atomic_write(workspace / DATA_REL / "latest-proposals.json", dump_json({"run_id": run_id, "proposals": proposals}))
    print(dump_json({"status": "created", "proposal": row}).rstrip())
    return 0


def review(args: argparse.Namespace) -> int:
    workspace = args.workspace.resolve()
    run_id = args.run_id or latest_run_id(workspace)
    proposals = load_json(workspace / DATA_REL / "proposals" / f"{run_id}.json", {}).get("proposals", [])
    proposal = next((row for row in proposals if row.get("proposal_id") == args.proposal_id), None)
    if not proposal:
        raise LoopError(f"unknown proposal {args.proposal_id}")
    checked = list(dict.fromkeys(args.checked_evidence or []))
    required = proposal.get("evidence_ids") or []
    if sorted(checked) != sorted(required):
        raise LoopError("reviewer must independently check every cited evidence id")
    reviews_path = workspace / DATA_REL / "reviews" / f"{run_id}.json"
    payload = load_json(reviews_path, {"run_id": run_id, "reviews": []})
    reviews = [row for row in (payload.get("reviews") or []) if row.get("proposal_id") != args.proposal_id]
    row = {
        "proposal_id": args.proposal_id,
        "run_id": run_id,
        "reviewed_at": now_cairo().isoformat(),
        "verdict": args.verdict,
        "reason": compact(args.reason, 700),
        "checked_evidence_ids": checked,
        "reviewer": "fresh-isolated-evaluator",
    }
    reviews.append(row)
    atomic_write(reviews_path, dump_json({"run_id": run_id, "reviews": reviews}))
    atomic_write(workspace / DATA_REL / "latest-reviews.json", dump_json({"run_id": run_id, "reviews": reviews}))
    print(dump_json({"status": "recorded", "review": row}).rstrip())
    return 0


def history_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def duplicate_of(proposal: dict[str, Any], history: list[dict[str, Any]], now: datetime,
                 window_days: int, threshold: float) -> str | None:
    current = normalized(proposal.get("title", "") + " " + proposal.get("action_summary", ""))
    cutoff = now - timedelta(days=window_days)
    for row in history:
        when_text = str(row.get("finalized_at") or "")
        try:
            when = datetime.fromisoformat(when_text.replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=now.tzinfo)
            when = when.astimezone(now.tzinfo)
        except ValueError:
            continue
        if when < cutoff:
            continue
        previous = normalized(row.get("title", "") + " " + row.get("action_summary", ""))
        if current and previous and SequenceMatcher(None, current, previous).ratio() >= threshold:
            return str(row.get("proposal_id") or "prior item")
    return None


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:70] or "opportunity"


def write_auto_artifact(workspace: Path, run_id: str, proposal: dict[str, Any],
                        evidence: dict[str, dict[str, Any]]) -> str:
    folder = workspace / REPORT_REL / run_id
    path = folder / f"{slugify(proposal['title'])}.md"
    label = "Action brief" if proposal["action_kind"] == "prepare_action_brief" else "Owner handoff"
    lines = [
        f"# {label}: {proposal['title']}",
        "",
        f"- Status: prepared and evaluator-approved",
        f"- Owner: {proposal.get('owner') or 'NASR'}",
        f"- Priority: {proposal.get('priority')}",
        f"- Run: {run_id}",
        "",
        "## Why now",
        "",
        proposal.get("why_now", ""),
        "",
        "## Prepared next action",
        "",
        proposal.get("action_summary", ""),
        "",
        "## Evidence",
        "",
    ]
    for item_id in proposal.get("evidence_ids", []):
        item = evidence[item_id]
        lines.append(f"- `{item_id}` — {item['source']} ({item['locator']}): {item['summary']}")
    lines += [
        "",
        "## Boundary",
        "",
        "This artifact is internal preparation only. It does not authorize external messaging, publishing, applications, financial actions, credential changes, destructive work, runtime/config changes, or cross-workspace mutation.",
        "",
    ]
    atomic_write(path, "\n".join(lines))
    return str(path)


def append_history(path: Path, rows: list[dict[str, Any]]) -> None:
    existing = {row.get("proposal_id") for row in history_rows(path)}
    additions = [row for row in rows if row.get("proposal_id") not in existing]
    if not additions:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in additions:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def finalize(args: argparse.Namespace) -> int:
    workspace = args.workspace.resolve()
    run_id = args.run_id or latest_run_id(workspace)
    config = load_json(workspace / CONFIG_REL, {})
    snapshot = snapshot_for(workspace, run_id)
    evidence = {row["evidence_id"]: row for row in snapshot.get("evidence", [])}
    proposals = load_json(workspace / DATA_REL / "proposals" / f"{run_id}.json", {}).get("proposals", [])
    reviews = load_json(workspace / DATA_REL / "reviews" / f"{run_id}.json", {}).get("reviews", [])
    reviews_by_id = {row.get("proposal_id"): row for row in reviews}
    history_path = workspace / DATA_REL / "history.jsonl"
    history = history_rows(history_path)
    now = now_cairo(args.now)
    allowed = set(config.get("allowed_auto_actions") or [])
    approval_terms = [normalized(x) for x in config.get("approval_only_terms") or []]
    minimum = int(config.get("minimum_priority", 60))
    outcomes = []

    for proposal in proposals:
        review_row = reviews_by_id.get(proposal.get("proposal_id"))
        status = "rejected"
        reason = "missing independent evaluator review"
        artifact = ""
        cited = proposal.get("evidence_ids") or []
        if review_row and review_row.get("verdict") == "accept":
            checked = review_row.get("checked_evidence_ids") or []
            if sorted(checked) != sorted(cited) or any(item not in evidence for item in cited):
                reason = "evidence verification is incomplete"
            elif int(proposal.get("priority") or 0) < minimum:
                reason = f"priority below {minimum}"
            else:
                duplicate = duplicate_of(
                    proposal,
                    history,
                    now,
                    int(config.get("duplicate_window_days", 14)),
                    float(config.get("duplicate_similarity", 0.88)),
                )
                if duplicate:
                    status = "duplicate"
                    reason = f"duplicates recent proposal {duplicate}"
                else:
                    action_text = normalized(proposal.get("action_summary", ""))
                    approval_hit = next((term for term in approval_terms if term and term in action_text), None)
                    if proposal.get("action_kind") in allowed and not approval_hit:
                        status = "auto_prepared"
                        reason = "fresh evaluator accepted all evidence; action is inside the local preparation allowlist"
                        artifact = write_auto_artifact(workspace, run_id, proposal, evidence)
                    else:
                        status = "approval_required"
                        reason = proposal.get("approval_reason") or (
                            f"action crosses approval term: {approval_hit}" if approval_hit else "action is outside the auto-action allowlist"
                        )
        elif review_row:
            reason = review_row.get("reason") or "evaluator rejected the proposal"
        outcome = {
            **proposal,
            "finalized_at": now.isoformat(),
            "review": review_row,
            "status": status,
            "final_reason": reason,
            "artifact": artifact,
        }
        outcomes.append(outcome)

    result = {
        "schema_version": 1,
        "run_id": run_id,
        "finalized_at": now.isoformat(),
        "status": "clean_noop" if not outcomes else "complete",
        "outcomes": outcomes,
        "counts": {
            name: sum(1 for row in outcomes if row["status"] == name)
            for name in ("auto_prepared", "approval_required", "duplicate", "rejected")
        },
    }
    data_dir = workspace / DATA_REL
    atomic_write(data_dir / "results" / f"{run_id}.json", dump_json(result))
    atomic_write(data_dir / "latest-result.json", dump_json(result))
    append_history(history_path, outcomes)

    report_lines = [
        f"# Proactive Opportunity Loop — {run_id}", "",
        f"- Finalized: {result['finalized_at']}",
        f"- Counts: {result['counts']}", "",
    ]
    if not outcomes:
        report_lines += ["No evidence-backed missed action survived the producer/evaluator gates.", ""]
    for row in outcomes:
        report_lines += [
            f"## {row['title']}", "",
            f"- Status: `{row['status']}`",
            f"- Priority: {row['priority']}",
            f"- Owner: {row.get('owner') or 'NASR'}",
            f"- Decision: {row['final_reason']}",
            f"- Prepared artifact: {row.get('artifact') or 'none'}",
            "",
            row.get("action_summary", ""), "",
        ]
    report_path = workspace / REPORT_REL / f"proactive-opportunity-{run_id}.md"
    atomic_write(report_path, "\n".join(report_lines))
    atomic_write(workspace / REPORT_REL / "latest.md", "\n".join(report_lines))

    actionable = [row for row in outcomes if row["status"] in {"auto_prepared", "approval_required"}]
    if not actionable:
        print("NO_REPLY")
        return 0
    lines = ["Proactive loop:"]
    for row in actionable:
        marker = "Prepared" if row["status"] == "auto_prepared" else "Approval needed"
        lines.append(f"- {marker}: {row['title']} — {row['action_summary']}")
    lines.append(f"Evidence: {report_path}")
    print("\n".join(lines))
    return 0


def status(args: argparse.Namespace) -> int:
    workspace = args.workspace.resolve()
    latest = load_json(workspace / DATA_REL / "latest-result.json", {})
    print(dump_json(latest).rstrip())
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    sub = root.add_subparsers(dest="command", required=True)

    collect_cmd = sub.add_parser("collect")
    collect_cmd.add_argument("--run-id")
    collect_cmd.add_argument("--now")
    collect_cmd.set_defaults(func=collect)

    propose_cmd = sub.add_parser("propose")
    propose_cmd.add_argument("--run-id")
    propose_cmd.add_argument("--title", required=True)
    propose_cmd.add_argument("--priority", type=int, choices=range(1, 101), required=True)
    propose_cmd.add_argument("--action-kind", required=True, choices=(
        "prepare_action_brief", "prepare_owner_handoff", "approval_request", "no_action"
    ))
    propose_cmd.add_argument("--action-summary", required=True)
    propose_cmd.add_argument("--why-now", required=True)
    propose_cmd.add_argument("--owner", default="NASR")
    propose_cmd.add_argument("--evidence-id", action="append", required=True)
    propose_cmd.add_argument("--approval-reason", default="")
    propose_cmd.set_defaults(func=propose)

    review_cmd = sub.add_parser("review")
    review_cmd.add_argument("--run-id")
    review_cmd.add_argument("--proposal-id", required=True)
    review_cmd.add_argument("--verdict", choices=("accept", "reject"), required=True)
    review_cmd.add_argument("--reason", required=True)
    review_cmd.add_argument("--checked-evidence", action="append", required=True)
    review_cmd.set_defaults(func=review)

    finalize_cmd = sub.add_parser("finalize")
    finalize_cmd.add_argument("--run-id")
    finalize_cmd.add_argument("--now")
    finalize_cmd.set_defaults(func=finalize)

    status_cmd = sub.add_parser("status")
    status_cmd.set_defaults(func=status)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return int(args.func(args))
    except LoopError as exc:
        print(dump_json({"status": "blocked", "reason": str(exc)}).rstrip())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
