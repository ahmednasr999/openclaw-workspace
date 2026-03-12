#!/usr/bin/env python3
"""
Self-Improvement Engine
=======================
Reads system logs from the past 7 days, detects patterns, auto-fixes configs,
and promotes recurring learnings. Runs daily before the morning briefing.

Usage:
    python3 self-improvement-engine.py              # Full analysis + auto-fix
    python3 self-improvement-engine.py --dry-run    # Show what would change
    python3 self-improvement-engine.py --report     # Weekly summary report

Returns JSON with actions taken.
"""

import json, os, sys, glob, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter

WORKSPACE       = "/root/.openclaw/workspace"
SCRAPED_DIR     = f"{WORKSPACE}/jobs-bank/scraped"
LEARNINGS_FILE  = f"{WORKSPACE}/.learnings/LEARNINGS.md"
TARGETS_FILE    = f"{WORKSPACE}/config/linkedin-comment-targets.json"
COMMENTED_FILE  = f"{WORKSPACE}/linkedin/engagement/commented-posts.md"
FEEDBACK_FILE   = f"{WORKSPACE}/memory/improvement-feedback.md"
METRICS_FILE    = f"{WORKSPACE}/memory/improvement-metrics.json"

CAIRO = timezone(timedelta(hours=2))


def log(msg):
    ts = datetime.now(CAIRO).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def load_system_logs(days=7):
    """Load system log JSONs from the last N days."""
    logs = []
    today = datetime.now(CAIRO).date()
    for i in range(days):
        d = today - timedelta(days=i)
        path = f"{SCRAPED_DIR}/system-log-{d.isoformat()}.json"
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                data["_date"] = d.isoformat()
                logs.append(data)
            except:
                pass
    return logs


def load_metrics():
    """Load historical metrics for trend tracking."""
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE) as f:
            return json.load(f)
    return {"daily": [], "weekly_summaries": [], "pattern_counts": {}}


def save_metrics(metrics):
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)


def extract_daily_metrics(log_data):
    """Extract key metrics from a single day's system log."""
    ops = log_data.get("operations_summary", {})
    
    # Parse numbers from operation strings
    def extract_num(s, default=0):
        nums = re.findall(r'\d+', str(s))
        return int(nums[0]) if nums else default
    
    linkedin_str = ops.get("linkedin_found", "0")
    comments_str = ops.get("comments_drafted", "0")
    
    return {
        "date": log_data.get("_date", "unknown"),
        "posts_found": extract_num(linkedin_str),
        "comments_drafted": extract_num(comments_str),
        "errors": len(log_data.get("went_wrong", [])),
        "successes": len(log_data.get("went_right", [])),
        "layer1_working": any("Layer 1" in str(w) or "pipeline" in str(w).lower() 
                             for w in log_data.get("went_right", [])),
        "layer2_working": any("Layer 2" in str(w) or "recruiter" in str(w).lower() 
                             for w in log_data.get("went_right", [])),
        "layer3_working": any("Layer 3" in str(w) or "industry" in str(w).lower() 
                             for w in log_data.get("went_right", [])),
    }


