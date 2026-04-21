#!/usr/bin/env bash
set -euo pipefail

AGENTS_DIR="${OPENCLAW_AGENTS_DIR:-$HOME/.openclaw/agents}"
AGENT_FILTER=""
LIMIT_SESSIONS=3
OUTPUT_JSON=0

usage() {
  cat <<'USAGE'
Usage: scripts/nasr-prompt-truncation-report.sh [--agent NAME] [--limit-sessions N] [--json]

Checks the most recent sessions per live agent and reports real bootstrap truncation
or near-limit warnings from systemPromptReport.bootstrapTruncation.

Defaults:
  --limit-sessions 3
  scans live local agents only, skips archived cleanup snapshots
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT_FILTER="${2:-}"
      shift 2
      ;;
    --limit-sessions)
      LIMIT_SESSIONS="${2:-3}"
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

case "$LIMIT_SESSIONS" in
  ''|*[!0-9]*)
    printf 'Invalid --limit-sessions value: %s\n' "$LIMIT_SESSIONS" >&2
    exit 1
    ;;
esac

python3 - "$AGENTS_DIR" "$AGENT_FILTER" "$LIMIT_SESSIONS" "$OUTPUT_JSON" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_ts(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        value = float(value)
        return value / 1000.0 if value > 10_000_000_000 else value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0.0
        try:
            number = float(text)
            return number / 1000.0 if number > 10_000_000_000 else number
        except ValueError:
            pass
        for candidate in (text, text.replace("Z", "+00:00")):
            try:
                dt = datetime.fromisoformat(candidate)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except ValueError:
                continue
    return 0.0


def iso_utc(value):
    ts = parse_ts(value)
    if not ts:
        return "unknown"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_session_items(payload):
    if isinstance(payload, dict):
        if payload.get("sessions") and isinstance(payload["sessions"], dict):
            return list(payload["sessions"].items())
        if all(isinstance(v, dict) for v in payload.values()):
            return list(payload.items())
    if isinstance(payload, list):
        return [(str(index), item) for index, item in enumerate(payload)]
    return []


def live_agent_dirs(base_dir: Path, agent_filter: str):
    if agent_filter:
        candidate = base_dir / agent_filter
        if (candidate / "sessions" / "sessions.json").exists():
            return [candidate]
        return []

    skips = ("_archived", "session-archive-", "session-cleanup-")
    dirs = []
    for child in sorted(base_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(skips) or child.name in skips:
            continue
        if (child / "sessions" / "sessions.json").exists():
            dirs.append(child)
    return dirs


def file_entries(value):
    if isinstance(value, list):
        entries = []
        for item in value:
            if isinstance(item, dict):
                path = item.get("path") or item.get("file") or item.get("name") or "unknown"
                entries.append(path)
            else:
                entries.append(str(item))
        return len(entries), entries
    if isinstance(value, int):
        return value, []
    if isinstance(value, dict):
        path = value.get("path") or value.get("file") or value.get("name")
        return (1, [path or "unknown"])
    if value in (None, False, "", 0):
        return 0, []
    return 1, [str(value)]


base_dir = Path(sys.argv[1]).expanduser()
agent_filter = sys.argv[2]
limit_sessions = int(sys.argv[3])
output_json = sys.argv[4] == "1"

agents = []
for agent_dir in live_agent_dirs(base_dir, agent_filter):
    sessions_path = agent_dir / "sessions" / "sessions.json"
    try:
        payload = json.loads(sessions_path.read_text(encoding="utf-8"))
    except Exception as exc:
        agents.append({"agent": agent_dir.name, "error": f"invalid sessions.json: {exc}"})
        continue

    records = []
    for key, session in normalize_session_items(payload):
        if not isinstance(session, dict):
            continue
        updated = (
            parse_ts(session.get("updatedAt"))
            or parse_ts(session.get("endedAt"))
            or parse_ts(session.get("startedAt"))
            or parse_ts(session.get("createdAt"))
        )
        records.append((updated, key, session))

    records.sort(key=lambda item: item[0], reverse=True)
    recent = records[:limit_sessions]
    affected_sessions = []

    for _, key, session in recent:
        report = session.get("systemPromptReport") or {}
        truncation = report.get("bootstrapTruncation") or {}
        if not isinstance(truncation, dict):
            continue

        truncated_count, truncated_files = file_entries(truncation.get("truncatedFiles"))
        near_limit_count, near_limit_files = file_entries(truncation.get("nearLimitFiles"))
        total_near_limit = bool(truncation.get("totalNearLimit"))
        warning_shown = bool(truncation.get("warningShown"))

        if not any((truncated_count, near_limit_count, total_near_limit, warning_shown)):
            continue

        affected_sessions.append(
            {
                "session_key": session.get("sessionKey") or key,
                "updated_at": iso_utc(session.get("updatedAt") or session.get("endedAt") or session.get("startedAt")),
                "provider": session.get("modelProvider") or report.get("provider") or "unknown",
                "model": session.get("model") or report.get("model") or "unknown",
                "warning_shown": warning_shown,
                "total_near_limit": total_near_limit,
                "truncated_count": truncated_count,
                "truncated_files": truncated_files,
                "near_limit_count": near_limit_count,
                "near_limit_files": near_limit_files,
            }
        )

    agents.append(
        {
            "agent": agent_dir.name,
            "checked_sessions": len(recent),
            "affected_sessions": len(affected_sessions),
            "sessions": affected_sessions,
        }
    )

payload = {
    "checked_agents": len([a for a in agents if "error" not in a]),
    "affected_agents": len([a for a in agents if a.get("affected_sessions")]),
    "limit_sessions": limit_sessions,
    "results": sorted(
        agents,
        key=lambda item: (-item.get("affected_sessions", 0), item.get("agent", "")),
    ),
}

if output_json:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(0)

affected = [item for item in payload["results"] if item.get("affected_sessions")]
if not affected:
    print(
        f"No prompt truncation or near-limit warnings found across {payload['checked_agents']} live agents "
        f"(last {limit_sessions} sessions each)."
    )
    raise SystemExit(0)

print(
    f"Prompt truncation or near-limit warnings found in {payload['affected_agents']} of "
    f"{payload['checked_agents']} live agents (last {limit_sessions} sessions each):"
)
for agent in affected:
    print(f"- {agent['agent']}: {agent['affected_sessions']} affected of {agent['checked_sessions']} checked")
    for session in agent["sessions"]:
        print(
            f"    {session['updated_at']} | truncated={session['truncated_count']} "
            f"near_limit={session['near_limit_count']} warning={str(session['warning_shown']).lower()} "
            f"| {session['session_key']}"
        )
        for path in session["truncated_files"][:5]:
            print(f"      truncated: {path}")
        for path in session["near_limit_files"][:5]:
            print(f"      near-limit: {path}")
        if session["total_near_limit"]:
            print("      total prompt hit overall near-limit threshold")
PY
