#!/usr/bin/env python3
"""
daily-learner.py — Learning engine that analyzes feedback and auto-adjusts parameters.

Runs at 11 PM Cairo daily. Analyzes:
- Job recommendations vs actual applications (accuracy)
- Briefing actions vs actual changes (actionability)

Auto-adjustments (with guard rails):
- Skip patterns: add to skip-patterns.md after 2 consistent skips
- Keyword weights: update keyword-weights.json (max +/-0.5 per week)
- Source rankings: update source-rankings.json

Guard rails:
- Max weight change: +/-0.5 per week
- Skip pattern: only after 2 consistent signals
- Drift ceiling: no parameter moves >30% from original
- Kill switch: --no-learn flag
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add parent to path for agent-common
sys.path.insert(0, str(Path(__file__).parent))
from pathlib import Path

# Try to import agent_main, fall back to local implementation if not available
try:
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location("agent_common", Path(__file__).parent / "agent-common.py")
    agent_common = module_from_spec(spec)
    spec.loader.exec_module(agent_common)
    agent_main = agent_common.agent_main
    AgentResult = agent_common.AgentResult
    now_cairo = agent_common.now_cairo
    now_iso = agent_common.now_iso
    load_json = agent_common.load_json
    is_dry_run = agent_common.is_dry_run
    WORKSPACE = agent_common.WORKSPACE
    DATA_DIR = agent_common.DATA_DIR
    FEEDBACK_DIR = agent_common.FEEDBACK_DIR
    LEARNING_DIR = agent_common.LEARNING_DIR
except Exception as e:
    print(f"Warning: Could not import agent-common.py: {e}")
    print("Using local fallback implementations")
    from datetime import timezone
    WORKSPACE = Path("/root/.openclaw/workspace")
    DATA_DIR = WORKSPACE / "data"
    FEEDBACK_DIR = DATA_DIR / "feedback"
    LEARNING_DIR = DATA_DIR / "learning"
    CAIRO_TZ = timezone(timedelta(hours=2))
    def now_cairo(): return datetime.now(CAIRO_TZ)
    def now_iso(): return now_cairo().isoformat()
    def load_json(path, default=None):
        path = Path(path)
        if not path.exists(): return default or {}
        try:
            with open(path) as f: return json.load(f)
        except: return default or {}
    def is_dry_run(): return "--dry-run" in sys.argv

# Paths
JOBS_BANK = WORKSPACE / "jobs-bank"
APPLIED_IDS_FILE = JOBS_BANK / "applied-job-ids.txt"
SKIP_PATTERNS_FILE = JOBS_BANK / "skip-patterns.md"
KEYWORD_WEIGHTS_FILE = LEARNING_DIR / "keyword-weights.json"
SOURCE_RANKINGS_FILE = LEARNING_DIR / "source-rankings.json"
LEARNING_SUMMARY_FILE = LEARNING_DIR / "learning-summary.json"
LEARNING_LOG_FILE = LEARNING_DIR / "learning-log.jsonl"
ORIGINAL_WEIGHTS_FILE = LEARNING_DIR / "original-weights.json"  # Baseline for drift ceiling

# Guard rail constants
MAX_WEIGHT_CHANGE_PER_WEEK = 0.5
MIN_SKIP_SIGNALS = 2
DRIFT_CEILING_PERCENT = 30  # Max 30% drift from original


def load_applied_job_ids():
    """Load set of job IDs that Ahmed actually applied to."""
    if not APPLIED_IDS_FILE.exists():
        return set()
    with open(APPLIED_IDS_FILE) as f:
        return set(line.strip() for line in f if line.strip() and not line.startswith('#'))


def load_jsonl(path):
    """Load all entries from a JSONL file."""
    path = Path(path)
    if not path.exists():
        return []
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def append_jsonl(path, entry):
    """Append a single entry to a JSONL file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a') as f:
        f.write(json.dumps(entry, default=str) + '\n')


def is_no_learn():
    """Check if --no-learn flag is set (kill switch)."""
    return "--no-learn" in sys.argv


def get_week_start():
    """Get the Monday of the current week."""
    today = now_cairo().date()
    return today - timedelta(days=today.weekday())