def detect_patterns(logs, metrics):
    """Analyze logs for recurring issues and improvement opportunities."""
    patterns = []
    daily_data = [extract_daily_metrics(l) for l in logs]
    
    if not daily_data:
        return patterns
    
    # Pattern 1: Layer drought (any layer returning 0 for 3+ consecutive days)
    for layer_key, layer_name in [
        ("layer1_working", "Layer 1 (Pipeline Companies)"),
        ("layer2_working", "Layer 2 (Recruiters)"),
        ("layer3_working", "Layer 3 (Industry)")
    ]:
        consecutive_zeros = 0
        for d in daily_data:
            if not d.get(layer_key, False):
                consecutive_zeros += 1
            else:
                break
        if consecutive_zeros >= 3:
            patterns.append({
                "type": "layer_drought",
                "layer": layer_name,
                "days": consecutive_zeros,
                "severity": "high",
                "action": "rotate_search_queries",
                "detail": f"{layer_name} returned 0 posts for {consecutive_zeros} consecutive days. Search queries need rotation."
            })
    
    # Pattern 2: Comment quality declining (fewer comments drafted vs posts found)
    recent_ratios = []
    for d in daily_data[:3]:
        if d["posts_found"] > 0:
            recent_ratios.append(d["comments_drafted"] / d["posts_found"])
    if recent_ratios and sum(recent_ratios) / len(recent_ratios) < 0.5:
        patterns.append({
            "type": "comment_quality_drop",
            "severity": "medium",
            "action": "review_comment_prompt",
            "detail": f"Comment draft success rate below 50%. Average: {sum(recent_ratios)/len(recent_ratios):.0%}"
        })
    
    # Pattern 3: Dedup exhaustion (posts found trending to 0)
    if len(daily_data) >= 3:
        recent_posts = [d["posts_found"] for d in daily_data[:3]]
        if all(p <= 2 for p in recent_posts):
            patterns.append({
                "type": "dedup_exhaustion",
                "severity": "medium",
                "action": "expand_search_terms",
                "detail": f"Posts found declining: {recent_posts}. Dedup log may be exhausting available posts."
            })
    
    # Pattern 4: Recurring errors
    all_errors = []
    for l in logs:
        for err in l.get("went_wrong", []):
            if isinstance(err, dict):
                all_errors.append(err.get("issue", str(err)))
            else:
                all_errors.append(str(err))
    
    error_counts = Counter(all_errors)
    for error, count in error_counts.items():
        if count >= 3:
            patterns.append({
                "type": "recurring_error",
                "severity": "high",
                "action": "auto_fix_or_escalate",
                "detail": f"Error occurred {count} times in {len(logs)} days: {error[:100]}",
                "error": error
            })
    
    # Pattern 5: Zero errors streak (things are going well)
    error_free_days = sum(1 for d in daily_data if d["errors"] == 0)
    if error_free_days >= 5:
        patterns.append({
            "type": "stability_streak",
            "severity": "info",
            "action": "none",
            "detail": f"{error_free_days} error-free days in last {len(daily_data)} days. System stable."
        })
    
    # Pattern 6: Commented posts log growing large (dedup pressure)
    if os.path.exists(COMMENTED_FILE):
        with open(COMMENTED_FILE) as f:
            lines = f.readlines()
        url_count = sum(1 for l in lines if l.strip().startswith("- URL:"))
        if url_count > 100:
            patterns.append({
                "type": "dedup_log_large",
                "severity": "low",
                "action": "prune_old_entries",
                "detail": f"Commented posts log has {url_count} entries. Consider pruning entries older than 30 days."
            })
    
    return patterns


def apply_fixes(patterns, dry_run=False):
    """Auto-apply fixes for detected patterns."""
    actions_taken = []
    
    for p in patterns:
        if p["type"] == "layer_drought" and p["action"] == "rotate_search_queries":
            action = rotate_layer_queries(p["layer"], dry_run)
            if action:
                actions_taken.append(action)
        
        elif p["type"] == "dedup_exhaustion" and p["action"] == "expand_search_terms":
            action = expand_search_terms(dry_run)
            if action:
                actions_taken.append(action)
        
        elif p["type"] == "dedup_log_large" and p["action"] == "prune_old_entries":
            action = prune_old_dedup(dry_run)
            if action:
                actions_taken.append(action)
        
        elif p["type"] == "recurring_error" and p["action"] == "auto_fix_or_escalate":
            action = log_recurring_error(p["error"], dry_run)
            if action:
                actions_taken.append(action)
    
    return actions_taken


def rotate_layer_queries(layer_name, dry_run=False):
    """Rotate search queries for a struggling layer."""
    if not os.path.exists(TARGETS_FILE):
        return None
    
    with open(TARGETS_FILE) as f:
        targets = json.load(f)
    
    # Add variation terms to struggling layer
    rotation_terms = {
        "Layer 1": [
            "proud to announce", "we are hiring", "team milestone",
            "digital transformation results", "my journey at"
        ],
        "Layer 2": [
            "executive search", "confidential mandate", "leadership opportunity",
            "C-suite placement", "just placed"
        ],
        "Layer 3": [
            "AI in healthcare", "digital transformation GCC", "future of fintech",
            "Saudi Vision 2030 technology", "enterprise AI deployment"
        ]
    }
    
    layer_key = None
    for k in ["Layer 1", "Layer 2", "Layer 3"]:
        if k in layer_name:
            layer_key = k
            break
    
    if not layer_key or layer_key not in rotation_terms:
        return None
    
    if dry_run:
        return {
            "action": f"Would rotate {layer_key} search queries",
            "new_terms": rotation_terms[layer_key],
            "applied": False
        }
    
    # Add rotation flag to targets
    for layer in targets.get("layers", []):
        if layer_key.lower().replace(" ", "") in layer.get("name", "").lower().replace(" ", ""):
            if "rotation_terms" not in layer:
                layer["rotation_terms"] = []
            layer["rotation_terms"].extend(rotation_terms[layer_key])
            layer["rotation_terms"] = list(set(layer["rotation_terms"]))
            layer["last_rotated"] = datetime.now(CAIRO).isoformat()
    
    with open(TARGETS_FILE, "w") as f:
        json.dump(targets, f, indent=2)
    
    return {
        "action": f"Rotated {layer_key} search queries",
        "new_terms": rotation_terms[layer_key],
        "applied": True
    }


