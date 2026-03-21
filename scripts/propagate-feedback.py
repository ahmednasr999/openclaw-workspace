#!/usr/bin/env python3
"""
Feedback Propagation Agent - Cross-agent correction sharing.
Inspired by Shubham Saboo: "One correction fixes all Agents."

When Ahmed gives feedback on one agent's output, this propagates
the correction to related agents so they learn from it too.

Propagation map (which agents share voice/style):
  writer       → linkedin_comment, content
  linkedin_post → writer, linkedin_comment
  cv           → cv only (specialized, no propagation)
  research     → research only
  outreach     → outreach only
  chief_of_staff → chief_of_staff only

Usage:
  python3 propagate-feedback.py                    # Run propagation check
  python3 propagate-feedback.py --dry-run          # Preview what would change
  python3 propagate-feedback.py --agent writer --reason "tone too corporate"
"""

import json, re, sys, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
FEEDBACK_FILE = WORKSPACE / "data/agent-feedback/feedback.jsonl"
AGENTS_DIR = WORKSPACE / "agents"
PROPAGATION_LOG = WORKSPACE / "data/agent-feedback/propagation-log.jsonl"

# Which agents share context and should receive corrections from each other
PROPAGATION_MAP = {
    "writer": ["linkedin_comment", "content", "outreach"],
    "linkedin_post": ["writer", "linkedin_comment"],
    "linkedin_comment": ["writer", "linkedin_post"],
    "chief_of_staff": [],
    "cv": [],
    "research": [],
    "scheduler": [],
    "narrator": [],  # briefing narrator shares voice
}

# Patterns that signal a style/voice correction (not just a task error)
VOICE_CORRECTION_PATTERNS = [
    "tone", "voice", "corporate", "stiff", "formal", "boring",
    "generic", "sounds like", "not me", "not Ahmed", "too much like",
    "overly", "bland", "dry", "robotic", "fluffy", "vague",
    "too long", "too short", "格式", "voice",
]

# Patterns that signal a task-specific error (don't propagate)
TASK_ERROR_PATTERNS = [
    "wrong person", "wrong company", "wrong date", "wrong number",
    "misspelled", "typo", "broken link", "wrong url", "404",
    "wrong format", "missing field", "wrong data",
]


def should_propagate(reason):
    """Check if this correction is a voice/style issue (should propagate)."""
    reason_lower = reason.lower()
    # If it's a task error, don't propagate
    for p in TASK_ERROR_PATTERNS:
        if p in reason_lower:
            return False
    # If it's a voice/style signal, propagate
    for p in VOICE_CORRECTION_PATTERNS:
        if p in reason_lower:
            return True
    return False


def get_propagation_targets(source_agent):
    """Get list of agents that should receive corrections from source."""
    return PROPAGATION_MAP.get(source_agent, [])


def extract_correction(summary_text):
    """Extract the core correction from a reason string."""
    # Clean up the reason
    text = re.sub(r'^[\s\-:]+', '', summary_text.strip())
    text = re.sub(r'\.$', '', text)
    return text[:200]


def current_soul_content(soul_path):
    """Read current SOUL.md content."""
    try:
        return open(soul_path).read()
    except:
        return ""


def append_to_soul(soul_path, correction_entry):
    """Append a propagation correction to a SOUL.md file."""
    if not soul_path.exists():
        return False, f"File not found: {soul_path}"

    content = current_soul_content(soul_path)
    ts = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d")

    # Check if this exact correction already exists (avoid duplicates)
    if correction_entry["correction"][:80] in content:
        return False, "Correction already present"

    # Find the ## Anti-Patterns section and add before it
    marker = f"\n\n<!-- PROPGATED:{ts} -->\n"
    new_section = f"{marker}### Voice Correction (propagated from {correction_entry['source_agent']})\n- {correction_entry['correction']}\n"

    if "## Anti-Patterns" in content:
        content = content.replace("## Anti-Patterns", f"{new_section}## Anti-Patterns")
    else:
        content += f"\n{new_section}"

    with open(soul_path, "w") as f:
        f.write(content)

    return True, "Appended to SOUL.md"


def propagate_correction(source_agent, reason):
    """Propagate a voice correction to related agents."""
    if not should_propagate(reason):
        return []

    targets = get_propagation_targets(source_agent)
    if not targets:
        return []

    correction = extract_correction(reason)
    results = []
    ts = datetime.now(timezone(timedelta(hours=2))).isoformat()

    entry = {
        "ts": ts,
        "source_agent": source_agent,
        "correction": correction,
        "targets": targets,
    }

    for target in targets:
        soul_path = AGENTS_DIR / target / "SOUL.md"
        if soul_path.exists():
            success, msg = append_to_soul(soul_path, entry)
            results.append({
                "target": target,
                "file": str(soul_path),
                "success": success,
                "message": msg,
            })
        else:
            results.append({
                "target": target,
                "file": str(soul_path),
                "success": False,
                "message": "SOUL.md not found for this agent",
            })

    # Log propagation
    log_entry = {**entry, "results": results}
    with open(PROPAGATION_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return results


def run_propagation(dry_run=False):
    """Read recent feedback and propagate corrections."""
    if not FEEDBACK_FILE.exists():
        print("No feedback file found.")
        return []

    # Read last 7 days of feedback
    cutoff = datetime.now(timezone(timedelta(hours=2))) - timedelta(days=7)
    recent_entries = []

    for line in open(FEEDBACK_FILE):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            ts = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
            if ts >= cutoff:
                recent_entries.append(e)
        except:
            pass

    # Find corrections that should propagate
    corrections_run = []
    seen_corrections = set()

    for e in recent_entries:
        if e.get("status") not in ("revised", "rejected"):
            continue
        reason = e.get("reason", "")
        if not reason:
            continue

        agent = e.get("agent", "")
        key = f"{agent}:{reason[:50]}"
        if key in seen_corrections:
            continue
        seen_corrections.add(key)

        if should_propagate(reason):
            results = propagate_correction(agent, reason)
            if results:
                corrections_run.append({
                    "agent": agent,
                    "reason": reason,
                    "results": results,
                })

    return corrections_run


def show_propagation_plan():
    """Show what would be propagated without making changes."""
    if not FEEDBACK_FILE.exists():
        print("No feedback file found.")
        return

    cutoff = datetime.now(timezone(timedelta(hours=2))) - timedelta(days=7)

    corrections = []
    for line in open(FEEDBACK_FILE):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            ts = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
            if ts < cutoff:
                continue
            if e.get("status") not in ("revised", "rejected"):
                continue
            reason = e.get("reason", "")
            if reason and should_propagate(reason):
                corrections.append(e)
        except:
            pass

    if not corrections:
        print("No voice corrections found to propagate.")
        return

    print(f"Found {len(corrections)} voice corrections to propagate:\n")
    for e in corrections:
        agent = e.get("agent", "?")
        reason = e.get("reason", "?")
        targets = get_propagation_targets(agent)
        print(f"  [{agent}] -> {targets}")
        print(f"    Reason: {reason[:100]}")
        print()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== Propagation Plan (dry run) ===\n")
        show_propagation_plan()
    else:
        print("=== Running Feedback Propagation ===")
        results = run_propagation()

        if not results:
            print("No corrections propagated.")
        else:
            print(f"Propagated {len(results)} correction(s):")
            for r in results:
                print(f"\n  From: {r['agent']}")
                print(f"  Reason: {r['reason'][:80]}")
                for res in r["results"]:
                    emoji = "✅" if res["success"] else "❌"
                    print(f"    {emoji} {res['target']}: {res['message']}")