def calculate_job_recommendation_accuracy(result):
    """
    Analyze jobs-recommended.jsonl against applied-job-ids.txt.
    Returns accuracy metrics and skip candidates.
    """
    recommendations = load_jsonl(FEEDBACK_DIR / "jobs-recommended.jsonl")
    applied_ids = load_applied_job_ids()
    
    if not recommendations:
        return {
            "total_recommendations": 0,
            "applied_count": 0,
            "skip_count": 0,
            "accuracy_rate": None,
            "skip_candidates": []
        }
    
    # Group by job_id to count signals
    job_signals = defaultdict(lambda: {"submit_count": 0, "skip_count": 0, "reasons": []})
    
    for rec in recommendations:
        job_id = rec.get("job_id", rec.get("id", ""))
        verdict = rec.get("verdict", "").upper()
        reason = rec.get("reason", "")
        
        if verdict in ["SUBMIT", "APPLY"]:
            job_signals[job_id]["submit_count"] += 1
        elif verdict in ["SKIP", "REJECT", "REVIEW"]:
            job_signals[job_id]["skip_count"] += 1
            if reason:
                job_signals[job_id]["reasons"].append(reason)
    
    # Calculate accuracy
    total_submit_recs = sum(1 for j in job_signals.values() if j["submit_count"] > 0)
    applied_from_recs = sum(1 for job_id in job_signals if job_id in applied_ids and job_signals[job_id]["submit_count"] > 0)
    
    # Find skip candidates (2+ consistent skip signals)
    skip_candidates = []
    for job_id, signals in job_signals.items():
        if signals["skip_count"] >= MIN_SKIP_SIGNALS and signals["submit_count"] == 0:
            # Extract common reason
            reasons = signals["reasons"]
            common_reason = reasons[0] if reasons else "Consistently skipped"
            skip_candidates.append({
                "job_id": job_id,
                "skip_signals": signals["skip_count"],
                "reason": common_reason
            })
    
    return {
        "total_recommendations": len(recommendations),
        "total_unique_jobs": len(job_signals),
        "submit_recommendations": total_submit_recs,
        "applied_count": applied_from_recs,
        "accuracy_rate": (applied_from_recs / total_submit_recs * 100) if total_submit_recs > 0 else None,
        "skip_candidates": skip_candidates
    }


def calculate_briefing_actionability(result):
    """
    Analyze briefing-actions.jsonl against data file changes.
    Did the briefing actions lead to actual changes?
    """
    actions = load_jsonl(FEEDBACK_DIR / "briefing-actions.jsonl")
    
    if not actions:
        return {
            "total_briefings": 0,
            "actionable_rate": None
        }
    
    # Get today's and yesterday's data snapshots
    today = now_cairo().date().isoformat()
    yesterday = (now_cairo().date() - timedelta(days=1)).isoformat()
    
    # Check current state of data files
    pipeline = load_json(DATA_DIR / "pipeline-status.json", {})
    
    # Find yesterday's action entry
    yesterday_actions = [a for a in actions if a.get("date") == yesterday]
    
    if not yesterday_actions:
        return {
            "total_briefings": len(actions),
            "yesterday_actions": None,
            "changes_detected": False,
            "actionable_rate": None
        }
    
    last_action = yesterday_actions[-1]
    prev_pipeline_total = last_action.get("pipeline_total", 0)
    current_pipeline_total = len(pipeline.get("data", {}).get("applications", []))
    
    # Simple heuristic: did pipeline change?
    changes_detected = current_pipeline_total != prev_pipeline_total
    
    # Calculate overall actionability (how often briefings led to changes)
    action_dates = set(a.get("date") for a in actions)
    
    return {
        "total_briefings": len(actions),
        "yesterday_actions": last_action.get("actions", []),
        "yesterday_urgent": last_action.get("urgent_count", 0),
        "changes_detected": changes_detected,
        "pipeline_delta": current_pipeline_total - prev_pipeline_total
    }


def load_weekly_weight_changes():
    """Load weight changes made this week for guard rail enforcement."""
    log_entries = load_jsonl(LEARNING_LOG_FILE)
    week_start = get_week_start().isoformat()
    
    weekly_changes = defaultdict(float)
    for entry in log_entries:
        if entry.get("timestamp", "")[:10] >= week_start:
            for change in entry.get("weight_changes", []):
                keyword = change.get("keyword", "")
                delta = change.get("delta", 0)
                weekly_changes[keyword] += abs(delta)
    
    return weekly_changes