def expand_search_terms(dry_run=False):
    """Expand search scope when dedup exhaustion is detected."""
    if dry_run:
        return {"action": "Would expand search terms for dedup exhaustion", "applied": False}
    
    # Add new hashtags/topics to search
    expansion_topics = [
        "digital health innovation GCC",
        "enterprise architecture Middle East",
        "healthcare technology transformation",
        "AI strategy implementation",
        "PMO leadership excellence"
    ]
    
    # Write expansion to a config that the orchestrator reads
    expansion_file = f"{WORKSPACE}/config/search-expansion.json"
    existing = {}
    if os.path.exists(expansion_file):
        with open(expansion_file) as f:
            existing = json.load(f)
    
    existing["expanded_topics"] = expansion_topics
    existing["expanded_at"] = datetime.now(CAIRO).isoformat()
    existing["reason"] = "dedup_exhaustion_detected"
    
    with open(expansion_file, "w") as f:
        json.dump(existing, f, indent=2)
    
    return {"action": "Expanded search terms", "topics": expansion_topics, "applied": True}


def prune_old_dedup(dry_run=False, max_age_days=30):
    """Remove dedup entries older than max_age_days."""
    if not os.path.exists(COMMENTED_FILE):
        return None
    
    with open(COMMENTED_FILE) as f:
        content = f.read()
    
    lines = content.split("\n")
    cutoff = datetime.now(CAIRO).date() - timedelta(days=max_age_days)
    
    kept = []
    skip_block = False
    removed = 0
    
    for line in lines:
        # Check date lines
        date_match = re.search(r'Date: (\d{4}-\d{2}-\d{2})', line)
        if date_match:
            entry_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
            if entry_date < cutoff:
                skip_block = True
                removed += 1
                continue
            else:
                skip_block = False
        
        if skip_block and line.startswith("- "):
            continue
        elif skip_block and line.strip() == "":
            skip_block = False
            continue
        
        kept.append(line)
    
    if removed == 0:
        return None
    
    if dry_run:
        return {"action": f"Would prune {removed} entries older than {max_age_days} days", "applied": False}
    
    with open(COMMENTED_FILE, "w") as f:
        f.write("\n".join(kept))
    
    return {"action": f"Pruned {removed} dedup entries older than {max_age_days} days", "applied": True}


def log_recurring_error(error_text, dry_run=False):
    """Log recurring error to LEARNINGS.md for human review."""
    if dry_run:
        return {"action": f"Would log recurring error to LEARNINGS.md", "error": error_text[:80], "applied": False}
    
    # Check if already logged
    if os.path.exists(LEARNINGS_FILE):
        with open(LEARNINGS_FILE) as f:
            existing = f.read()
        if error_text[:50] in existing:
            return None  # Already logged
    
    today = datetime.now(CAIRO).strftime("%Y%m%d")
    entry = f"""
## [LRN-{today}-AUTO] Recurring pipeline error (auto-detected)
**Date:** {datetime.now(CAIRO).strftime('%Y-%m-%d')}
**Category:** Auto-detected
**What happened:** Error occurred 3+ times in 7 days: {error_text[:200]}
**Action needed:** Manual review required. Check orchestrator logs.
**Auto-promoted:** Yes (self-improvement engine)
"""
    
    with open(LEARNINGS_FILE, "a") as f:
        f.write(entry)
    
    return {"action": "Logged recurring error to LEARNINGS.md", "error": error_text[:80], "applied": True}


def update_feedback_file(patterns, actions, daily_data):
    """Write human-readable feedback summary."""
    today = datetime.now(CAIRO).strftime("%Y-%m-%d %H:%M")
    
    content = f"\n---\n\n## Self-Improvement Run: {today}\n\n"
    
    # Metrics summary
    if daily_data:
        latest = daily_data[0] if daily_data else {}
        content += f"**Latest metrics:** {latest.get('posts_found', 0)} posts found, "
        content += f"{latest.get('comments_drafted', 0)} comments drafted, "
        content += f"{latest.get('errors', 0)} errors\n\n"
    
    # Patterns detected
    if patterns:
        content += "**Patterns detected:**\n"
        for p in patterns:
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(p["severity"], "")
            content += f"- {icon} [{p['severity'].upper()}] {p['detail']}\n"
        content += "\n"
    else:
        content += "**No patterns detected.** System operating normally.\n\n"
    
    # Actions taken
    if actions:
        content += "**Actions taken:**\n"
        for a in actions:
            status = "✅" if a.get("applied") else "🔍 (dry run)"
            content += f"- {status} {a['action']}\n"
        content += "\n"
    
    # Ensure file exists
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w") as f:
            f.write("# Improvement Feedback Log\n\nAuto-generated by self-improvement engine.\n")
    
    with open(FEEDBACK_FILE, "a") as f:
        f.write(content)


