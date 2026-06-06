#!/usr/bin/env python3
"""Deterministic OS-cron runners for workflows that used to rely on agent exec."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path("/root/.openclaw/workspace")
CMO_ROOT = Path("/root/.openclaw/workspace-cmo")
LOG_DIR = ROOT / "logs" / "cron" / "direct-cron"
LOCK_DIR = Path("/var/lock/openclaw")
CAIRO = ZoneInfo("Africa/Cairo")

CEO_GROUP = "-1003882622947"
TOPIC_CEO = "10"
TOPIC_CMO = "7"
TOPIC_CTO = "8"
AHMED_DM = "866838380"

APPROVED_BATCH_START = date.fromisoformat("2026-05-15")


def now() -> datetime:
    return datetime.now(CAIRO)


def send_telegram(message: str, *, target: str, thread_id: str | None = None, presentation: dict | None = None, no_send: bool = False) -> dict:
    if no_send:
        return {"ok": True, "dry_run": True, "target": target, "thread_id": thread_id, "presentation": bool(presentation)}
    cmd = [
        "openclaw",
        "message",
        "send",
        "--channel",
        "telegram",
        "--target",
        target,
        "--message",
        message,
        "--json",
    ]
    if thread_id:
        cmd.extend(["--thread-id", thread_id])
    if presentation:
        cmd.extend(["--presentation", json.dumps(presentation, ensure_ascii=False)])

    last_result = {
        "ok": False,
        "returncode": None,
        "stdout": "",
        "stderr": "not attempted",
        "target": target,
        "thread_id": thread_id,
    }
    for attempt in range(1, 4):
        try:
            proc = subprocess.run(cmd, text=True, capture_output=True, timeout=45)
            last_result = {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
                "target": target,
                "thread_id": thread_id,
                "attempt": attempt,
            }
        except subprocess.TimeoutExpired as exc:
            last_result = {
                "ok": False,
                "returncode": 124,
                "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
                "stderr": f"Telegram delivery timed out after {exc.timeout}s",
                "target": target,
                "thread_id": thread_id,
                "attempt": attempt,
            }
        except Exception as exc:
            last_result = {
                "ok": False,
                "returncode": None,
                "stdout": "",
                "stderr": f"Telegram delivery exception: {exc}",
                "target": target,
                "thread_id": thread_id,
                "attempt": attempt,
            }

        if last_result["ok"]:
            return last_result
        if attempt < 3:
            time.sleep(2 * attempt)
    return last_result


def run_command(task: str, cmd: list[str], *, cwd: Path, timeout: int, env: dict[str, str] | None = None) -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{task}-{now():%Y%m%d-%H%M%S}.log"
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            env=merged_env,
        )
        result = {
            "task": task,
            "ts": now().isoformat(),
            "cmd": cmd,
            "cwd": str(cwd),
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "log_path": str(log_path),
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "task": task,
            "ts": now().isoformat(),
            "cmd": cmd,
            "cwd": str(cwd),
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + f"\nTimed out after {timeout}s",
            "log_path": str(log_path),
        }
    log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def with_lock(task: str):
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = LOCK_DIR / f"direct-cron-{task}.lock"
    fh = lock_path.open("w", encoding="utf-8")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(json.dumps({"ok": False, "task": task, "skipped": "lock_busy", "lock": str(lock_path)}))
        raise SystemExit(0)
    return fh


def parse_json_stdout(stdout: str) -> dict | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", text, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None


def weekly_self_health(args: argparse.Namespace) -> int:
    with with_lock("weekly-self-health"):
        result = run_command(
            "weekly-self-health",
            [sys.executable, "scripts/weekly-self-health-fast.py", "--write-report"],
            cwd=ROOT,
            timeout=420,
        )
        stdout = result["stdout"].strip()
        if result["returncode"] == 0 and stdout:
            delivery = send_telegram(stdout, target=CEO_GROUP, thread_id=TOPIC_CEO, no_send=args.no_send)
        else:
            body = (
                "Weekly self-health failed.\n"
                f"Return code: {result['returncode']}\n"
                f"Log: {result['log_path']}\n"
                f"Error: {result['stderr'][-900:].strip() or 'no stderr'}"
            )
            delivery = send_telegram(body, target=CEO_GROUP, thread_id=TOPIC_CEO, no_send=args.no_send)
        print(json.dumps({"ok": result["returncode"] == 0 and delivery.get("ok"), "result": result, "delivery": delivery}, ensure_ascii=False))
        return 0 if result["returncode"] == 0 and delivery.get("ok") else 1


def disk_guard(args: argparse.Namespace) -> int:
    with with_lock("disk-guard"):
        env = {"DISK_GUARD_THRESHOLD": "101"} if args.validate else None
        result = run_command(
            "disk-guard",
            [str(ROOT / "scripts" / "vps-disk-guard.sh")],
            cwd=ROOT,
            timeout=900,
            env=env,
        )
        stdout = result["stdout"].strip()
        delivery = {"ok": True, "skipped": "ok_below_threshold"}
        if result["returncode"] != 0:
            body = (
                "Disk guard failed.\n"
                f"Return code: {result['returncode']}\n"
                f"Log: {result['log_path']}\n"
                f"Error: {result['stderr'][-900:].strip() or 'no stderr'}"
            )
            delivery = send_telegram(body, target=AHMED_DM, no_send=args.no_send)
        elif stdout.startswith("DISK_GUARD_TRIGGERED"):
            fields = dict(line.split("=", 1) for line in stdout.splitlines() if "=" in line)
            cleanup_log = fields.get("log", "")
            candidate_note = ""
            if cleanup_log and Path(cleanup_log).exists():
                cleanup_text = Path(cleanup_log).read_text(encoding="utf-8", errors="replace")
                if re.search(r"/root/(?:openclaw-backups|\\.openclaw/backups|openclaw-snapshot-)", cleanup_text):
                    candidate_note = "\nBackup/snapshot candidates were listed in the log. Pruning still needs explicit approval."
            body = (
                "Disk guard triggered.\n"
                f"Before: {fields.get('before', '?')}\n"
                f"After: {fields.get('after', '?')}\n"
                f"Threshold: {fields.get('threshold', '?')}\n"
                f"Log: {cleanup_log or result['log_path']}"
                f"{candidate_note}"
            )
            delivery = send_telegram(body, target=AHMED_DM, no_send=args.no_send)
        print(json.dumps({"ok": result["returncode"] == 0 and delivery.get("ok"), "result": result, "delivery": delivery}, ensure_ascii=False))
        return 0 if result["returncode"] == 0 and delivery.get("ok") else 1


def session_cleanup(args: argparse.Namespace) -> int:
    with with_lock("session-cleanup"):
        if args.validate:
            result = run_command(
                "session-cleanup-validate",
                ["bash", "-n", str(ROOT / "scripts" / "session-cleanup.sh")],
                cwd=ROOT,
                timeout=30,
            )
            print(json.dumps({"ok": result["returncode"] == 0, "validate": True, "result": result}, ensure_ascii=False))
            return 0 if result["returncode"] == 0 else 1
        result = run_command(
            "session-cleanup",
            ["bash", str(ROOT / "scripts" / "session-cleanup.sh")],
            cwd=ROOT,
            timeout=600,
        )
        stdout = result["stdout"].strip()
        delivery = {"ok": True, "skipped": "no_output"}
        if result["returncode"] == 0 and stdout:
            body = f"Session cleanup completed.\n{stdout}"
            delivery = send_telegram(body, target=CEO_GROUP, thread_id=TOPIC_CTO, no_send=args.no_send)
        elif result["returncode"] != 0:
            body = (
                "Session cleanup failed.\n"
                f"Return code: {result['returncode']}\n"
                f"Log: {result['log_path']}\n"
                f"Error: {result['stderr'][-900:].strip() or 'no stderr'}"
            )
            delivery = send_telegram(body, target=CEO_GROUP, thread_id=TOPIC_CTO, no_send=args.no_send)
        print(json.dumps({"ok": result["returncode"] == 0 and delivery.get("ok"), "result": result, "delivery": delivery}, ensure_ascii=False))
        return 0 if result["returncode"] == 0 and delivery.get("ok") else 1


def approved_batch_post(args: argparse.Namespace) -> int:
    with with_lock("approved-14day-post"):
        today = now().date()
        post_number = (today - APPROVED_BATCH_START).days + 1
        if args.validate:
            if post_number < 1 or post_number > 14:
                print(json.dumps({"ok": True, "validate": True, "skipped": "outside_window", "post_number": post_number}))
                return 0
            cmd = [
                sys.executable,
                "scripts/post_approved_14day_batch.py",
                "--post",
                str(post_number),
                "--date",
                today.isoformat(),
                "--dry-run",
            ]
            task_timeout = 120
        else:
            cmd = [sys.executable, "scripts/run_approved_14day_daily_post.py"]
            task_timeout = 900
        result = run_command("approved-14day-post", cmd, cwd=CMO_ROOT, timeout=task_timeout)
        data = parse_json_stdout(result["stdout"]) or {}
        delivery = {"ok": True, "skipped": "no_announcement_needed"}

        if args.validate:
            print(json.dumps({"ok": result["returncode"] == 0, "validate": True, "data": data, "result": result}, ensure_ascii=False))
            return 0 if result["returncode"] == 0 else 1

        if result["returncode"] == 0:
            record = data.get("posted") or data if data.get("already_posted") else data.get("existing_publish_success") or {}
            url = record.get("url") or record.get("post_url") or ""
            title = record.get("title") or "Approved LinkedIn post"
            status = "already posted" if data.get("already_posted") or data.get("skipped") else "posted"
            if url:
                body = f"LinkedIn approved batch {status}.\nTitle: {title}\nURL: {url}"
                delivery = send_telegram(body, target=CEO_GROUP, thread_id=TOPIC_CMO, no_send=args.no_send)
        else:
            body = (
                "LinkedIn approved batch publisher failed.\n"
                "The day was not marked skipped.\n"
                f"Log: {result['log_path']}\n"
                f"Error: {(result['stderr'] or result['stdout'])[-900:].strip() or 'no output'}"
            )
            delivery = send_telegram(body, target=CEO_GROUP, thread_id=TOPIC_CMO, no_send=args.no_send)

        print(json.dumps({"ok": result["returncode"] == 0 and delivery.get("ok"), "data": data, "result": result, "delivery": delivery}, ensure_ascii=False))
        return 0 if result["returncode"] == 0 and delivery.get("ok") else 1


def approved_batch_engagement(args: argparse.Namespace) -> int:
    with with_lock("approved-14day-engagement"):
        if args.validate:
            state_path = CMO_ROOT / "data" / "approved-14day-linkedin-posting-state.json"
            today = now().date()
            post_number = (today - APPROVED_BATCH_START).days + 1
            state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"posted": {}}
            rec = state.get("posted", {}).get(str(post_number), {})
            print(json.dumps({"ok": True, "validate": True, "post_number": post_number, "posted": bool(rec), "url": rec.get("url", "")}))
            return 0
        result = run_command(
            "approved-14day-engagement",
            [sys.executable, "scripts/send_approved_14day_engagement_alert.py"],
            cwd=CMO_ROOT,
            timeout=120,
        )
        data = parse_json_stdout(result["stdout"]) or {}
        delivery = {"ok": True, "skipped": "outside_window_or_no_output"}
        if result["returncode"] == 0 and data:
            if data.get("posted"):
                body = (
                    "LinkedIn engagement window is due now.\n"
                    f"Post {data.get('post_number')}: {data.get('url')}\n"
                    "Check comments and reactions."
                )
            else:
                body = (
                    "LinkedIn engagement reminder skipped.\n"
                    "Expected daily post was not found in the approved batch state. Check publishing log."
                )
            delivery = send_telegram(body, target=CEO_GROUP, thread_id=TOPIC_CMO, no_send=args.no_send)
        elif result["returncode"] != 0:
            body = (
                "LinkedIn engagement reminder check failed.\n"
                f"Log: {result['log_path']}\n"
                f"Error: {result['stderr'][-900:].strip() or 'no stderr'}"
            )
            delivery = send_telegram(body, target=CEO_GROUP, thread_id=TOPIC_CMO, no_send=args.no_send)
        print(json.dumps({"ok": result["returncode"] == 0 and delivery.get("ok"), "data": data, "result": result, "delivery": delivery}, ensure_ascii=False))
        return 0 if result["returncode"] == 0 and delivery.get("ok") else 1


def markdown_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return ""
    end = len(lines)
    for idx in range(start, len(lines)):
        if lines[idx].startswith("## ") or lines[idx].startswith("Needs ") or lines[idx].startswith("No approval"):
            end = idx
            break
    return "\n".join(line for line in lines[start:end] if line.strip()).strip()


def linkedin_radar_ready_count(report_path: str) -> int | None:
    if not report_path:
        return None
    path = Path(report_path)
    if not path.exists():
        return None
    report = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"^Ready for approval:\s*(\d+)\/", report, re.M)
    return int(match.group(1)) if match else None


def linkedin_radar_status_pack(report_path: str, status: str, posts: str, action_line: str) -> str:
    base = [f"Status: {status}", f"Candidate count: {posts}"]
    if not report_path:
        return "\n".join([*base, action_line])

    path = Path(report_path)
    if not path.exists():
        return "\n".join([*base, f"Report: {report_path}", action_line])

    report = path.read_text(encoding="utf-8", errors="ignore")
    operational = markdown_section(report, "## Operational Status")
    source = markdown_section(report, "## Candidate Source")
    candidates = markdown_section(report, "## Candidates")
    signals = markdown_section(report, "## Content Signals for Ahmed")
    angles = markdown_section(report, "## Post Angles to Consider")

    details = base[:]
    if operational:
        details.extend(["", "Operational status:", operational])
    if source:
        compact_source = [line for line in source.splitlines() if "URL coverage" in line or "fallback" in line]
        if compact_source:
            details.extend(["", "Source:", "\n".join(compact_source)])
    if candidates:
        details.extend(["", "Candidate details:", candidates])
        if status != "ok_ready_for_approval":
            details.append("Approval buttons remain locked until a candidate is marked ready.")
    if signals:
        details.extend(["", "Content signals:", signals])
    if angles:
        details.extend(["", "Post angles:", angles])
    details.extend(["", action_line, f"Report: {report_path}"])
    return "\n".join(details)


def load_linkedin_radar_cards(cards_path: str) -> dict | None:
    if not cards_path:
        return None
    path = Path(cards_path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def send_linkedin_radar_approval_cards(cards_path: str, *, no_send: bool) -> dict:
    data = load_linkedin_radar_cards(cards_path)
    if not data:
        return {"ok": False, "count": 0, "error": "missing_or_invalid_card_payload", "cards_path": cards_path}
    cards = [card for card in data.get("cards", []) if isinstance(card, dict) and card.get("approval_enabled")]
    deliveries = []
    for card in cards[:5]:
        text = str(card.get("telegram_text") or "").strip()
        presentation = card.get("presentation") if isinstance(card.get("presentation"), dict) else None
        if not text:
            continue
        deliveries.append(send_telegram(text, target=CEO_GROUP, thread_id=TOPIC_CMO, presentation=presentation, no_send=no_send))
    return {"ok": all(item.get("ok") for item in deliveries) if deliveries else True, "count": len(deliveries), "cards_path": cards_path, "deliveries": deliveries}

def linkedin_comment_radar(args: argparse.Namespace, slot: str) -> int:
    with with_lock(f"linkedin-comment-radar-{slot}"):
        label = f"{slot[:2]}:{slot[2:]}"
        result = run_command(
            f"linkedin-comment-radar-{slot}-validate" if args.validate else f"linkedin-comment-radar-{slot}",
            [sys.executable, "scripts/run_linkedin_comment_radar.py", "--slot", slot],
            cwd=CMO_ROOT,
            timeout=1500,
        )

        stdout = result["stdout"].strip()
        report_path = ""
        cards_path = ""
        posts = "?"
        status = "unknown"
        for line in stdout.splitlines():
            if line.startswith("/") and line.endswith(".md"):
                report_path = line.strip()
            if line.startswith("cards="):
                cards_path = line.split("=", 1)[1].strip()
            match = re.search(r"status=([^\s]+) posts=(\d+)", line)
            if match:
                status, posts = match.group(1), match.group(2)

        if args.validate:
            print(json.dumps({"ok": result["returncode"] == 0, "validate": True, "slot": slot, "status": status, "posts": posts, "report": report_path, "cards": cards_path, "result": result}, ensure_ascii=False))
            return 0 if result["returncode"] == 0 else 1

        ready_count = linkedin_radar_ready_count(report_path)
        if status == "ok_ready_for_approval":
            if ready_count is not None and ready_count < 5:
                action_line = f"Needs CMO: target is 5; only {ready_count} candidates are ready. Continue recovery unless Ahmed approves the partial pack."
            else:
                action_line = "Needs Ahmed: approve only candidates marked Ready."
        elif status == "needs_url_recovery":
            action_line = "Needs CMO: recover URLs before asking Ahmed to approve comments."
        elif status == "no_ready_candidates":
            action_line = "No approval requested: no candidates passed the quality gate."
        else:
            action_line = "Review the report before taking any LinkedIn action."

        if result["returncode"] == 0:
            status_pack = linkedin_radar_status_pack(report_path, status, posts, action_line)
            body = f"LinkedIn Comment Radar {label} completed.\n{status_pack}"
            card_payload = load_linkedin_radar_cards(cards_path) or {}
            summary_presentation = card_payload.get("summary_presentation") if isinstance(card_payload.get("summary_presentation"), dict) else None
            delivery = send_telegram(body, target=CEO_GROUP, thread_id=TOPIC_CMO, presentation=summary_presentation, no_send=args.no_send)
            if status == "ok_ready_for_approval":
                card_delivery = send_linkedin_radar_approval_cards(cards_path, no_send=args.no_send)
                delivery = {"ok": delivery.get("ok") and card_delivery.get("ok"), "summary": delivery, "cards": card_delivery}
        else:
            body = (
                f"LinkedIn Comment Radar {label} failed.\n"
                f"Return code: {result['returncode']}\n"
                f"Log: {result['log_path']}\n"
                f"Error: {(result['stderr'] or result['stdout'])[-900:].strip() or 'no output'}"
            )
            delivery = send_telegram(body, target=AHMED_DM, no_send=args.no_send)

        print(json.dumps({"ok": result["returncode"] == 0 and delivery.get("ok"), "slot": slot, "status": status, "posts": posts, "report": report_path, "cards": cards_path, "result": result, "delivery": delivery}, ensure_ascii=False))
        return 0 if result["returncode"] == 0 and delivery.get("ok") else 1


def linkedin_comment_radar_1100(args: argparse.Namespace) -> int:
    return linkedin_comment_radar(args, "1100")


def linkedin_comment_radar_1500(args: argparse.Namespace) -> int:
    return linkedin_comment_radar(args, "1500")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-send", action="store_true", help="Run without Telegram delivery.")
    parser.add_argument("--validate", action="store_true", help="Use a non-destructive validation path where available.")
    sub = parser.add_subparsers(dest="task", required=True)
    for name in ("weekly-self-health", "disk-guard", "session-cleanup", "approved-14day-post", "approved-14day-engagement", "linkedin-comment-radar-1100", "linkedin-comment-radar-1500"):
        sub.add_parser(name)
    args = parser.parse_args()

    handlers = {
        "weekly-self-health": weekly_self_health,
        "disk-guard": disk_guard,
        "session-cleanup": session_cleanup,
        "approved-14day-post": approved_batch_post,
        "approved-14day-engagement": approved_batch_engagement,
        "linkedin-comment-radar-1100": linkedin_comment_radar_1100,
        "linkedin-comment-radar-1500": linkedin_comment_radar_1500,
    }
    return handlers[args.task](args)


if __name__ == "__main__":
    raise SystemExit(main())
