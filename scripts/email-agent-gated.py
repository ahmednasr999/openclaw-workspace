#!/usr/bin/env python3
"""Conservative gate for frequent scheduled email-agent runs.

Skips the full email agent only when the INBOX is clearly unchanged:
- prior email state exists
- prior gate checkpoint exists
- prior email summary exists and is healthy
- mailbox metadata is unchanged since the checkpoint
- there are no unread INBOX messages

Any missing state, parse issue, or IMAP error fails open and runs email-agent.py.
"""

from __future__ import annotations

import copy
import imaplib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE / "data"
CONFIG_PATH = WORKSPACE / "config" / "gmail-imap.json"
EMAIL_AGENT_PATH = Path(__file__).with_name("email-agent.py")

STATE_PATH = DATA_DIR / "email-state.json"
GATE_STATE_PATH = DATA_DIR / "email-gate-state.json"
SUMMARY_PATH = DATA_DIR / "email-summary.json"
LATEST_PATH = DATA_DIR / "email-latest.json"

STATUS_FIELDS = ("MESSAGES", "UNSEEN", "UIDNEXT", "UIDVALIDITY")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def load_imap_config() -> dict[str, Any]:
    cfg = load_json(CONFIG_PATH)
    if not cfg:
        raise RuntimeError(f"missing or invalid config: {CONFIG_PATH}")
    user = cfg.get("user")
    password = cfg.get("app_password")
    if not user or not password:
        raise RuntimeError("gmail-imap.json missing user/app_password")
    return {
        "user": user,
        "password": password,
        "host": cfg.get("imap_host", "imap.gmail.com"),
        "port": int(cfg.get("imap_port", 993)),
    }


def parse_status_blob(blob: bytes | str) -> dict[str, int]:
    text = blob.decode(errors="replace") if isinstance(blob, bytes) else str(blob)
    parsed: dict[str, int] = {}
    for field in STATUS_FIELDS:
        match = re.search(rf"{field}\s+(\d+)", text)
        if not match:
            raise RuntimeError(f"unable to parse {field} from IMAP STATUS: {text}")
        parsed[field.lower()] = int(match.group(1))
    return parsed


def fetch_mailbox_status() -> dict[str, int]:
    cfg = load_imap_config()
    mail = imaplib.IMAP4_SSL(cfg["host"], cfg["port"])
    try:
        mail.login(cfg["user"], cfg["password"])
        status, data = mail.status("INBOX", "(MESSAGES UNSEEN UIDNEXT UIDVALIDITY)")
        if status != "OK" or not data:
            raise RuntimeError(f"IMAP STATUS failed: {status} {data!r}")
        parsed = parse_status_blob(data[0])
        return {
            "messages": parsed["messages"],
            "unseen": parsed["unseen"],
            "uidnext": parsed["uidnext"],
            "uidvalidity": parsed["uidvalidity"],
        }
    finally:
        try:
            mail.logout()
        except Exception:
            pass


def decide_gate(
    mailbox: dict[str, int] | None,
    email_state: dict[str, Any] | None,
    gate_state: dict[str, Any] | None,
    summary: dict[str, Any] | None,
    latest: dict[str, Any] | None,
) -> tuple[bool, str]:
    if mailbox is None:
        return False, "mailbox status unavailable"
    if not email_state:
        return False, "email state missing"
    last_seen_uid = int(email_state.get("last_seen_uid", 0) or 0)
    if last_seen_uid <= 0 or not email_state.get("last_success"):
        return False, "email state incomplete"
    if not gate_state:
        return False, "gate checkpoint missing"
    if not summary:
        return False, "email summary missing"
    meta = summary.get("meta") if isinstance(summary.get("meta"), dict) else {}
    if meta.get("status") not in (None, "success"):
        return False, "last email summary not successful"
    if latest and latest.get("status") == "error":
        return False, "latest email snapshot is error state"
    if mailbox.get("uidvalidity") != gate_state.get("uidvalidity"):
        return False, "uidvalidity changed"
    if mailbox.get("uidnext") != gate_state.get("uidnext"):
        return False, "uidnext changed"
    if mailbox.get("messages") != gate_state.get("messages"):
        return False, "message count changed"
    if mailbox.get("unseen", 0) != 0:
        return False, "unread inbox mail present"
    if mailbox.get("uidnext") != last_seen_uid + 1:
        return False, "last_seen_uid no longer matches mailbox head"
    return True, "mailbox metadata unchanged and no unread inbox mail"


