#!/usr/bin/env python3
"""Read-only outcome resolver for persistent OpenClaw work.

The resolver observes canonical evidence, classifies the next operational state,
and writes audit/briefing views. It never calls an executor or mutates its data.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


WORKSPACE = Path("/root/.openclaw/workspace")
DEFAULT_CONFIG = WORKSPACE / "config/open-work-resolver.json"
APPROVAL_MARKERS = (
    "approval_required",
    "awaiting_approval",
    "unknown_sensitive_answer",
    "mfa_required",
    "otp_required",
    "captcha_required",
)


class ResolverError(RuntimeError):
    pass


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


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


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ResolverError(f"missing evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ResolverError(f"invalid JSON evidence: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ResolverError(f"expected JSON object: {path}")
    return data


def run_json(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ResolverError(f"evidence command failed: {command[0]}: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().replace("\n", " ")[:400]
        raise ResolverError(f"evidence command rc={result.returncode}: {detail}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ResolverError(f"evidence command returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ResolverError("evidence command did not return a JSON object")
    return data


def systemd_state(service: str) -> dict[str, Any]:
    command = [
        "systemctl",
        "--user",
        "show",
        service,
        "--no-pager",
        "-p",
        "LoadState",
        "-p",
        "ActiveState",
        "-p",
        "SubState",
        "-p",
        "Result",
        "-p",
        "MainPID",
        "-p",
        "NRestarts",
        "-p",
        "ExecMainStatus",
    ]
    environment = os.environ.copy()
    runtime_dir = Path(f"/run/user/{os.getuid()}")
    if runtime_dir.is_dir():
        environment.setdefault("XDG_RUNTIME_DIR", str(runtime_dir))
        bus = runtime_dir / "bus"
        if bus.exists():
            environment.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path={bus}")
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ResolverError(f"cannot inspect service {service}: {exc}") from exc
    if result.returncode != 0:
        raise ResolverError(f"cannot inspect service {service}: {result.stderr.strip()[:300]}")
    values: dict[str, Any] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def pid_is_alive(pid: Any) -> bool:
    try:
        number = int(pid)
    except (TypeError, ValueError):
        return False
    return number > 0 and Path(f"/proc/{number}").exists()


def previous_item(snapshot: dict[str, Any], item_id: str) -> dict[str, Any] | None:
    for item in snapshot.get("items", []):
        if isinstance(item, dict) and item.get("id") == item_id:
            return item
    return None


def evaluate_linkedin_plus30(
    item: dict[str, Any],
    supervisor: dict[str, Any],
    ledger_status: dict[str, Any],
    service: dict[str, Any],
    now: datetime,
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    target = int(item["target"])
    verified = int(ledger_status.get("verified", 0))
    state_verified = int(supervisor.get("verified", -1))
    remaining = max(0, target - verified)
    stale_after = int(item.get("stale_after_seconds", 900))
    heartbeat = parse_timestamp(str(supervisor.get("heartbeat_at") or ""))
    heartbeat_age = None if heartbeat is None else max(0, int((now - heartbeat).total_seconds()))
    stale_deadline = None if heartbeat is None else heartbeat + timedelta(seconds=stale_after)
    main_pid = service.get("MainPID")
    supervisor_pid = supervisor.get("supervisor_pid")
    service_active = service.get("ActiveState") == "active" and service.get("SubState") == "running"
    child_event = supervisor.get("child_event")
    terminal_done = False
    if isinstance(child_event, dict) and child_event.get("event") == "done":
        try:
            terminal_done = (
                int(child_event.get("submitted", -1)) >= target
                and int(child_event.get("target", -1)) == target
            )
        except (TypeError, ValueError):
            terminal_done = False

    evidence_issues: list[str] = []
    evidence_notes: list[str] = []
    if state_verified > verified:
        evidence_issues.append(
            f"supervisor count {state_verified} overclaims strict-ledger count {verified}"
        )
    elif state_verified < verified:
        evidence_notes.append(
            f"supervisor counter trails the strict ledger by {verified - state_verified} during an active cycle"
        )
    if terminal_done:
        evidence_notes.append(
            "supervisor recorded terminal completion; retired runtime evidence is informational"
        )
    else:
        if heartbeat is None:
            evidence_issues.append("supervisor heartbeat is missing or invalid")
        elif heartbeat_age is not None and heartbeat_age > stale_after:
            evidence_issues.append(
                f"supervisor heartbeat is stale by {heartbeat_age - stale_after}s"
            )
        if not pid_is_alive(supervisor_pid):
            evidence_issues.append("supervisor PID is not alive")
        if str(main_pid or "0") != str(supervisor_pid or ""):
            evidence_issues.append(
                f"systemd MainPID {main_pid or 0} disagrees with supervisor PID {supervisor_pid or 0}"
            )

    previous_verified = None if previous is None else previous.get("verified")
    prior_verified = None if previous_verified is None else int(previous_verified)
    delta = 0 if prior_verified is None else verified - prior_verified
    reason = str(supervisor.get("reason") or "")
    approval_required = any(marker in reason.lower() for marker in APPROVAL_MARKERS)

    if verified >= target and not evidence_issues:
        status = "verified_closed"
        blocker = None
        next_action = "No executor action; preserve the strict-ledger closure evidence."
    elif approval_required:
        status = "approval_required"
        blocker = reason
        next_action = "Escalate the exact approval decision to Ahmed; do not bypass the gate."
    elif evidence_issues:
        status = "intervention_required"
        blocker = "; ".join(evidence_issues)
        next_action = "Reconcile the canonical ledger, supervisor state, and service ownership before continuing."
    elif not service_active:
        status = "intervention_required"
        blocker = f"service is {service.get('ActiveState')}/{service.get('SubState')} before target completion"
        next_action = "Diagnose the inactive executor; restart only through the campaign's approved recovery path."
    elif delta > 0 or state_verified < verified:
        status = "progress"
        blocker = None
        next_action = f"Continue the active worker; {remaining} strict applications remain."
    else:
        status = "in_progress"
        blocker = None
        next_action = f"Continue the active worker; {remaining} strict applications remain."

    return {
        "id": item["id"],
        "title": item["title"],
        "owner": item["owner"],
        "resolver_owner": item.get("resolver_owner", "NASR"),
        "authority": item.get("authority", "read-only"),
        "status": status,
        "target": target,
        "unit": item["unit"],
        "verified": verified,
        "remaining": remaining,
        "progress_delta": delta,
        "next_action": next_action,
        "blocker": blocker,
        "stale_deadline": stale_deadline.isoformat() if stale_deadline else None,
        "verified_close": {
            "achieved": status == "verified_closed",
            "gate": f"{target} unique strict-ledger submissions with proof and all campaign quality gates",
            "verified_at": now.isoformat() if status == "verified_closed" else None,
        },
        "evidence": {
            "source_of_truth": ledger_status.get("source_of_truth"),
            "ledger": item["ledger"],
            "supervisor_state": item["state_file"],
            "service": item["service"],
            "service_state": f"{service.get('ActiveState')}/{service.get('SubState')}",
            "service_result": service.get("Result"),
            "main_pid": int(main_pid or 0),
            "supervisor_pid": int(supervisor_pid or 0),
            "heartbeat_at": supervisor.get("heartbeat_at"),
            "heartbeat_age_seconds": heartbeat_age,
            "supervisor_reason": reason or None,
            "strict_exclusions": len(ledger_status.get("exclusions", [])),
            "issues": evidence_issues,
            "notes": evidence_notes,
        },
    }


def blocked_item(item: dict[str, Any], reason: str, now: datetime) -> dict[str, Any]:
    return {
        "id": item.get("id", "unknown"),
        "title": item.get("title", "Unknown outcome"),
        "owner": item.get("owner", "unknown"),
        "resolver_owner": item.get("resolver_owner", "NASR"),
        "authority": item.get("authority", "read-only"),
        "status": "blocked",
        "target": item.get("target"),
        "unit": item.get("unit"),
        "verified": None,
        "remaining": None,
        "progress_delta": 0,
        "next_action": "Restore read access to canonical evidence; do not infer progress from narrative reports.",
        "blocker": reason,
        "stale_deadline": now.isoformat(),
        "verified_close": {"achieved": False, "gate": None, "verified_at": None},
        "evidence": {"issues": [reason]},
    }


def resolve_item(
    item: dict[str, Any], now: datetime, previous: dict[str, Any] | None
) -> dict[str, Any]:
    if item.get("adapter") != "linkedin_plus30":
        raise ResolverError(f"unsupported adapter: {item.get('adapter')}")
    supervisor = load_json(Path(item["state_file"]))
    ledger_status = run_json(
        [
            "/usr/bin/python3",
            item["status_script"],
            "--date",
            item["date"],
            "--target",
            str(item["target"]),
            "--ledger",
            item["ledger"],
        ]
    )
    service = systemd_state(item["service"])
    return evaluate_linkedin_plus30(item, supervisor, ledger_status, service, now, previous)


def build_briefing(snapshot: dict[str, Any]) -> dict[str, Any]:
    briefing = {
        "generated_at": snapshot["generated_at"],
        "progress": [],
        "intervention": [],
        "closures": [],
    }
    for item in snapshot["items"]:
        card = {
            "id": item["id"],
            "owner": item["owner"],
            "title": item["title"],
            "status": item["status"],
            "progress": f"{item.get('verified')}/{item.get('target')}",
            "delta": item.get("progress_delta", 0),
            "next_action": item["next_action"],
            "blocker": item.get("blocker"),
        }
        if item["status"] == "verified_closed":
            briefing["closures"].append(card)
        elif item["status"] in {"blocked", "intervention_required", "approval_required"}:
            briefing["intervention"].append(card)
        else:
            briefing["progress"].append(card)
    return briefing


def render_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# Open-Work Resolver",
        "",
        f"Generated: {snapshot['generated_at']}",
        "",
    ]
    for item in snapshot["items"]:
        lines.extend(
            [
                f"## {item['title']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Owner: {item['owner']} (Resolver: {item['resolver_owner']})",
                f"- Progress: {item.get('verified')}/{item.get('target')} {item.get('unit')}",
                f"- Next action: {item['next_action']}",
                f"- Blocker: {item.get('blocker') or 'None'}",
                f"- Stale deadline: {item.get('stale_deadline') or 'Unavailable'}",
                f"- Verified close: {'yes' if item['verified_close']['achieved'] else 'no'}",
                f"- Evidence: {item.get('evidence', {}).get('source_of_truth') or 'unavailable'}; "
                f"service {item.get('evidence', {}).get('service_state') or 'unavailable'}; "
                f"heartbeat age {item.get('evidence', {}).get('heartbeat_age_seconds')}s",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def meaningful_change(previous: dict[str, Any] | None, current: dict[str, Any]) -> bool:
    if previous is None:
        return True
    keys = ("status", "verified", "blocker")
    return any(previous.get(key) != current.get(key) for key in keys)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve persistent work from canonical evidence")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--now", help="ISO timestamp override for deterministic testing")
    parser.add_argument("--no-history", action="store_true")
    args = parser.parse_args()

    config = load_json(args.config)
    now = parse_timestamp(args.now) if args.now else datetime.now().astimezone()
    if now is None:
        raise SystemExit("invalid --now timestamp")

    snapshot_path = Path(config["snapshot_file"])
    try:
        old_snapshot = load_json(snapshot_path)
    except ResolverError:
        old_snapshot = {"items": []}

    resolved: list[dict[str, Any]] = []
    history_events: list[dict[str, Any]] = []
    for item in config.get("items", []):
        old_item = previous_item(old_snapshot, item["id"])
        try:
            current = resolve_item(item, now, old_item)
        except ResolverError as exc:
            current = blocked_item(item, str(exc), now)
        resolved.append(current)
        if meaningful_change(old_item, current):
            history_events.append(
                {
                    "timestamp": now.isoformat(),
                    "id": current["id"],
                    "status": current["status"],
                    "verified": current.get("verified"),
                    "target": current.get("target"),
                    "delta": current.get("progress_delta", 0),
                    "blocker": current.get("blocker"),
                }
            )

    snapshot = {
        "version": 1,
        "generated_at": now.isoformat(),
        "summary": {
            "tracked": len(resolved),
            "progress": sum(i["status"] in {"progress", "in_progress"} for i in resolved),
            "intervention": sum(
                i["status"] in {"blocked", "intervention_required", "approval_required"}
                for i in resolved
            ),
            "closures": sum(i["status"] == "verified_closed" for i in resolved),
        },
        "items": resolved,
    }
    briefing = build_briefing(snapshot)

    output_dir = Path(config["output_dir"])
    atomic_write(snapshot_path, json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    atomic_write(output_dir / "latest.json", json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    atomic_write(output_dir / "latest.md", render_markdown(snapshot))
    atomic_write(output_dir / "briefing.json", json.dumps(briefing, indent=2, ensure_ascii=False) + "\n")

    if history_events and not args.no_history:
        history_path = Path(config["history_file"])
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as handle:
            for event in history_events:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(json.dumps(snapshot, ensure_ascii=False))
    return 1 if snapshot["summary"]["intervention"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
