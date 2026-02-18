#!/usr/bin/env python3
"""
Persistent Notion Database Creator
Creates Skills Deep Dive, Company Research, Lessons Learned databases.
Retries every 5 minutes until successful.
"""

import os
import time
import subprocess
from notion_client import Client

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
PARENT = "30b8d599-a162-8067-9eb8-f229b473d25f"

DATABASES = [
    ("Skills Deep Dive", {
        "Skill": {"title": {}},
        "Level": {"select": {"options": [{"name": "Expert"}, {"name": "Advanced"}, {"name": "Intermediate"}]}},
        "Priority": {"select": {"options": [{"name": "Core"}, {"name": "Secondary"}]}}
    }),
    ("Company Research", {
        "Company": {"title": {}},
        "Status": {"select": {"options": [{"name": "Researched"}, {"name": "In Progress"}]}},
        "Priority": {"select": {"options": [{"name": "High"}, {"name": "Medium"}]}}
    }),
    ("Lessons Learned", {
        "Lesson": {"title": {}},
        "Category": {"select": {"options": [{"name": "Job Search"}, {"name": "Interview"}]}}
    })
]

log_file = "/root/.openclaw/logs/notion_db_creation.log"

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)

log("Starting persistent database creation...")

for name, props in DATABASES:
    created = False
    attempts = 0
    
    while not created:
        attempts += 1
        try:
            db = notion.databases.create(
                parent={"page_id": PARENT},
                title=[{"text": {"content": name}}],
                properties=props
            )
            log(f"SUCCESS: {name} - {db.get('url', 'OK')}")
            created = True
            time.sleep(120)  # Wait between databases
            
        except Exception as e:
            error = str(e)[:100]
            log(f"Attempt {attempts} failed: {error}")
            if attempts > 50:
                log(f"Giving up on {name} after {attempts} attempts")
                break
            time.sleep(300)  # 5 minutes between retries

log("Database creation complete!")