def build_gate_payload(reason: str, mailbox: dict[str, int], email_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "skipped",
        "reason": reason,
        "checked_at": now_iso(),
        "mailbox": mailbox,
        "last_full_success": email_state.get("last_success"),
        "last_seen_uid": email_state.get("last_seen_uid"),
    }


def write_skip_outputs(summary: dict[str, Any], latest: dict[str, Any] | None, gate_payload: dict[str, Any], duration_ms: int) -> None:
    updated_summary = copy.deepcopy(summary)
    meta = updated_summary.setdefault("meta", {})
    meta["generated_at"] = gate_payload["checked_at"]
    meta["duration_ms"] = duration_ms
    meta["status"] = "success"
    meta["error"] = None
    meta["run_id"] = f"gate-{int(time.time())}"
    meta["gate"] = gate_payload

    data = updated_summary.setdefault("data", {})
    if isinstance(data, dict):
        data["gate"] = gate_payload

    updated_latest = copy.deepcopy(latest if isinstance(latest, dict) else data)
    if not isinstance(updated_latest, dict):
        updated_latest = {}
    updated_latest["gate"] = gate_payload

    save_json(SUMMARY_PATH, updated_summary)
    save_json(LATEST_PATH, updated_latest)


def save_gate_checkpoint(mailbox: dict[str, int], email_state: dict[str, Any] | None, decision: str, reason: str) -> None:
    payload = dict(mailbox)
    payload.update({
        "checked_at": now_iso(),
        "decision": decision,
        "reason": reason,
        "last_seen_uid": (email_state or {}).get("last_seen_uid"),
        "last_email_success": (email_state or {}).get("last_success"),
    })
    save_json(GATE_STATE_PATH, payload)


def run_full_agent(args: list[str], reason: str) -> int:
    print(f"email gate: running full agent ({reason})")
    proc = subprocess.run([sys.executable, str(EMAIL_AGENT_PATH), *args])
    return proc.returncode


def main() -> int:
    args = sys.argv[1:]
    if "--dry-run" in args:
        return run_full_agent(args, "dry-run bypass")

    started = time.monotonic()
    email_state = load_json(STATE_PATH)
    gate_state = load_json(GATE_STATE_PATH)
    summary = load_json(SUMMARY_PATH)
    latest = load_json(LATEST_PATH)

    try:
        mailbox = fetch_mailbox_status()
    except Exception as exc:
        return run_full_agent(args, f"fail-open on mailbox check error: {exc}")

    should_skip, reason = decide_gate(mailbox, email_state, gate_state, summary, latest)
    if should_skip:
        gate_payload = build_gate_payload(reason, mailbox, email_state or {})
        duration_ms = int((time.monotonic() - started) * 1000)
        try:
            write_skip_outputs(summary or {}, latest, gate_payload, duration_ms)
            save_gate_checkpoint(mailbox, email_state, "skip", reason)
        except Exception as exc:
            return run_full_agent(args, f"fail-open on skip snapshot error: {exc}")
        print(f"email gate: skipped full agent ({reason})")
        return 0

    code = run_full_agent(args, reason)
    if code == 0:
        refreshed_state = load_json(STATE_PATH) or email_state
        try:
            post_mailbox = fetch_mailbox_status()
        except Exception:
            post_mailbox = mailbox
        try:
            save_gate_checkpoint(post_mailbox, refreshed_state, "run", reason)
        except Exception as exc:
            print(f"email gate: warning, could not update checkpoint: {exc}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
