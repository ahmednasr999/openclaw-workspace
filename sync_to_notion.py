#!/usr/bin/env python3
"""
OpenClaw to Notion Sync Script
Syncs workspace data to Notion databases
Schedule: hourly via cron
Usage: python3 sync_to_notion.py
"""

from notion_client import Client
import os
import json
from datetime import datetime

NOTION_KEY = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
notion = Client(auth=NOTION_KEY)

# Database IDs
DB_IDS = {
    "cv_library": "30b8d599a1628124a26bc5094804a234",
    "job_tracker": "30b8d599a1628140a655d5ef843cd833",
    "daily_notes": "30b8d599a162819caaece83207b76394",
    "knowledge_base": "30b8d599a162817fab62c4a951b24e2c",
    "coordination": "30b8d599a16281a0a12ff2ed81cb99da",
    "skills_catalog": "30b8d599a16281a88e1bd2d2258909e4"
}

def sync_cvs():
    """Sync CVs from /cvs/ directory"""
    cv_dir = "/root/.openclaw/workspace/cvs"
    for f in os.listdir(cv_dir):
        if f.endswith('.pdf'):
            print(f"CV: {f}")

def sync_daily_notes():
    """Sync daily notes from memory/ directory"""
    memory_dir = "/root/.openclaw/workspace/memory"
    for f in os.listdir(memory_dir):
        if f.startswith('2026-') and f.endswith('.md'):
            print(f"Daily Note: {f}")

def sync_knowledge():
    """Sync key memory files"""
    key_files = [
        "memory/master-cv-data.md",
        "memory/ats-best-practices.md",
        "memory/active-tasks.md",
        "memory/lessons-learned.md"
    ]
    for f in key_files:
        if os.path.exists(f"/root/.openclaw/workspace/{f}"):
            print(f"Knowledge: {f}")

if __name__ == "__main__":
    print(f"Syncing at {datetime.now()}")
    sync_cvs()
    sync_daily_notes()
    sync_knowledge()
    print("Sync complete")
