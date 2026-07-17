#!/usr/bin/env python3
"""Isolated tests for the Gmail push watcher's Telegram delivery ledger.

No Gmail, Telegram, gateway, or email-send command is executed.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "scripts" / "gmail-pubsub-pull-worker.py"


def load_worker():
    spec = importlib.util.spec_from_file_location("gmail_pubsub_worker_under_test", WORKER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


worker = load_worker()


def envelope(email_key: str, *, kind: str = "hiring_process_update") -> dict:
    action_required = kind == "action_required"
    return {
        "type": kind,
        "importance": "high",
        "action_required": action_required,
        "pipeline_matches": ["Sprinklr"],
        "email_keys": [email_key],
        "message": "🚨 Action required" if action_required else "📌 Hiring process update",
    }


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        ledger_path = Path(temp_dir) / "ledger.json"
        worker.LOG_PATH = Path(temp_dir) / "worker.log"

        created = worker.register_envelopes([envelope("id:364923")], ledger_path=ledger_path)
        ledger = worker.load_ledger(ledger_path)
        entries = ledger["entries"]
        if created != 1 or len(entries) != 1 or next(iter(entries.values()))["status"] != "pending":
            failures.append("register_envelopes did not persist one pending alert")

        commands: list[list[str]] = []

        def success_runner(cmd: list[str], *, timeout: int):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({"messageId": "test-1", "payload": {"ok": True, "messageId": "test-1"}}),
                stderr="",
            )

        outcome = worker.deliver_pending_alerts(ledger_path=ledger_path, runner=success_runner)
        delivered_entry = next(iter(worker.load_ledger(ledger_path)["entries"].values()))
        if outcome != {"attempted": 1, "delivered": 1, "failed": 0}:
            failures.append(f"successful delivery outcome incorrect: {outcome}")
        if delivered_entry.get("status") != "delivered" or delivered_entry.get("message_id") != "test-1":
            failures.append("successful receipt did not mark ledger entry delivered")
        if not commands or commands[0][:6] != [
            "/usr/bin/openclaw", "message", "send", "--channel", "telegram", "--target",
        ]:
            failures.append(f"delivery command was not Telegram-only: {commands}")

        duplicate = worker.register_envelopes([envelope("id:364923")], ledger_path=ledger_path)
        if duplicate != 0 or len(worker.load_ledger(ledger_path)["entries"]) != 1:
            failures.append("delivered alert was not deduplicated")

        multi = envelope("id:multi")
        multi["email_keys"] = [f"id:{number}" for number in range(10)]
        worker.register_envelopes([multi], ledger_path=ledger_path)
        multi_entry = next(
            entry for entry in worker.load_ledger(ledger_path)["entries"].values()
            if "id:9" in entry.get("email_keys", [])
        )
        if len(multi_entry.get("email_keys") or []) != 10:
            failures.append("ledger did not preserve every email key in a batch")
        worker.deliver_pending_alerts(ledger_path=ledger_path, runner=success_runner)

        worker.register_envelopes([envelope("id:364924", kind="action_required")], ledger_path=ledger_path)

        def failure_runner(cmd: list[str], *, timeout: int):
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="temporary Telegram failure")

        failed = worker.deliver_pending_alerts(ledger_path=ledger_path, runner=failure_runner)
        pending = [entry for entry in worker.load_ledger(ledger_path)["entries"].values() if entry["status"] == "pending"]
        if failed["failed"] != 1 or len(pending) != 1 or pending[0].get("attempts") != 1:
            failures.append("failed delivery was not preserved as pending")

        retry_ledger = worker.load_ledger(ledger_path)
        for entry in retry_ledger["entries"].values():
            if entry["status"] == "pending":
                entry["next_retry_at_epoch"] = 0
        worker.save_ledger(retry_ledger, ledger_path)
        recovered = worker.deliver_pending_alerts(ledger_path=ledger_path, runner=success_runner)
        if recovered["delivered"] != 1:
            failures.append(f"pending alert did not recover on retry: {recovered}")

        worker.register_envelopes([envelope("id:364925")], ledger_path=ledger_path)

        def incomplete_receipt_runner(cmd: list[str], *, timeout: int):
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"payload": {"ok": True}}), stderr="")

        incomplete = worker.deliver_pending_alerts(ledger_path=ledger_path, runner=incomplete_receipt_runner)
        if incomplete["failed"] != 1:
            failures.append("receipt without messageId was incorrectly accepted")

    source = WORKER_PATH.read_text(encoding="utf-8").lower()
    forbidden_commands = (
        "himalaya message reply",
        "himalaya message write",
        "himalaya template send",
        "himalaya message forward",
        "smtplib",
    )
    found = [command for command in forbidden_commands if command in source]
    if found:
        failures.append(f"worker contains forbidden email-send capability: {found}")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS: Gmail Pub/Sub worker delivery ledger")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
