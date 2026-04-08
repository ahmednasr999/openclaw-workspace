#!/usr/bin/env python3
"""Build index.json and lessons.md from trace-log.jsonl"""
import json, os
from datetime import datetime, timezone

TRACES_DIR = "/root/.openclaw/workspace/memory/agent-traces"

def main():
    log_path = os.path.join(TRACES_DIR, "trace-log.jsonl")
    index_path = os.path.join(TRACES_DIR, "index.json")
    lessons_path = os.path.join(TRACES_DIR, "lessons.md")

    traces = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    traces.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # Filter out expired traces
    now = datetime.now(timezone.utc).isoformat()
    active = [t for t in traces if not t.get("expires") or t["expires"] > now]

    # Build category index
    by_category = {}
    for t in active:
        cat = t.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append({
            "id": t["id"],
            "agent": t["agent"],
            "timestamp": t["timestamp"],
            "lesson": t.get("lesson", ""),
            "severity": "high" if t["outcome"] == "failed" else "medium"
        })

    # Recent entries (last 50)
    recent = [{
        "id": t["id"],
        "agent": t["agent"],
        "category": t.get("category", "unknown"),
        "lesson": t.get("lesson", ""),
        "timestamp": t["timestamp"]
    } for t in active[-50:]]

    index = {
        "updated_at": now,
        "total_traces": len(active),
        "by_category": by_category,
        "recent": recent
    }

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    # Build lessons.md — curated from high-severity unique lessons
    lessons = []
    seen = set()
    for t in active:
        lesson = t.get("lesson", "").strip()
        if lesson and lesson not in seen:
            seen.add(lesson)
            lessons.append({"category": t.get("category", "unknown"), "lesson": lesson, "agent": t["agent"], "timestamp": t["timestamp"]})

    # Group by category
    by_cat_lessons = {}
    for l in lessons:
        cat = l["category"]
        if cat not in by_cat_lessons:
            by_cat_lessons[cat] = []
        prefix = "✅ " if "always" in l["lesson"].lower() else "❌ "
        by_cat_lessons[cat].append(f"- {prefix}{l['lesson']} ({l['agent']}, {l['timestamp'][:10]})")

    with open(lessons_path, "w") as f:
        f.write("# Agent Lessons Learned\n\n")
        f.write(f"*Auto-curated from agent traces. Updated: {now[:10]}*\n\n")
        for cat in sorted(by_cat_lessons.keys()):
            f.write(f"## {cat.replace('_', ' ').title()}\n")
            for line in by_cat_lessons[cat]:
                f.write(line + "\n")
            f.write("\n")

    print(f"Index: {len(active)} active traces, {len(by_category)} categories")
    print(f"Lessons: {len(lessons)} unique lessons across {len(by_cat_lessons)} categories")

if __name__ == "__main__":
    main()
