#!/usr/bin/env python3
"""
Heartbeat Checker — Per-agent completion verification with auto-recovery.

Runs after each pipeline phase. Checks if required agents completed
within their window. If missed, triggers re-run before dependent agents.

Usage:
  python3 heartbeat-checker.py                    # Check all, auto-fix
  python3 heartbeat-checker.py --phase data       # Check only data phase
  python3 heartbeat-checker.py --dry-run        # Preview without running
  python3 heartbeat-checker.py --agent pipeline-agent  # Check single agent
"""

import json, subprocess, sys, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
HEARTBEAT_FILE = WORKSPACE / "data/heartbeat.json"
LOG_DIR = Path("/var/log/briefing")
TZ_OFFSET = 2

# Expected windows: when each agent should have run by
# Format: (agent_name, expected_by_cron, dependent_agents)
# dependent_agents = agents that READ this agent's output
AGENT_DEPS = {
    "pipeline-agent": {
        "expected_window_min": 60,   # Should run every 2h
        "depends_on": [],
        "output_file": "data/pipeline-status.json",
        "run_cmd": ["bash", str(WORKSPACE / "scripts/run-briefing-pipeline.sh"), "--data-only"],
    },
    "jobs-source-linkedin": {
        "expected_window_min": 480,  # Should run 4x/day (every 6h)
        "depends_on": [],
        "output_file": "data/jobs-raw/linkedin.json",
        "run_cmd": ["bash", str(WORKSPACE / "scripts/run-briefing-pipeline.sh"), "--jobs-only"],
    },
    "jobs-merge": {
        "expected_window_min": 60,   # After sources, within same pipeline run
        "depends_on": ["jobs-source-linkedin", "jobs-source-indeed"],
        "output_file": "data/jobs-merged.json",
        "run_cmd": ["bash", str(WORKSPACE / "scripts/run-briefing-pipeline.sh"), "--jobs-only"],
    },
    "jobs-review": {
        "expected_window_min": 120,  # After merge + enrich
        "depends_on": ["jobs-merge"],
        "output_file": "data/jobs-summary.json",
        "run_cmd": ["bash", str(WORKSPACE / "scripts/run-briefing-pipeline.sh"), "--jobs-only"],
    },
    "outreach-agent": {
        "expected_window_min": 60,   # Every 2h with data agents
        "depends_on": [],
        "output_file": "data/outreach-summary.json",
        "run_cmd": ["bash", str(WORKSPACE / "scripts/run-briefing-pipeline.sh"), "--data-only"],
    },
    "email-agent": {
        "expected_window_min": 60,
        "depends_on": [],
        "output_file": "data/email-summary.json",
        "run_cmd": ["bash", str(WORKSPACE / "scripts/run-briefing-pipeline.sh"), "--data-only"],
    },
    "pam-newsletter": {
        "expected_window_min": 480,  # Once per day (morning)
        "depends_on": ["pipeline-agent", "email-agent", "outreach-agent"],
        "output_file": "data/pam-newsletter.json",
        "run_cmd": ["python3", str(WORKSPACE / "scripts/pam-newsletter-agent.py")],
    },
}


def load_heartbeat():
    try:
        return json.load(open(HEARTBEAT_FILE))
    except:
        return {}


def last_run_ok(agent_name, hb):
    """Check if an agent ran within its expected window."""
    if agent_name not in hb:
        return False, "Never ran"

    entry = hb[agent_name]
    ts_str = entry.get("ts", "")
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone(timedelta(hours=TZ_OFFSET)))
        age_min = (now - ts).total_seconds() / 60
        window = AGENT_DEPS.get(agent_name, {}).get("expected_window_min", 60)
        if age_min <= window * 1.2:  # 20% grace period
            return True, f"OK ({int(age_min)}m ago)"
        else:
            return False, f"Missed window ({int(age_min)}m old, expected <{window}m)"
    except Exception as e:
        return False, f"Error: {e}"


def output_exists_and_fresh(agent_name, hb):
    """Check if the output file exists and has reasonable content."""
    entry = hb.get(agent_name, {})
    output = entry.get("output")
    if not output:
        return False, "No output tracked"
    path = Path(output)
    if not path.exists():
        return False, "Output file missing"
    size = path.stat().st_size
    if size < 10:
        return False, "Output file empty"
    return True, f"OK ({size:,} bytes)"