def load_original_weights():
    """Load original baseline weights for drift ceiling check."""
    if ORIGINAL_WEIGHTS_FILE.exists():
        return load_json(ORIGINAL_WEIGHTS_FILE, {})
    # If no original file, current weights become the baseline
    current = load_json(KEYWORD_WEIGHTS_FILE, {})
    if current and not is_dry_run():
        ORIGINAL_WEIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ORIGINAL_WEIGHTS_FILE, 'w') as f:
            json.dump(current, f, indent=2)
    return current


def check_drift_ceiling(keyword, current_value, proposed_value, original_weights):
    """Check if proposed change exceeds drift ceiling from original."""
    original = original_weights.get(keyword, current_value)
    if original == 0:
        return True  # Can't calculate percentage drift from zero
    
    proposed_drift_pct = abs(proposed_value - original) / abs(original) * 100
    return proposed_drift_pct <= DRIFT_CEILING_PERCENT


def update_skip_patterns(skip_candidates, result):
    """Add new skip patterns to skip-patterns.md after validation."""
    if not skip_candidates:
        return []
    
    # Read existing patterns
    existing_patterns = set()
    if SKIP_PATTERNS_FILE.exists():
        with open(SKIP_PATTERNS_FILE) as f:
            for line in f:
                if line.startswith("- "):
                    # Extract job identifier from pattern
                    existing_patterns.add(line.strip())
    
    # Add new patterns
    added_patterns = []
    today = now_cairo().date().isoformat()
    
    new_lines = []
    for candidate in skip_candidates:
        job_id = candidate["job_id"]
        reason = candidate["reason"]
        skip_signals = candidate["skip_signals"]
        
        # Create pattern line
        pattern_line = f"- [{today}] {job_id}: {reason} (auto-learned after {skip_signals} skip signals)"
        
        # Check if similar pattern already exists
        if not any(job_id in p for p in existing_patterns):
            new_lines.append(pattern_line)
            added_patterns.append({"job_id": job_id, "reason": reason})
    
    if new_lines and not is_dry_run():
        with open(SKIP_PATTERNS_FILE, 'a') as f:
            f.write("\n" + "\n".join(new_lines))
    
    return added_patterns


def update_keyword_weights(job_accuracy, result):
    """
    Adjust keyword weights based on recommendation accuracy.
    Guard rails: max +/-0.5 per week, 30% drift ceiling.
    """
    if job_accuracy.get("accuracy_rate") is None:
        return []
    
    current_weights = load_json(KEYWORD_WEIGHTS_FILE, {
        "transformation": 1.0,
        "digital": 1.0,
        "PMO": 1.0,
        "VP": 1.2,
        "Director": 1.1,
        "MENA": 1.1,
        "Dubai": 1.1,
        "Riyadh": 1.0,
        "remote": 0.9
    })
    
    original_weights = load_original_weights()
    weekly_changes = load_weekly_weight_changes()
    
    accuracy = job_accuracy["accuracy_rate"]
    weight_adjustments = []
    
    # Simple heuristic: if accuracy is high (>70%), boost core keywords slightly
    # If accuracy is low (<50%), reduce weights on non-core keywords
    if accuracy >= 70:
        # Good accuracy - slight boost to core keywords
        for keyword in ["transformation", "digital", "PMO"]:
            if keyword in current_weights:
                current = current_weights[keyword]
                proposed_delta = 0.05
                
                # Check weekly limit
                if weekly_changes[keyword] + proposed_delta > MAX_WEIGHT_CHANGE_PER_WEEK:
                    continue
                
                proposed = current + proposed_delta
                
                # Check drift ceiling
                if not check_drift_ceiling(keyword, current, proposed, original_weights):
                    continue
                
                current_weights[keyword] = proposed
                weight_adjustments.append({
                    "keyword": keyword,
                    "old": current,
                    "new": proposed,
                    "delta": proposed_delta,
                    "reason": f"High accuracy ({accuracy:.1f}%)"
                })
    
    elif accuracy < 50:
        # Low accuracy - reduce peripheral keywords
        for keyword in ["remote"]:
            if keyword in current_weights:
                current = current_weights[keyword]
                proposed_delta = -0.05
                
                # Check weekly limit
                if weekly_changes[keyword] + abs(proposed_delta) > MAX_WEIGHT_CHANGE_PER_WEEK:
                    continue
                
                proposed = current + proposed_delta
                
                # Check drift ceiling
                if not check_drift_ceiling(keyword, current, proposed, original_weights):
                    continue
                
                # Don't go below 0.5
                if proposed < 0.5:
                    continue
                
                current_weights[keyword] = proposed
                weight_adjustments.append({
                    "keyword": keyword,
                    "old": current,
                    "new": proposed,
                    "delta": proposed_delta,
                    "reason": f"Low accuracy ({accuracy:.1f}%)"
                })
    
    # Write updated weights
    if weight_adjustments and not is_dry_run():
        KEYWORD_WEIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(KEYWORD_WEIGHTS_FILE, 'w') as f:
            json.dump(current_weights, f, indent=2)
    
    return weight_adjustments


