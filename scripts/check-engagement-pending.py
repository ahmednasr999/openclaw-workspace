#!/usr/bin/env python3
import json, sys

try:
    with open("/root/.openclaw/workspace/data/linkedin-engagement-pending.json") as f:
        d = json.load(f)
except FileNotFoundError:
    print("No pending file")
    sys.exit(0)

posts = d.get('posts', [])
approved = [p for p in posts if p.get('approved') and not p.get('posted')]
pending = [p for p in posts if not p.get('approved') and not p.get('posted')]

print(f"Approved (awaiting posting): {len(approved)}")
for p in approved[:5]:
    print(f"  - {p.get('title','?')[:60]} | {p.get('author','?')}")

print(f"Pending (awaiting approval): {len(pending)}")
for p in pending[:5]:
    print(f"  - {p.get('title','?')[:60]} | {p.get('author','?')}")

print(f"\nQueue date: {d.get('date','unknown')}")
print(f"Total posts in file: {len(posts)}")
