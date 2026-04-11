#!/usr/bin/env python3
import json

with open("/root/.openclaw/workspace/data/linkedin-research-log.json") as f:
    d = json.load(f)

posts = d.get("posts", [])
print(f"Total posts in research log: {len(posts)}")
print()
for p in posts:
    date = p.get("date", "?")
    title = p.get("post_text", "")[:60].replace("\n", " ")
    score = p.get("score", "?")
    url = p.get("post_url", "no url")
    print(f"{date} | score={score} | url={'yes' if 'linkedin' in url else 'no'} | {title}")