def update_source_rankings(job_accuracy, result):
    """
    Update source rankings based on which sources produced applied jobs.
    """
    # Load job recommendations with source info
    recommendations = load_jsonl(FEEDBACK_DIR / "jobs-recommended.jsonl")
    applied_ids = load_applied_job_ids()
    
    if not recommendations:
        return {}
    
    # Count by source
    source_stats = defaultdict(lambda: {"recommended": 0, "applied": 0})
    
    for rec in recommendations:
        source = rec.get("source", "unknown")
        job_id = rec.get("job_id", rec.get("id", ""))
        
        source_stats[source]["recommended"] += 1
        if job_id in applied_ids:
            source_stats[source]["applied"] += 1
    
    # Calculate rankings (applied rate)
    rankings = {}
    for source, stats in source_stats.items():
        if stats["recommended"] > 0:
            rankings[source] = {
                "recommended": stats["recommended"],
                "applied": stats["applied"],
                "rate": stats["applied"] / stats["recommended"]
            }
    
    # Sort by rate
    sorted_rankings = dict(sorted(rankings.items(), key=lambda x: x[1]["rate"], reverse=True))
    
    # Write rankings
    if sorted_rankings and not is_dry_run():
        SOURCE_RANKINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SOURCE_RANKINGS_FILE, 'w') as f:
            json.dump(sorted_rankings, f, indent=2)
    
    return sorted_rankings


def write_learning_summary(job_accuracy, briefing_actionability, skip_patterns, weight_changes, source_rankings, result):
    """Write summary for Brief Me to read."""
    summary = {
        "generated_at": now_iso(),
        "period": "last_7_days",
        "job_recommendation_accuracy": {
            "rate": job_accuracy.get("accuracy_rate"),
            "total": job_accuracy.get("total_recommendations", 0),
            "applied": job_accuracy.get("applied_count", 0)
        },
        "briefing_actionability": {
            "total_briefings": briefing_actionability.get("total_briefings", 0),
            "changes_detected": briefing_actionability.get("changes_detected", False)
        },
        "auto_adjustments": {
            "skip_patterns_added": len(skip_patterns),
            "weight_changes": len(weight_changes),
            "source_rankings_updated": bool(source_rankings)
        },
        "insights": []
    }
    
    # Generate insights
    if job_accuracy.get("accuracy_rate") is not None:
        if job_accuracy["accuracy_rate"] >= 70:
            summary["insights"].append(f"✅ Job recommendations on target ({job_accuracy['accuracy_rate']:.0f}% applied)")
        elif job_accuracy["accuracy_rate"] < 50:
            summary["insights"].append(f"⚠️ Job recommendation accuracy low ({job_accuracy['accuracy_rate']:.0f}%) — weights adjusted")
    
    if skip_patterns:
        summary["insights"].append(f"📝 Added {len(skip_patterns)} new skip patterns from feedback")
    
    if weight_changes:
        summary["insights"].append(f"⚖️ Adjusted {len(weight_changes)} keyword weights")
    
    if not is_dry_run():
        LEARNING_SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LEARNING_SUMMARY_FILE, 'w') as f:
            json.dump(summary, f, indent=2)
    
    return summary


def log_learning_run(job_accuracy, briefing_actionability, skip_patterns, weight_changes, source_rankings):
    """Append to learning-log.jsonl for audit trail."""
    entry = {
        "timestamp": now_iso(),
        "dry_run": is_dry_run(),
        "no_learn": is_no_learn(),
        "job_accuracy": {
            "rate": job_accuracy.get("accuracy_rate"),
            "total": job_accuracy.get("total_recommendations", 0),
            "applied": job_accuracy.get("applied_count", 0)
        },
        "briefing_actionability": briefing_actionability,
        "skip_patterns_added": skip_patterns,
        "weight_changes": weight_changes,
        "source_rankings_updated": list(source_rankings.keys()) if source_rankings else []
    }
    
    if not is_dry_run():
        append_jsonl(LEARNING_LOG_FILE, entry)
    
    return entry


