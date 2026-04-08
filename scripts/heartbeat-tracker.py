#!/usr/bin/env python3
"""
Heartbeat Tracker — Records successful agent runs for the heartbeat system.

Each agent calls this after a successful run:
  python3 heartbeat-tracker.py --agent pipeline-agent --output data/pipeline-status.json

Stores last successful run in data/heartbeat.json:
  {
    "pipeline-agent": {"ts": "2026-03-22T05:00:12+02:00", "output": "data/pipeline-status.json", "hash": "abc123"},
    ...
  }

Also stores a hash of the output file so we can detect if the data actually changed.
"""

import json, sys, hashlib, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
HEARTBEAT_FILE = WORKSPACE / "data/heartbeat.json"
TZ_OFFSET = 2

def file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except:
        return "?"

def load_heartbeat():
    if HEARTBEAT_FILE.exists():
        try:
            return json.load(open(HEARTBEAT_FILE))
        except:
            pass
    return {}

def save_heartbeat(data):
    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(HEARTBEAT_FILE, "w"), indent=2)

def record(agent_name, output_file=None):
    """Record a successful run for an agent."""
    data = load_heartbeat()
    entry = {
        "ts": datetime.now(timezone(timedelta(hours=TZ_OFFSET))).isoformat(),
        "ts_utc": datetime.now(timezone.utc).isoformat(),
    }
    if output_file:
        path = WORKSPACE / output_file if not Path(output_file).is_absolute() else Path(output_file)
        entry["output"] = str(path)
        entry["hash"] = file_hash(path) if path.exists() else "?"
        entry["size"] = path.stat().st_size if path.exists() else 0

    data[agent_name] = entry
    save_heartbeat(data)
    print(f"Heartbeat recorded: {agent_name} at {entry['ts']}")

def status():
    """Show current heartbeat status."""
    data = load_heartbeat()
    if not data:
        print("No heartbeats recorded.")
        return

    now = datetime.now(timezone(timedelta(hours=TZ_OFFSET)))
    print(f"\nHeartbeat Status — {now.strftime('%Y-%m-%d %H:%M')} Cairo")
    print("=" * 50)
    for agent, info in sorted(data.items()):
        ts = datetime.fromisoformat(info["ts"].replace("Z", "+00:00"))
        age_min = int((now - ts).total_seconds() / 60)
        if age_min < 60:
            age = f"{age_min}m ago"
        elif age_min < 1440:
            age = f"{age_min//60}h {age_min%60}m ago"
        else:
            age = f"{age_min//1440}d ago"
        size = info.get("size", 0)
        print(f"  ✅ {agent:<30} {age} ({size:,} bytes)")

if __name__ == "__main__":
    if "--status" in sys.argv:
        status()
    elif "--agent" in sys.argv and "--output" in sys.argv:
        i = sys.argv.index("--agent")
        agent = sys.argv[i + 1]
        output = None
        if "--output" in sys.argv:
            j = sys.argv.index("--output")
            output = sys.argv[j + 1]
        record(agent, output)
    elif "--agent" in sys.argv:
        i = sys.argv.index("--agent")
        agent = sys.argv[i + 1]
        record(agent)
    else:
        print("Usage:")
        print("  python3 heartbeat-tracker.py --status")
        print("  python3 heartbeat-tracker.py --agent pipeline-agent --output data/pipeline-status.json")
