#!/usr/bin/env python3
"""Send one local media artifact to Telegram with an idempotent proof receipt."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_CLI = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"
ALLOWED_ROOT = Path("/root/.openclaw/media").resolve()
RECEIPT_DIR = Path("/root/.openclaw/state/media-delivery-receipts")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_result(raw: str) -> tuple[bool, str | None, dict]:
    decoder = json.JSONDecoder()
    payload = None
    for index, character in enumerate(raw):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(raw[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            payload = candidate
    if payload is None:
        raise ValueError("no JSON object found in delivery response")
    inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
    ok = bool(inner.get("ok"))
    message_id = inner.get("messageId") or payload.get("messageId")
    return ok and bool(message_id), str(message_id) if message_id else None, payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--receipt-key", required=True, help="Stable per-request idempotency key, such as Telegram inbound message ID.")
    parser.add_argument("--caption", default="")
    parser.add_argument("--reply-to")
    parser.add_argument("--force", action="store_true", help="Resend even if this receipt key already succeeded.")
    args = parser.parse_args()

    media = Path(args.media).resolve()
    if not media.is_file():
        print(json.dumps({"ok": False, "error": "media_missing", "media": str(media)}))
        return 2
    if ALLOWED_ROOT not in media.parents:
        print(json.dumps({"ok": False, "error": "media_outside_allowed_root", "allowed_root": str(ALLOWED_ROOT)}))
        return 2

    safe_key = hashlib.sha256(args.receipt_key.encode("utf-8")).hexdigest()
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    receipt_path = RECEIPT_DIR / f"{safe_key}.json"
    if receipt_path.is_file() and not args.force:
        existing = json.loads(receipt_path.read_text())
        if existing.get("ok") and existing.get("message_id"):
            print(json.dumps({**existing, "duplicate_prevented": True}, ensure_ascii=False))
            return 0

    cli = os.environ.get("OPENCLAW_MEDIA_CLI", DEFAULT_CLI)
    command = [cli, "message", "send", "--channel", "telegram", "--target", args.target, "--media", str(media), "--json"]
    if args.caption:
        command.extend(["--message", args.caption])
    if args.reply_to:
        command.extend(["--reply-to", args.reply_to])

    completed = subprocess.run(command, text=True, capture_output=True, timeout=90, check=False)
    try:
        success, message_id, response = parse_result(completed.stdout)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": "invalid_delivery_response", "detail": str(exc), "stderr": completed.stderr[-1000:]}))
        return 3

    verified = success and completed.returncode == 0
    receipt = {
        "ok": verified,
        "message_id": message_id,
        "target": args.target,
        "media": str(media),
        "sha256": sha256(media),
        "receipt_key": args.receipt_key,
        "sent_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "exit_code": completed.returncode,
        "response": response,
    }
    if verified:
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(receipt, ensure_ascii=False))
        return 0

    print(json.dumps(receipt, ensure_ascii=False))
    return 4


if __name__ == "__main__":
    sys.exit(main())