def generate_weekly_report(logs, metrics):
    """Generate weekly summary for Sunday review."""
    daily_data = [extract_daily_metrics(l) for l in logs]
    
    if not daily_data:
        return "No data available for weekly report."
    
    total_posts = sum(d["posts_found"] for d in daily_data)
    total_comments = sum(d["comments_drafted"] for d in daily_data)
    total_errors = sum(d["errors"] for d in daily_data)
    days_with_data = len(daily_data)
    
    report = f"""
## Weekly Self-Improvement Report
**Period:** Last {days_with_data} days
**Generated:** {datetime.now(CAIRO).strftime('%Y-%m-%d %H:%M')}

### Performance Metrics
- Total posts found: {total_posts} (avg {total_posts/max(days_with_data,1):.1f}/day)
- Total comments drafted: {total_comments} (avg {total_comments/max(days_with_data,1):.1f}/day)
- Total errors: {total_errors} (avg {total_errors/max(days_with_data,1):.1f}/day)
- Error-free days: {sum(1 for d in daily_data if d['errors']==0)}/{days_with_data}

### Layer Health
- Layer 1 (Pipeline): {'Active' if any(d.get('layer1_working') for d in daily_data) else 'Inactive'} ({sum(1 for d in daily_data if d.get('layer1_working'))}/{days_with_data} days)
- Layer 2 (Recruiters): {'Active' if any(d.get('layer2_working') for d in daily_data) else 'Inactive'} ({sum(1 for d in daily_data if d.get('layer2_working'))}/{days_with_data} days)
- Layer 3 (Industry): {'Active' if any(d.get('layer3_working') for d in daily_data) else 'Inactive'} ({sum(1 for d in daily_data if d.get('layer3_working'))}/{days_with_data} days)

### Trend
"""
    for d in daily_data:
        status = "✅" if d["errors"] == 0 else "⚠️"
        report += f"- {d['date']}: {status} {d['posts_found']} posts, {d['comments_drafted']} comments, {d['errors']} errors\n"
    
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", action="store_true", help="Generate weekly report")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    
    log("=== Self-Improvement Engine ===")
    
    # Load data
    logs = load_system_logs(days=7)
    metrics = load_metrics()
    log(f"Loaded {len(logs)} system logs from last 7 days")
    
    if not logs:
        log("No system logs found. Nothing to analyze.")
        if args.json:
            print(json.dumps({"patterns": [], "actions": [], "status": "no_data"}))
        return
    
    # Extract daily metrics
    daily_data = [extract_daily_metrics(l) for l in logs]
    
    # Save daily metrics to history
    for d in daily_data:
        if d["date"] not in [m.get("date") for m in metrics.get("daily", [])]:
            metrics.setdefault("daily", []).append(d)
    # Keep only last 90 days
    metrics["daily"] = sorted(metrics["daily"], key=lambda x: x["date"], reverse=True)[:90]
    
    if args.report:
        report = generate_weekly_report(logs, metrics)
        print(report)
        save_metrics(metrics)
        return
    
    # Detect patterns
    patterns = detect_patterns(logs, metrics)
    log(f"Detected {len(patterns)} patterns")
    for p in patterns:
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(p["severity"], "")
        log(f"  {icon} {p['type']}: {p['detail'][:80]}")
    
    # Apply fixes
    actions = apply_fixes(patterns, dry_run=args.dry_run)
    log(f"Applied {len(actions)} fixes")
    for a in actions:
        status = "✅" if a.get("applied") else "🔍"
        log(f"  {status} {a['action']}")
    
    # Update tracking
    update_feedback_file(patterns, actions, daily_data)
    
    # Track pattern counts for promotion logic
    for p in patterns:
        key = p["type"]
        metrics.setdefault("pattern_counts", {})[key] = metrics.get("pattern_counts", {}).get(key, 0) + 1
    
    save_metrics(metrics)
    log("Done.")
    
    if args.json:
        print(json.dumps({
            "patterns": patterns,
            "actions": actions,
            "daily_metrics": daily_data,
            "status": "ok"
        }, indent=2))


if __name__ == "__main__":
    main()
