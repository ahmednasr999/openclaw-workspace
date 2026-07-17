#!/usr/bin/env python3
"""Private Gmail Pub/Sub pull worker with durable Telegram alert delivery.

The worker keeps Gmail push private: it pulls from Google Pub/Sub locally,
runs the existing body-aware email classifier, and sends only structured
action-required or hiring-process-update alerts to Ahmed on Telegram.

This worker has no email compose, reply, forward, SMTP, or send path. Scheduled
IMAP polling remains the fallback retrieval path.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path("/root/.openclaw/workspace")
SUBSCRIPTION = "projects/openclaw-ahmed/subscriptions/gog-gmail-watch-pull"
TARGET = "866838380"
STATE_PATH = ROOT / "data" / "gmail-pubsub-pull-state.json"
LOG_PATH = ROOT / "logs" / "gmail-pubsub-pull.log"
LEDGER_PATH = ROOT / "data" / "email-alert-delivery-ledger.json"
POLL_INTERVAL_SECONDS = 5
FETCH_DELAY_SECONDS = 4
MAX_LEDGER_ENTRIES = 500
MAX_RETRY_SECONDS = 300


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def log(event: str, **fields: Any) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": now_iso(), "event": event, **fields}
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_state(**fields: Any) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"updated_at": now_iso(), **fields}
    STATE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"delivery ledger is unreadable: {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("entries"), dict):
        raise RuntimeError(f"delivery ledger has invalid structure: {path}")
    data["version"] = 1
    return data


def save_ledger(ledger: dict[str, Any], path: Path = LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = ledger.setdefault("entries", {})
    delivered = sorted(
        ((key, value) for key, value in entries.items() if value.get("status") == "delivered"),
        key=lambda pair: pair[1].get("delivered_at") or pair[1].get("created_at") or "",
        reverse=True,
    )
    keep_delivered = {key for key, _ in delivered[:MAX_LEDGER_ENTRIES]}
    ledger["entries"] = {
        key: value
        for key, value in entries.items()
        if value.get("status") != "delivered" or key in keep_delivered
    }
    ledger["updated_at"] = now_iso()
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp_path.replace(path)


def ledger_counts(path: Path = LEDGER_PATH) -> dict[str, int]:
    entries = load_ledger(path).get("entries", {})
    return {
        "pending_alerts": sum(1 for entry in entries.values() if entry.get("status") != "delivered"),
        "delivered_alerts": sum(1 for entry in entries.values() if entry.get("status") == "delivered"),
    }


def run(cmd: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)


def alert_id(envelope: dict[str, Any]) -> str:
    material = {
        "type": envelope.get("type"),
        "email_keys": sorted(str(key) for key in envelope.get("email_keys") or []),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:32]


def register_envelopes(
    envelopes: list[dict[str, Any]],
    *,
    ledger_path: Path = LEDGER_PATH,
) -> int:
    """Persist not-yet-delivered alerts before any Telegram delivery attempt."""
    ledger = load_ledger(ledger_path)
    entries = ledger.setdefault("entries", {})
    created = 0
    for envelope in envelopes:
        if envelope.get("type") not in {"action_required", "hiring_process_update"}:
            continue
        if envelope.get("importance") not in {"critical", "high"}:
            continue
        if not envelope.get("email_keys") or not str(envelope.get("message") or "").strip():
            continue
        key = alert_id(envelope)
        existing = entries.get(key)
        if existing and existing.get("status") == "delivered":
            continue
        now = now_iso()
        if existing:
            existing.update({
                "message": envelope["message"],
                "importance": envelope.get("importance"),
                "action_required": bool(envelope.get("action_required")),
                "pipeline_matches": envelope.get("pipeline_matches") or [],
                "email_keys": envelope.get("email_keys") or [],
                "updated_at": now,
            })
            existing["status"] = "pending"
        else:
            entries[key] = {
                "id": key,
                "type": envelope["type"],
                "importance": envelope.get("importance"),
                "action_required": bool(envelope.get("action_required")),
                "pipeline_matches": envelope.get("pipeline_matches") or [],
                "email_keys": envelope.get("email_keys") or [],
                "message": envelope["message"],
                "status": "pending",
                "attempts": 0,
                "next_retry_at_epoch": 0,
                "created_at": now,
                "updated_at": now,
            }
            created += 1
    save_ledger(ledger, ledger_path)
    return created


def parse_delivery_receipt(proc: subprocess.CompletedProcess[str]) -> tuple[bool, dict[str, Any], str]:
    if proc.returncode != 0:
        return False, {}, (proc.stderr or proc.stdout or "Telegram delivery command failed").strip()[-1200:]
    try:
        receipt = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return False, {}, "Telegram delivery returned non-JSON output"
    payload = receipt.get("payload") if isinstance(receipt.get("payload"), dict) else {}
    ok = payload.get("ok") is True
    message_id = receipt.get("messageId") or payload.get("messageId")
    if not ok or not str(message_id or "").strip():
        return False, receipt, "Telegram delivery receipt missing ok=true or messageId"
    return True, receipt, ""


def deliver_pending_alerts(
    *,
    ledger_path: Path = LEDGER_PATH,
    runner=run,
) -> dict[str, int]:
    ledger = load_ledger(ledger_path)
    entries = ledger.get("entries", {})
    attempted = delivered = failed = 0
    now_epoch = time.time()

    for key, entry in list(entries.items()):
        if entry.get("status") == "delivered":
            continue
        if float(entry.get("next_retry_at_epoch") or 0) > now_epoch:
            continue
        attempted += 1
        entry["status"] = "in_flight"
        entry["attempts"] = int(entry.get("attempts") or 0) + 1
        entry["last_attempt_at"] = now_iso()
        retry_delay = min(MAX_RETRY_SECONDS, 15 * (2 ** min(entry["attempts"] - 1, 5)))
        entry["next_retry_at_epoch"] = now_epoch + retry_delay
        save_ledger(ledger, ledger_path)

        try:
            proc = runner([
                "/usr/bin/openclaw", "message", "send", "--channel", "telegram",
                "--target", TARGET, "--message", entry["message"], "--json",
            ], timeout=60)
            ok, receipt, error = parse_delivery_receipt(proc)
        except Exception as exc:
            ok, receipt, error = False, {}, str(exc)

        if ok:
            message_id = receipt.get("messageId") or (receipt.get("payload") or {}).get("messageId")
            entry.update({
                "status": "delivered",
                "delivered_at": now_iso(),
                "message_id": str(message_id),
                "next_retry_at_epoch": 0,
                "last_error": None,
            })
            delivered += 1
            log("alert_delivered", alert_id=key, alert_type=entry.get("type"), message_id=str(message_id))
        else:
            entry["status"] = "pending"
            entry["last_error"] = error[-1200:]
            failed += 1
            log("delivery_failed", alert_id=key, alert_type=entry.get("type"), error=error[-1200:])
        entry["updated_at"] = now_iso()
        save_ledger(ledger, ledger_path)

    return {"attempted": attempted, "delivered": delivered, "failed": failed}


def pull() -> list[dict[str, Any]]:
    proc = run([
        "/usr/local/bin/gcloud", "pubsub", "subscriptions", "pull", SUBSCRIPTION,
        "--limit=20", "--auto-ack", "--format=json", "--quiet",
    ], timeout=45)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "gcloud pull failed").strip())
    data = json.loads(proc.stdout or "[]")
    return data if isinstance(data, list) else []


def load_delivery_plan() -> dict[str, Any]:
    formatter = run([
        "/usr/bin/python3", str(ROOT / "scripts" / "format-email-alert.py"),
        "--input", str(ROOT / "data" / "email-summary.json"),
        "--output", "json",
    ], timeout=30)
    if formatter.returncode != 0:
        raise RuntimeError((formatter.stderr or formatter.stdout or "formatter failed").strip()[-1200:])
    try:
        delivery_plan = json.loads(formatter.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"formatter returned invalid JSON: {exc}") from exc
    envelopes = delivery_plan.get("envelopes") if isinstance(delivery_plan, dict) else None
    if not isinstance(envelopes, list):
        raise RuntimeError("formatter JSON missing envelopes list")
    return delivery_plan


def reconcile_latest_summary() -> int:
    """Recover a classified alert if the worker stopped before ledger registration."""
    summary_path = ROOT / "data" / "email-summary.json"
    if not summary_path.exists():
        return 0
    delivery_plan = load_delivery_plan()
    return register_envelopes(delivery_plan["envelopes"])


def scan_and_alert(notification_count: int) -> None:
    time.sleep(FETCH_DELAY_SECONDS)
    scan = run(["/usr/bin/python3", str(ROOT / "scripts" / "email-agent-gated.py")], timeout=300)
    full_run = "email gate: running full agent" in scan.stdout
    if scan.returncode != 0:
        log("scan_failed", returncode=scan.returncode, stderr=scan.stderr[-1200:])
        save_state(status="scan_failed", notification_count=notification_count)
        return
    if not full_run:
        log("scan_skipped", notification_count=notification_count)
        save_state(status="healthy", last_event="scan_skipped", notification_count=notification_count)
        return

    try:
        delivery_plan = load_delivery_plan()
        envelopes = delivery_plan["envelopes"]
    except RuntimeError as exc:
        log("formatter_invalid", error=str(exc))
        save_state(status="formatter_invalid", notification_count=notification_count)
        return

    created = register_envelopes(envelopes)
    if not envelopes:
        log("no_notifiable_alert", notification_count=notification_count)
    outcome = deliver_pending_alerts()
    counts = ledger_counts()
    if outcome["failed"]:
        save_state(
            status="delivery_pending",
            last_event="delivery_failed",
            notification_count=notification_count,
            registered_alerts=created,
            **counts,
        )
        return
    event = "alerts_delivered" if outcome["delivered"] else "no_notifiable_alert"
    save_state(
        status="healthy",
        last_event=event,
        notification_count=notification_count,
        registered_alerts=created,
        delivered_now=outcome["delivered"],
        **counts,
    )


def main() -> int:
    log("worker_started", subscription=SUBSCRIPTION)
    save_state(status="starting", subscription=SUBSCRIPTION)
    consecutive_errors = 0
    last_idle_state = 0.0
    try:
        recovered = reconcile_latest_summary()
        if recovered:
            log("summary_reconciled", registered_alerts=recovered)
        deliver_pending_alerts()
    except Exception as exc:
        log("startup_recovery_failed", error=str(exc))
        save_state(status="recovery_error", error=str(exc))
    while True:
        try:
            messages = pull()
            consecutive_errors = 0
            if messages:
                log("notifications_received", count=len(messages))
                scan_and_alert(len(messages))
            else:
                if time.monotonic() - last_idle_state >= 60:
                    reconciled = reconcile_latest_summary()
                    if reconciled:
                        log("summary_reconciled", registered_alerts=reconciled)
                retry_outcome = deliver_pending_alerts()
                if retry_outcome["failed"]:
                    save_state(status="delivery_pending", last_event="delivery_retry_failed", **ledger_counts())
                elif retry_outcome["delivered"]:
                    save_state(status="healthy", last_event="delivery_recovered", **ledger_counts())
                elif time.monotonic() - last_idle_state >= 60:
                    save_state(status="healthy", last_event="idle", subscription=SUBSCRIPTION, **ledger_counts())
                    last_idle_state = time.monotonic()
        except Exception as exc:
            consecutive_errors += 1
            log("worker_error", error=str(exc), consecutive_errors=consecutive_errors)
            save_state(status="error", error=str(exc), consecutive_errors=consecutive_errors)
            time.sleep(min(60, 5 * consecutive_errors))
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
