#!/usr/bin/env bash
set -euo pipefail

AGENT_FILTER=""
CONSECUTIVE_FILTER=1
OUTPUT_JSON=0

usage() {
  cat <<'USAGE'
Usage: scripts/nasr-cron-error-inspector.sh [--agent NAME] [--consecutive N] [--json]

Summarizes erroring cron jobs from `openclaw cron list --all --json` and adds
practical hints for this install, especially timeouts and context weight issues.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT_FILTER="${2:-}"
      shift 2
      ;;
    --consecutive)
      CONSECUTIVE_FILTER="${2:-1}"
      shift 2
      ;;
    --json)
      OUTPUT_JSON=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$CONSECUTIVE_FILTER" in
  ''|*[!0-9]*)
    printf 'Invalid --consecutive value: %s\n' "$CONSECUTIVE_FILTER" >&2
    exit 1
    ;;
esac

tmp_json="$(mktemp)"
trap 'rm -f "$tmp_json"' EXIT
openclaw cron list --all --json > "$tmp_json"

python3 - "$tmp_json" "$AGENT_FILTER" "$CONSECUTIVE_FILTER" "$OUTPUT_JSON" <<'PY'
import json
import sys
import time


def schedule_text(schedule):
    if not isinstance(schedule, dict):
        return "unknown"
    kind = schedule.get("kind")
    if kind == "cron":
        expr = schedule.get("expr", "?")
        tz = schedule.get("tz")
        return f"{expr} ({tz})" if tz else expr
    if kind == "every":
        every_ms = schedule.get("everyMs")
        if every_ms:
            if every_ms % 3_600_000 == 0:
                return f"every {every_ms // 3_600_000}h"
            if every_ms % 60_000 == 0:
                return f"every {every_ms // 60_000}m"
            return f"every {every_ms}ms"
    if kind == "at":
        return str(schedule.get("at") or "unknown")
    return kind or "unknown"


def human_age(last_run_ms):
    if not last_run_ms:
        return "never"
    try:
        delta = max(0, int(time.time() - (float(last_run_ms) / 1000.0)))
    except Exception:
        return "unknown"
    if delta < 60:
        return f"{delta}s"
    if delta < 3600:
        return f"{delta // 60}m"
    if delta < 86400:
        return f"{delta // 3600}h"
    return f"{delta // 86400}d"


def payload_preview(payload):
    if not isinstance(payload, dict):
        return ""
    bits = []
    if payload.get("kind"):
        bits.append(f"kind={payload['kind']}")
    if payload.get("model"):
        bits.append(f"model={payload['model']}")
    if "lightContext" in payload:
        bits.append(f"lightContext={payload['lightContext']}")
    if payload.get("timeoutSeconds"):
        bits.append(f"timeout={payload['timeoutSeconds']}s")
    message = payload.get("message")
    if message:
        text = str(message).replace("\n", " ").strip()
        if len(text) > 70:
            text = text[:70] + "..."
        bits.append(text)
    return " | ".join(bits)


def build_hints(job, payload, state):
    hints = []
    reason = state.get("lastErrorReason") or ""
    last_error = (state.get("lastError") or "").lower()
    timeout_seconds = payload.get("timeoutSeconds")
    duration_ms = state.get("lastDurationMs") or 0

    if reason == "timeout" or "timed out" in last_error:
        if payload.get("kind") == "agentTurn" and not payload.get("lightContext"):
            hints.append("Timeout + no lightContext, strong candidate for lighter context if judgment depth is not required.")
        if timeout_seconds and duration_ms >= int(timeout_seconds * 1000 * 0.95):
            hints.append("Run appears to be hitting the timeout ceiling, either simplify the job or raise timeoutSeconds.")
        elif not timeout_seconds:
            hints.append("Timeout error without explicit timeoutSeconds, inspect the inherited/default timeout.")

    if state.get("consecutiveErrors", 0) >= 3:
        hints.append("Three or more consecutive failures, escalate instead of waiting for passive recovery.")

    delivery_status = state.get("lastDeliveryStatus") or ""
    if delivery_status in {"error", "failed", "unknown"} and state.get("lastStatus") == "ok":
        hints.append("Execution may be fine but delivery is not, inspect channel routing rather than the task logic.")

    if not hints:
        hints.append("Inspect the payload and latest run logs directly, no deterministic fix pattern matched.")
    return hints


with open(sys.argv[1], "r", encoding="utf-8") as handle:
    raw = json.load(handle)

agent_filter = sys.argv[2]
consecutive_filter = int(sys.argv[3])
output_json = sys.argv[4] == "1"
jobs = raw if isinstance(raw, list) else raw.get("jobs", raw.get("crons", []))

rows = []
for job in jobs:
    if not isinstance(job, dict):
        continue
    agent = job.get("agentId") or "unknown"
    if agent_filter and agent != agent_filter:
        continue

    state = job.get("state") or {}
    payload = job.get("payload") or {}
    consecutive_errors = int(state.get("consecutiveErrors") or 0)
    last_status = state.get("lastStatus") or state.get("lastRunStatus") or ""
    if consecutive_filter > 1:
        if consecutive_errors < consecutive_filter:
            continue
    elif consecutive_errors <= 0 and last_status != "error":
        continue

    rows.append(
        {
            "id": job.get("id") or "",
            "name": job.get("name") or "(unnamed)",
            "agent": agent,
            "schedule": schedule_text(job.get("schedule")),
            "last_status": last_status or "unknown",
            "last_run_age": human_age(state.get("lastRunAtMs")),
            "consecutive_errors": consecutive_errors,
            "last_error_reason": state.get("lastErrorReason") or "(none)",
            "last_error": state.get("lastError") or "(none)",
            "payload_preview": payload_preview(payload),
            "hints": build_hints(job, payload, state),
        }
    )

rows.sort(key=lambda item: (-item["consecutive_errors"], item["agent"], item["name"], item["id"]))
payload = {"erroring_jobs": len(rows), "results": rows}

if output_json:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(0)

if not rows:
    target = f" for agent {agent_filter}" if agent_filter else ""
    print(f"No erroring cron jobs found{target} with consecutiveErrors >= {consecutive_filter}.")
    raise SystemExit(0)

print(f"Erroring cron jobs: {len(rows)}")
for item in rows:
    print(f"- {item['id']} | {item['name']}")
    print(f"  agent: {item['agent']}")
    print(f"  schedule: {item['schedule']}")
    print(f"  state: {item['last_status']} | consecutive={item['consecutive_errors']} | last-run-age={item['last_run_age']}")
    print(f"  lastErrorReason: {item['last_error_reason']}")
    print(f"  lastError: {item['last_error']}")
    print(f"  payload: {item['payload_preview'] or '(empty)'}")
    for hint in item["hints"]:
        print(f"  hint: {hint}")
    print("")
PY
