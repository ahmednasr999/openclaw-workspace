#!/usr/bin/env python3
"""
Sync Notion Content Calendar → Ontology Graph (LinkedInPost entities)
Runs on: cron daily OR called from morning-briefing-orchestrator.py

Usage: python3 scripts/ontology-notion-sync.py
"""

import json
import urllib.request
import ssl
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path("/root/.openclaw/workspace")
GRAPH_FILE = WORKSPACE / "memory/ontology/graph.jsonl"
NOTION_CONFIG = WORKSPACE / "config/notion.json"
CONTENT_DB_ID = "3268d599-a162-814b-8854-c9b8bde62468"

ctx = ssl.create_default_context()

def load_token():
    return json.loads(NOTION_CONFIG.read_text())["token"]

def notion_request(url, body=None, method="POST"):
    token = load_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    resp = urllib.request.urlopen(req, timeout=20, context=ctx)
    return json.loads(resp.read())

def load_graph_post_ids():
    """Return set of Notion page IDs already in graph."""
    ids = set()
    if not GRAPH_FILE.exists():
        return ids
    with open(GRAPH_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("op") == "create" and entry.get("entity", {}).get("type") == "LinkedInPost":
                notion_id = entry["entity"]["properties"].get("notion_id")
                if notion_id:
                    ids.add(notion_id)
    return ids

def fetch_notion_posts():
    """Fetch all posts from Notion Content Calendar DB."""
    posts = []
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        result = notion_request(
            f"https://api.notion.com/v1/databases/{CONTENT_DB_ID}/query",
            body
        )
        for page in result.get("results", []):
            props = page.get("properties", {})

            def text(prop_name):
                p = props.get(prop_name, {})
                if p.get("type") == "title":
                    items = p.get("title", [])
                elif p.get("type") == "rich_text":
                    items = p.get("rich_text", [])
                else:
                    return None
                return "".join(i.get("plain_text", "") for i in items) or None

            def select(prop_name):
                p = props.get(prop_name, {})
                sel = p.get("select")
                return sel.get("name") if sel else None

            def date_prop(prop_name):
                p = props.get(prop_name, {})
                d = p.get("date")
                return d.get("start") if d else None

            def url_prop(prop_name):
                p = props.get(prop_name, {})
                return p.get("url")

            status_raw = select("Status") or "idea"
            status_map = {
                "Posted": "posted",
                "Scheduled": "scheduled",
                "Drafted": "draft",
                "Draft": "draft",
                "Review": "draft",
                "Idea": "idea",
            }
            status = status_map.get(status_raw, "idea")

            posts.append({
                "notion_id": page["id"].replace("-", ""),
                "title": text("Title") or text("Hook") or "Untitled",
                "hook": text("Hook"),
                "topic": select("Topic"),
                "status": status,
                "planned_date": date_prop("Planned Date"),
                "posted_date": date_prop("Planned Date") if status == "posted" else None,
                "post_url": url_prop("Post URL"),
            })

        if not result.get("has_more"):
            break
        cursor = result.get("next_cursor")

    return posts

def sync():
    now = datetime.now(timezone.utc).isoformat()
    existing_ids = load_graph_post_ids()
    posts = fetch_notion_posts()

    new_entries = []
    updated = 0
    skipped = 0

    for post in posts:
        notion_id = post["notion_id"]

        if notion_id in existing_ids:
            # Update status in graph via update op
            new_entries.append({
                "op": "update",
                "entity": {
                    "id": f"post_notion_{notion_id[:12]}",
                    "type": "LinkedInPost",
                    "properties": {
                        "status": post["status"],
                        "post_url": post.get("post_url"),
                    },
                    "updated": now
                }
            })
            updated += 1
        else:
            new_entries.append({
                "op": "create",
                "entity": {
                    "id": f"post_notion_{notion_id[:12]}",
                    "type": "LinkedInPost",
                    "properties": {k: v for k, v in {
                        "notion_id": notion_id,
                        "title": post["title"],
                        "hook": post["hook"],
                        "topic": post["topic"],
                        "status": post["status"],
                        "planned_date": post["planned_date"],
                        "posted_date": post["posted_date"],
                        "post_url": post["post_url"],
                    }.items() if v is not None},
                    "created": now,
                    "updated": now
                }
            })

    with open(GRAPH_FILE, "a") as f:
        for entry in new_entries:
            f.write(json.dumps(entry) + "\n")

    new_count = len([e for e in new_entries if e["op"] == "create"])
    print(f"✅ Notion sync: {new_count} new | {updated} updated | {len(posts)} total posts in Notion")
    return {"new": new_count, "updated": updated, "total": len(posts)}

if __name__ == "__main__":
    sync()
