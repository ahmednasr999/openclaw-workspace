#!/usr/bin/env python3
import json
import urllib.request

with open("/root/.openclaw/workspace/config/notion.json") as f:
    token = __import__('json').load(f)["token"]

db_id = "3268d599-a162-814b-8854-c9b8bde62468"
url = f"https://api.notion.com/v1/databases/{db_id}/query"

payload = json.dumps({
    "filter": {"property": "Status", "select": {"equals": "Scheduled"}},
    "sorts": [{"property": "Planned Date", "direction": "ascending"}],
    "page_size": 10
}).encode()

req = urllib.request.Request(url, data=payload, method="POST")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Notion-Version", "2022-06-28")
req.add_header("Content-Type", "application/json")

with urllib.request.urlopen(req) as resp:
    d = json.load(resp)

results = d.get("results", [])
print(f"Scheduled posts: {len(results)}\n")
for p in results:
    pid = p["id"]
    date = p["properties"].get("Planned Date", {}).get("date", {})
    date_str = date.get("start", "no date") if date else "no date"
    title = "".join(t.get("plain_text", "") for t in p["properties"].get("Name", {}).get("title", []))
    image = p["properties"].get("Image URL", {}).get("url", "no image")
    print(f"{date_str} | {title[:60]}")
    print(f"  id: {pid}")
    print(f"  image: {image[:80] if image else 'none'}")
    print()