def check_agent(agent_name, dry_run=False):
    """Check one agent and re-run if needed."""
    hb = load_heartbeat()
    window_ok, window_msg = last_run_ok(agent_name, hb)
    output_ok, output_msg = output_exists_and_fresh(agent_name, hb)

    deps = AGENT_DEPS.get(agent_name, {})

    # Check dependencies first
    dep_failures = []
    for dep in deps.get("depends_on", []):
        dep_ok, dep_msg = last_run_ok(dep, hb)
        if not dep_ok:
            dep_failures.append((dep, dep_msg))

    result = {
        "agent": agent_name,
        "window_ok": window_ok,
        "window_msg": window_msg,
        "output_ok": output_ok,
        "output_msg": output_msg,
        "dep_failures": dep_failures,
        "action": None,
    }

    # Decide action
    if dep_failures:
        result["action"] = "BLOCKED"
        result["action_msg"] = f"Blocked by: {', '.join(d[0] for d in dep_failures)}"
    elif not window_ok or not output_ok:
        result["action"] = "RE-RUN"
        result["action_msg"] = f"{window_msg} | {output_msg}"
    else:
        result["action"] = "OK"

    return result


def run_agent(agent_name, cmd, dry_run=False):
    """Run an agent's recovery command."""
    print(f"\n  🔄 Re-running {agent_name}...")
    if dry_run:
        print(f"     Would run: {' '.join(cmd)}")
        return True

    log_file = LOG_DIR / f"heartbeat-{agent_name}-{datetime.now().strftime('%Y%m%d-%H%M')}.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with open(log_file, "w") as f:
        f.write(f"Heartbeat re-run: {agent_name} at {datetime.now()}\n")
        f.write(f"Command: {' '.join(cmd)}\n\n")

    result = subprocess.run(
        cmd,
        cwd=WORKSPACE,
        stdout=open(log_file, "a"),
        stderr=subprocess.STDOUT,
        timeout=600,
    )

    if result.returncode == 0:
        # Record heartbeat
        subprocess.run(
            ["python3", str(WORKSPACE / "scripts/heartbeat-tracker.py"),
             "--agent", agent_name, "--output",
             AGENT_DEPS.get(agent_name, {}).get("output_file", "")],
            timeout=10,
        )
        print(f"  ✅ {agent_name} re-run successful")
        return True
    else:
        print(f"  ❌ {agent_name} re-run failed (exit {result.returncode})")
        print(f"     Log: {log_file}")
        return False


def check_all(dry_run=False):
    """Check all agents and report."""
    hb = load_heartbeat()
    now = datetime.now(timezone(timedelta(hours=TZ_OFFSET)))
    print(f"\n❤️ Heartbeat Check — {now.strftime('%Y-%m-%d %H:%M')} Cairo")
    print("=" * 55)

    actions_taken = []
    agents_blocked = []

    for agent in sorted(AGENT_DEPS.keys()):
        r = check_agent(agent, dry_run)
        emoji = {"OK": "✅", "RE-RUN": "🔄", "BLOCKED": "🚫"}.get(r["action"], "❓")

        if r["action"] == "OK":
            print(f"  {emoji} {agent:<35} {r['window_msg']}")
        elif r["action"] == "RE-RUN":
            print(f"  {emoji} {agent:<35} {r['action_msg']}")
            ok = run_agent(agent, AGENT_DEPS[agent]["run_cmd"], dry_run)
            actions_taken.append((agent, ok))
        else:
            print(f"  {emoji} {agent:<35} {r['action_msg']}")
            agents_blocked.append(agent)

    print("=" * 55)

    if actions_taken:
        print(f"\n🔄 {len(actions_taken)} agent(s) re-run:")
        for agent, ok in actions_taken:
            print(f"  {'✅' if ok else '❌'} {agent}")
    if agents_blocked:
        print(f"\n🚫 {len(agents_blocked)} blocked (missing dependencies):")
        for a in agents_blocked:
            print(f"  - {a}")
    if not actions_taken and not agents_blocked:
        print("\n  All agents healthy. No action needed.")

    return actions_taken, agents_blocked


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    phase = None
    if "--phase" in sys.argv:
        i = sys.argv.index("--phase")
        phase = sys.argv[i + 1]

    if "--agent" in sys.argv:
        i = sys.argv.index("--agent")
        agent = sys.argv[i + 1]
        r = check_agent(agent, dry_run)
        print(json.dumps(r, indent=2))
    else:
        check_all(dry_run)
