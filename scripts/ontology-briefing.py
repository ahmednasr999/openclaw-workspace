#!/usr/bin/env python3
"""
Unified morning briefing query from ontology graph.
Replaces reading 4 separate coordination/*.json files.

Usage: python3 scripts/ontology-briefing.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, date

WORKSPACE = Path("/root/.openclaw/workspace")
GRAPH_FILE = WORKSPACE / "memory/ontology/graph.jsonl"

def load_graph():
    entities = {}
    relations = []
    if not GRAPH_FILE.exists():
        return entities, relations
    with open(GRAPH_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("op") == "create":
                e = entry["entity"]
                entities[e["id"]] = e
            elif entry.get("op") == "relate":
                relations.append(entry)
            elif entry.get("op") == "update":
                e = entry["entity"]
                if e["id"] in entities:
                    entities[e["id"]]["properties"].update(e.get("properties", {}))
                    entities[e["id"]]["updated"] = e.get("updated", "")
    # Dedup: if same title appears in both old JSON posts AND Notion posts, keep Notion
    notion_titles = {
        e["properties"].get("title", "").lower()
        for e in entities.values()
        if e["type"] == "LinkedInPost" and e["id"].startswith("post_notion_")
    }
    to_remove = [
        eid for eid, e in entities.items()
        if e["type"] == "LinkedInPost"
        and not eid.startswith("post_notion_")
        and e["properties"].get("title", "").lower() in notion_titles
    ]
    for eid in to_remove:
        del entities[eid]
    return entities, relations

def by_type(entities, type_name):
    return [e for e in entities.values() if e["type"] == type_name]

def fmt_date(d):
    if not d:
        return ""
    try:
        return datetime.fromisoformat(d.replace("Z","")).strftime("%b %d")
    except:
        return d

def main():
    entities, relations = load_graph()
    today = date.today().isoformat()

    print("=" * 60)
    print(f"🎯 NASR COMMAND CENTER — Daily Briefing")
    print(f"   {datetime.now().strftime('%A, %B %d %Y')}")
    print("=" * 60)

    # ── 1. JOB PIPELINE ──────────────────────────────────────────
    applications = by_type(entities, "JobApplication")
    active = [a for a in applications if a["properties"].get("status") not in ("rejected", "withdrawn")]
    interviews = [a for a in active if a["properties"].get("status") == "interview"]
    applied = [a for a in active if a["properties"].get("status") == "applied"]

    print(f"\n📋 JOB PIPELINE ({len(active)} active)")
    if interviews:
        print(f"   🔥 Interviews ({len(interviews)}):")
        for a in interviews:
            p = a["properties"]
            print(f"      • {p['title']} @ {p['company']} — interview: {fmt_date(p.get('interview_date',''))}")
    if applied:
        print(f"   📤 Applied ({len(applied)}):")
        for a in applied:
            p = a["properties"]
            follow = f" | follow-up: {fmt_date(p.get('follow_up_date',''))}" if p.get('follow_up_date') else ""
            score = f" [{p['fit_score']}]" if p.get('fit_score') else ""
            print(f"      • {p['title']} @ {p['company']}{score}{follow}")

    # ── 2. OUTREACH ───────────────────────────────────────────────
    outreach = by_type(entities, "Outreach")
    high_priority = [o for o in outreach if o["properties"].get("priority") == "high"]
    needs_action = [o for o in outreach if o["properties"].get("next_action") in ("send_connection", "follow_up", "message")]

    print(f"\n🤝 OUTREACH ({len(outreach)} total | {len(high_priority)} high priority)")
    if needs_action:
        print(f"   ⚡ Action needed ({len(needs_action)}):")
        for o in needs_action:
            p = o["properties"]
            print(f"      • {p['person']} @ {p['company']} → {p.get('next_action','')}")

    # ── 3. CONTENT ────────────────────────────────────────────────
    posts = by_type(entities, "LinkedInPost")
    scheduled = [p for p in posts if p["properties"].get("status") == "scheduled"]
    drafts = [p for p in posts if p["properties"].get("status") == "draft"]
    ideas = [p for p in posts if p["properties"].get("status") == "idea"]

    print(f"\n✍️  CONTENT PIPELINE")
    if scheduled:
        print(f"   📅 Scheduled ({len(scheduled)}):")
        for p in scheduled:
            pp = p["properties"]
            print(f"      • {pp['title']} — {fmt_date(pp.get('planned_date',''))}")
    if drafts:
        print(f"   📝 Drafts ready ({len(drafts)}):")
        for p in drafts:
            print(f"      • {p['properties']['title']}")
    if ideas:
        print(f"   💡 Ideas ({len(ideas)}): {', '.join(p['properties']['title'] for p in ideas)}")

    # ── 4. TASKS ──────────────────────────────────────────────────
    tasks = by_type(entities, "Task")
    open_tasks = [t for t in tasks if t["properties"].get("status") in ("open", "in_progress")]
    if open_tasks:
        print(f"\n✅ OPEN TASKS ({len(open_tasks)})")
        for t in open_tasks:
            p = t["properties"]
            print(f"   • [{p.get('priority','med').upper()}] {p['title']}")

    # ── 5. SUMMARY ────────────────────────────────────────────────
    print(f"\n📊 SUMMARY")
    print(f"   Applications: {len(active)} active | {len(interviews)} at interview stage")
    print(f"   Outreach: {len(needs_action)} actions pending")
    print(f"   Content: {len(scheduled)} scheduled | {len(drafts)} drafts | {len(ideas)} ideas")
    print(f"   Graph: {len(entities)} entities total")
    print("=" * 60)

if __name__ == "__main__":
    main()
