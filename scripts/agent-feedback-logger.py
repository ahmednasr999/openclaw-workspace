#!/usr/bin/env python3
"""
Agent Feedback Logger - Tracks agent output quality.

Logs every agent output event with: agent, task_type, status, revision_reason, timestamp.
Read by weekly-agent-review.py to compute per-agent metrics.

Usage:
  python3 agent-feedback-logger.py --agent writer --task linkedin_post --status accepted
  python3 agent-feedback-logger.py --agent writer --task linkedin_post --status revised --reason "tone too corporate"
  python3 agent-feedback-logger.py --agent cv --task cv_tailor --status accepted --meta '{"ats_score": 85}'
  python3 agent-feedback-logger.py --report   # Show weekly summary
"""
import json, sys, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

FEEDBACK_DIR = Path("/root/.openclaw/workspace/data/agent-feedback")
FEEDBACK_FILE = FEEDBACK_DIR / "feedback.jsonl"
FAILURE_DIR = Path("/var/log/briefing")

FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


def log_feedback(agent, task_type, status, reason="", meta=None):
    """Append a feedback entry."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "task": task_type,
        "status": status,  # accepted, revised, rejected
        "reason": reason,
        "meta": meta or {},
    }
    with open(FEEDBACK_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Logged: {agent}/{task_type} -> {status}")


def load_feedback(days=7):
    """Load recent feedback entries."""
    if not FEEDBACK_FILE.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    entries = []
    for line in open(FEEDBACK_FILE):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            ts = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
            if ts >= cutoff:
                entries.append(e)
        except:
            pass
    return entries


def load_failures(days=7):
    """Load pipeline failure logs."""
    failures = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    for f in sorted(FAILURE_DIR.glob("failures-*.jsonl")):
        try:
            date_str = f.stem.replace("failures-", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < cutoff:
                continue
        except:
            continue
        for line in open(f):
            line = line.strip()
            if not line:
                continue
            try:
                failures.append(json.loads(line))
            except:
                pass
    return failures


def generate_report(days=7):
    """Generate per-agent quality report."""
    feedback = load_feedback(days)
    failures = load_failures(days)

    print(f"\n{'='*60}")
    print(f"  Agent Quality Report (last {days} days)")
    print(f"{'='*60}\n")

    # --- Feedback Metrics ---
    agents = {}
    for e in feedback:
        agent = e["agent"]
        if agent not in agents:
            agents[agent] = {"accepted": 0, "revised": 0, "rejected": 0, "total": 0, "reasons": []}
        agents[agent][e["status"]] = agents[agent].get(e["status"], 0) + 1
        agents[agent]["total"] += 1
        if e.get("reason"):
            agents[agent]["reasons"].append(e["reason"])

    if agents:
        print("Agent Output Quality:")
        print(f"  {'Agent':<15} {'Total':>6} {'Accept':>7} {'Revise':>7} {'Reject':>7} {'Accept%':>8}")
        print(f"  {'-'*15} {'-'*6} {'-'*7} {'-'*7} {'-'*7} {'-'*8}")
        for name, m in sorted(agents.items()):
            pct = f"{m['accepted']/m['total']*100:.0f}%" if m['total'] > 0 else "N/A"
            print(f"  {name:<15} {m['total']:>6} {m['accepted']:>7} {m['revised']:>7} {m['rejected']:>7} {pct:>8}")

        # Top revision reasons
        all_reasons = []
        for m in agents.values():
            all_reasons.extend(m["reasons"])
        if all_reasons:
            print(f"\n  Top Revision Reasons:")
            from collections import Counter
            for reason, count in Counter(all_reasons).most_common(5):
                print(f"    {count}x - {reason}")
    else:
        print("  No feedback data yet.")

    # --- Failure Metrics ---
    print(f"\n{'='*60}")
    print("Pipeline Failure Classification:")
    
    if failures:
        agent_failures = {}
        category_counts = {}
        for f in failures:
            agent = f.get("agent", "?")
            cat = f.get("category", "UNKNOWN")
            if agent not in agent_failures:
                agent_failures[agent] = 0
            agent_failures[agent] += 1
            category_counts[cat] = category_counts.get(cat, 0) + 1

        print(f"\n  By Category:")
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            emoji = {"TRANSIENT": "🟡", "CONFIG": "🔴", "LOGIC": "🔴"}.get(cat, "⚪")
            print(f"    {emoji} {cat}: {count}")

        print(f"\n  By Agent:")
        for agent, count in sorted(agent_failures.items(), key=lambda x: -x[1]):
            print(f"    {agent}: {count} failures")
    else:
        print("  No pipeline failures recorded.")

    # --- Cron Success Rate ---
    print(f"\n{'='*60}")
    print("Cron Success Rate (from pipeline logs):")
    
    total_runs = 0
    ok_runs = 0
    for logfile in sorted(FAILURE_DIR.glob("*.log")):
        if "failures" in logfile.name:
            continue
        try:
            content = open(logfile).read()
            total_runs += content.count("START ")
            ok_runs += content.count("OK    ")
        except:
            pass
    
    if total_runs > 0:
        rate = ok_runs / total_runs * 100
        print(f"  Total agent runs: {total_runs}")
        print(f"  Successful: {ok_runs} ({rate:.1f}%)")
        print(f"  Failed: {total_runs - ok_runs} ({100-rate:.1f}%)")
    else:
        print("  No pipeline logs found.")

    print(f"\n{'='*60}\n")

    # Save report as JSON
    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "feedback_summary": {
            name: {k: v for k, v in m.items() if k != "reasons"}
            for name, m in agents.items()
        },
        "failure_summary": {
            "by_category": category_counts if failures else {},
            "by_agent": agent_failures if failures else {},
        },
        "cron_success_rate": {
            "total": total_runs,
            "ok": ok_runs,
            "rate": round(ok_runs / total_runs * 100, 1) if total_runs > 0 else 0,
        },
    }
    report_file = FEEDBACK_DIR / "weekly-report.json"
    json.dump(report, open(report_file, "w"), indent=2)
    print(f"Report saved: {report_file}")
    return report


if __name__ == "__main__":
    if "--report" in sys.argv:
        days = 7
        for i, arg in enumerate(sys.argv):
            if arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])
        generate_report(days)
    else:
        # Parse args
        agent = task = status = reason = ""
        meta = None
        for i, arg in enumerate(sys.argv):
            if arg == "--agent" and i + 1 < len(sys.argv): agent = sys.argv[i + 1]
            if arg == "--task" and i + 1 < len(sys.argv): task = sys.argv[i + 1]
            if arg == "--status" and i + 1 < len(sys.argv): status = sys.argv[i + 1]
            if arg == "--reason" and i + 1 < len(sys.argv): reason = sys.argv[i + 1]
            if arg == "--meta" and i + 1 < len(sys.argv):
                try: meta = json.loads(sys.argv[i + 1])
                except: meta = {"raw": sys.argv[i + 1]}

        if not all([agent, task, status]):
            print("Usage: agent-feedback-logger.py --agent NAME --task TYPE --status STATUS [--reason TEXT] [--meta JSON]")
            print("  Status: accepted, revised, rejected")
            sys.exit(1)

        log_feedback(agent, task, status, reason, meta)
