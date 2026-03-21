#!/usr/bin/env python3
"""
Weekly Team Retro - Structured per-agent performance review.

Pulls from:
- heartbeat.json (last successful run per agent)
- run-history.jsonl (all runs with duration, status, records)
- agent-feedback/ (accepted/revised/rejected outcomes)
- lessons-learned.md (captured learnings)
- outreach-alerts.json (follow-up stats)

Generates a structured markdown report with:
- Per-agent stats (runs, success rate, avg duration)
- Failure patterns
- Top performers
- Growth areas
- Recommendations

Usage:
  python3 weekly-team-retro.py                  # Generate retro for last 7 days
  python3 weekly-team-retro.py --days 14        # Last 14 days
  python3 weekly-team-retro.py --output /path   # Custom output path
  python3 weekly-team-retro.py --dry-run        # Preview without saving
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict
import argparse

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
MEMORY_DIR = WORKSPACE / "memory"
OUTPUT_DIR = MEMORY_DIR / "retros"

def parse_args():
    parser = argparse.ArgumentParser(description="Generate weekly team retro")
    parser.add_argument("--days", type=int, default=7, help="Days to analyze")
    parser.add_argument("--output", type=str, help="Custom output path")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    return parser.parse_args()

def load_run_history(days: int) -> list:
    """Load run history for the specified time window."""
    history_file = DATA_DIR / "run-history.jsonl"
    if not history_file.exists():
        return []
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    runs = []
    
    with open(history_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                run = json.loads(line)
                # Parse timestamp
                started = run.get("started", "")
                if started:
                    # Handle both formats
                    try:
                        ts = datetime.fromisoformat(started.replace("Z", "+00:00"))
                    except:
                        continue
                    if ts >= cutoff:
                        run["_ts"] = ts
                        runs.append(run)
            except json.JSONDecodeError:
                continue
    
    return runs

def load_heartbeat() -> dict:
    """Load current heartbeat status."""
    heartbeat_file = DATA_DIR / "heartbeat.json"
    if heartbeat_file.exists():
        with open(heartbeat_file) as f:
            return json.load(f)
    return {}

def load_agent_feedback(days: int) -> dict:
    """Load agent feedback outcomes."""
    feedback_dir = DATA_DIR / "agent-feedback"
    if not feedback_dir.exists():
        return defaultdict(lambda: {"accepted": 0, "revised": 0, "rejected": 0})
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    feedback = defaultdict(lambda: {"accepted": 0, "revised": 0, "rejected": 0})
    
    for f in feedback_dir.glob("*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
                # Check if within window
                ts_str = data.get("timestamp", "")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts < cutoff:
                            continue
                    except:
                        pass
                
                agent = data.get("agent", "unknown")
                status = data.get("status", "unknown")
                if status in ["accepted", "revised", "rejected"]:
                    feedback[agent][status] += 1
        except:
            continue
    
    return feedback

def load_lessons_learned(days: int) -> list:
    """Load lessons learned from the period."""
    lessons_file = MEMORY_DIR / "lessons-learned.md"
    if not lessons_file.exists():
        return []
    
    cutoff = datetime.now() - timedelta(days=days)
    lessons = []
    current_date = None
    current_lessons = []
    
    with open(lessons_file) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("## "):
                # Date header
                if current_date and current_lessons:
                    lessons.append({"date": current_date, "items": current_lessons})
                current_lessons = []
                date_str = line[3:].strip()
                try:
                    current_date = datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    current_date = None
            elif line.startswith("- ") and current_date:
                if current_date >= cutoff:
                    current_lessons.append(line[2:])
    
    if current_date and current_lessons:
        lessons.append({"date": current_date, "items": current_lessons})
    
    return lessons

def analyze_runs(runs: list) -> dict:
    """Analyze run history per agent."""
    stats = defaultdict(lambda: {
        "total_runs": 0,
        "successes": 0,
        "failures": 0,
        "total_duration_ms": 0,
        "total_records": 0,
        "errors": []
    })
    
    for run in runs:
        agent = run.get("agent", "unknown")
        status = run.get("status", "unknown")
        duration = run.get("duration_ms", 0)
        records = run.get("records", 0)
        error = run.get("error")
        
        stats[agent]["total_runs"] += 1
        stats[agent]["total_duration_ms"] += duration
        stats[agent]["total_records"] += records
        
        if status == "success":
            stats[agent]["successes"] += 1
        else:
            stats[agent]["failures"] += 1
            if error:
                stats[agent]["errors"].append(error)
    
    # Calculate derived metrics
    for agent, data in stats.items():
        total = data["total_runs"]
        if total > 0:
            data["success_rate"] = round(data["successes"] / total * 100, 1)
            data["avg_duration_ms"] = round(data["total_duration_ms"] / total)
            data["avg_records"] = round(data["total_records"] / total, 1)
        else:
            data["success_rate"] = 0
            data["avg_duration_ms"] = 0
            data["avg_records"] = 0
    
    return dict(stats)

def generate_report(days: int, runs: list, heartbeat: dict, feedback: dict, lessons: list) -> str:
    """Generate the markdown report."""
    stats = analyze_runs(runs)
    now = datetime.now(timezone(timedelta(hours=2)))  # Cairo
    period_start = now - timedelta(days=days)
    
    report = []
    report.append(f"# Weekly Team Retro")
    report.append(f"")
    report.append(f"**Period:** {period_start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
    report.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M')} Cairo")
    report.append(f"")
    
    # Summary stats
    total_runs = sum(s["total_runs"] for s in stats.values())
    total_success = sum(s["successes"] for s in stats.values())
    total_failures = sum(s["failures"] for s in stats.values())
    overall_rate = round(total_success / total_runs * 100, 1) if total_runs > 0 else 0
    
    report.append(f"## Summary")
    report.append(f"")
    report.append(f"| Metric | Value |")
    report.append(f"|--------|-------|")
    report.append(f"| Total Runs | {total_runs} |")
    report.append(f"| Successes | {total_success} |")
    report.append(f"| Failures | {total_failures} |")
    report.append(f"| Overall Success Rate | {overall_rate}% |")
    report.append(f"| Active Agents | {len(stats)} |")
    report.append(f"")
    
    # Per-agent breakdown
    report.append(f"## Agent Performance")
    report.append(f"")
    report.append(f"| Agent | Runs | Success Rate | Avg Duration | Avg Records |")
    report.append(f"|-------|------|--------------|--------------|-------------|")
    
    # Sort by total runs descending
    sorted_agents = sorted(stats.items(), key=lambda x: x[1]["total_runs"], reverse=True)
    
    for agent, data in sorted_agents:
        duration_str = f"{data['avg_duration_ms']}ms" if data['avg_duration_ms'] < 1000 else f"{data['avg_duration_ms']/1000:.1f}s"
        rate_emoji = "✅" if data["success_rate"] >= 95 else "⚠️" if data["success_rate"] >= 80 else "❌"
        report.append(f"| {agent} | {data['total_runs']} | {rate_emoji} {data['success_rate']}% | {duration_str} | {data['avg_records']} |")
    
    report.append(f"")
    
    # Top performers
    report.append(f"## Top Performers")
    report.append(f"")
    
    # Most reliable (highest success rate with min 5 runs)
    reliable = [(a, d) for a, d in sorted_agents if d["total_runs"] >= 5]
    reliable.sort(key=lambda x: x[1]["success_rate"], reverse=True)
    
    if reliable:
        top = reliable[0]
        report.append(f"**Most Reliable:** {top[0]} ({top[1]['success_rate']}% success rate across {top[1]['total_runs']} runs)")
    
    # Fastest (lowest avg duration with min 5 runs)
    fast = [(a, d) for a, d in sorted_agents if d["total_runs"] >= 5 and d["avg_duration_ms"] > 0]
    fast.sort(key=lambda x: x[1]["avg_duration_ms"])
    
    if fast:
        top = fast[0]
        duration_str = f"{top[1]['avg_duration_ms']}ms" if top[1]['avg_duration_ms'] < 1000 else f"{top[1]['avg_duration_ms']/1000:.1f}s"
        report.append(f"**Fastest:** {top[0]} (avg {duration_str})")
    
    # Most productive (highest avg records)
    productive = [(a, d) for a, d in sorted_agents if d["total_runs"] >= 5]
    productive.sort(key=lambda x: x[1]["avg_records"], reverse=True)
    
    if productive:
        top = productive[0]
        report.append(f"**Most Productive:** {top[0]} (avg {top[1]['avg_records']} records/run)")
    
    report.append(f"")
    
    # Failure patterns
    failures = [(a, d) for a, d in sorted_agents if d["failures"] > 0]
    if failures:
        report.append(f"## Failure Patterns")
        report.append(f"")
        
        for agent, data in failures:
            if data["errors"]:
                report.append(f"**{agent}** ({data['failures']} failures):")
                # Dedupe errors
                unique_errors = list(set(data["errors"]))[:3]
                for err in unique_errors:
                    report.append(f"  - {err[:100]}...")
                report.append(f"")
    
    # Feedback stats
    if feedback:
        report.append(f"## Output Quality (Agent Feedback)")
        report.append(f"")
        report.append(f"| Agent | Accepted | Revised | Rejected |")
        report.append(f"|-------|----------|---------|----------|")
        
        for agent, counts in sorted(feedback.items()):
            total = counts["accepted"] + counts["revised"] + counts["rejected"]
            if total > 0:
                report.append(f"| {agent} | {counts['accepted']} | {counts['revised']} | {counts['rejected']} |")
        
        report.append(f"")
    
    # Lessons learned
    if lessons:
        report.append(f"## Lessons Learned This Period")
        report.append(f"")
        
        for entry in lessons[-5:]:  # Last 5 days with lessons
            report.append(f"**{entry['date'].strftime('%Y-%m-%d')}:**")
            for item in entry["items"][:3]:  # Max 3 per day
                report.append(f"- {item}")
            report.append(f"")
    
    # Growth areas
    report.append(f"## Growth Areas")
    report.append(f"")
    
    # Low success rate agents
    low_success = [(a, d) for a, d in sorted_agents if d["success_rate"] < 90 and d["total_runs"] >= 3]
    if low_success:
        report.append(f"**Reliability improvements needed:**")
        for agent, data in low_success:
            report.append(f"- {agent}: {data['success_rate']}% success rate")
        report.append(f"")
    
    # Slow agents
    slow = [(a, d) for a, d in sorted_agents if d["avg_duration_ms"] > 60000 and d["total_runs"] >= 3]
    if slow:
        report.append(f"**Performance optimization candidates:**")
        for agent, data in slow:
            report.append(f"- {agent}: avg {data['avg_duration_ms']/1000:.1f}s per run")
        report.append(f"")
    
    # Recommendations
    report.append(f"## Recommendations")
    report.append(f"")
    
    recommendations = []
    
    if total_failures > total_runs * 0.1:
        recommendations.append("- Overall failure rate above 10% - investigate error patterns")
    
    if low_success:
        recommendations.append(f"- Focus on stabilizing {low_success[0][0]} (lowest reliability)")
    
    if slow:
        recommendations.append(f"- Consider parallelizing or caching for {slow[0][0]} (slowest agent)")
    
    if not lessons:
        recommendations.append("- No lessons captured this period - enable auto-lessons-learned cron")
    
    if not recommendations:
        recommendations.append("- System performing well - maintain current practices")
    
    for rec in recommendations:
        report.append(rec)
    
    report.append(f"")
    report.append(f"---")
    report.append(f"*Generated by weekly-team-retro.py*")
    
    return "\n".join(report)

def main():
    args = parse_args()
    
    print(f"📊 Generating team retro for last {args.days} days...")
    
    # Load data
    runs = load_run_history(args.days)
    heartbeat = load_heartbeat()
    feedback = load_agent_feedback(args.days)
    lessons = load_lessons_learned(args.days)
    
    print(f"  - Loaded {len(runs)} runs from history")
    print(f"  - Loaded {len(heartbeat)} agents from heartbeat")
    print(f"  - Loaded feedback for {len(feedback)} agents")
    print(f"  - Loaded {sum(len(l['items']) for l in lessons)} lessons")
    
    # Generate report
    report = generate_report(args.days, runs, heartbeat, feedback, lessons)
    
    if args.dry_run:
        print("\n" + "="*60)
        print(report)
        print("="*60)
        print("\n(dry-run mode - not saved)")
        return
    
    # Save report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.output:
        output_path = Path(args.output)
    else:
        now = datetime.now()
        output_path = OUTPUT_DIR / f"{now.strftime('%Y-%m-%d')}-weekly-retro.md"
    
    with open(output_path, "w") as f:
        f.write(report)
    
    print(f"✅ Retro saved to: {output_path}")

if __name__ == "__main__":
    main()