def run_learning(result):
    """Main learning function."""
    print("[daily-learner] Analyzing feedback data...")
    
    # Check kill switch
    if is_no_learn():
        print("[daily-learner] --no-learn flag set — skipping all adjustments")
        result.set_data({
            "status": "skipped",
            "reason": "--no-learn flag active"
        })
        return
    
    # Step 1: Calculate job recommendation accuracy
    print("[daily-learner] Calculating job recommendation accuracy...")
    job_accuracy = calculate_job_recommendation_accuracy(result)
    print(f"  - Total recommendations: {job_accuracy['total_recommendations']}")
    print(f"  - Applied: {job_accuracy['applied_count']}")
    print(f"  - Accuracy: {job_accuracy['accuracy_rate']:.1f}%" if job_accuracy['accuracy_rate'] else "  - Accuracy: N/A")
    
    # Step 2: Calculate briefing actionability
    print("[daily-learner] Calculating briefing actionability...")
    briefing_actionability = calculate_briefing_actionability(result)
    print(f"  - Total briefings: {briefing_actionability['total_briefings']}")
    print(f"  - Changes detected: {briefing_actionability.get('changes_detected', 'N/A')}")
    
    # Step 3: Update skip patterns (with guard rail: 2+ signals)
    print("[daily-learner] Checking skip pattern candidates...")
    skip_patterns = update_skip_patterns(job_accuracy.get("skip_candidates", []), result)
    print(f"  - Skip patterns added: {len(skip_patterns)}")
    
    # Step 4: Update keyword weights (with guard rails)
    print("[daily-learner] Updating keyword weights...")
    weight_changes = update_keyword_weights(job_accuracy, result)
    print(f"  - Weight changes: {len(weight_changes)}")
    for change in weight_changes:
        print(f"    - {change['keyword']}: {change['old']:.2f} → {change['new']:.2f} ({change['reason']})")
    
    # Step 5: Update source rankings
    print("[daily-learner] Updating source rankings...")
    source_rankings = update_source_rankings(job_accuracy, result)
    print(f"  - Sources ranked: {len(source_rankings)}")
    
    # Step 6: Write learning summary
    print("[daily-learner] Writing learning summary...")
    summary = write_learning_summary(
        job_accuracy, briefing_actionability,
        skip_patterns, weight_changes, source_rankings, result
    )
    
    # Step 7: Log for audit trail
    print("[daily-learner] Logging run...")
    log_entry = log_learning_run(
        job_accuracy, briefing_actionability,
        skip_patterns, weight_changes, source_rankings
    )
    
    # Set result data
    result.set_data({
        "job_accuracy": job_accuracy,
        "briefing_actionability": briefing_actionability,
        "skip_patterns_added": skip_patterns,
        "weight_changes": weight_changes,
        "source_rankings": source_rankings,
        "summary": summary
    })
    
    # Set KPIs
    result.set_kpi({
        "recommendation_accuracy": job_accuracy.get("accuracy_rate"),
        "total_recommendations": job_accuracy.get("total_recommendations", 0),
        "skip_patterns_added": len(skip_patterns),
        "weight_changes": len(weight_changes)
    })
    
    print("[daily-learner] Complete!")


def main():
    """Entry point using agent_main pattern."""
    # Check for help
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        print("\nUsage: python daily-learner.py [options]")
        print("\nOptions:")
        print("  --dry-run    Print changes without writing files")
        print("  --no-learn   Skip all adjustments (kill switch)")
        print("  --help       Show this help message")
        return
    
    try:
        agent_main(
            agent_name="daily-learner",
            run_func=run_learning,
            output_path=LEARNING_DIR / "learner-output.json",
            ttl_hours=24,
            version="1.0.0"
        )
    except NameError:
        # Fallback if agent_main not available
        print("[daily-learner] Running in standalone mode (agent_main not available)")
        
        class SimpleResult:
            def __init__(self):
                self.data = {}
                self.kpi = {}
            def set_data(self, d): self.data = d
            def set_kpi(self, k): self.kpi = k
        
        result = SimpleResult()
        run_learning(result)
        
        if is_dry_run():
            print("\n[DRY RUN] Output:")
            print(json.dumps(result.data, indent=2, default=str))
        else:
            output_path = LEARNING_DIR / "learner-output.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump({"data": result.data, "kpi": result.kpi}, f, indent=2, default=str)
            print(f"\n[daily-learner] Output written to {output_path}")


if __name__ == "__main__":
    main()
