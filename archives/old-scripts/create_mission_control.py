#!/usr/bin/env python3
from notion_client import Client

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)

results = notion.search(query="Nasr's Command Center", filter={'value': 'page', 'property': 'object'}, page_size=5)
parent_id = None
for r in results.get('results', []):
    title = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
    if 'Command Center' in title:
        parent_id = r['id']
        break

print("Creating Mission Control...")

page = notion.pages.create(
    parent={'page_id': parent_id},
    properties={'title': {'title': [{'text': {'content': 'Mission Control - Implementation Plan'}}]}}
)
mission_id = page['id']

blocks = [
    {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": "MISSION CONTROL - Complete Implementation"}}]}},
    {"object": "block", "type": "callout", "callout": {"rich_text": [{"type": "text", "text": {"content": "Based on Alex Finn's framework. 5 components for maximum efficiency."}}], "icon": {"emoji": "🚀"}}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "1. TASKS BOARD"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Track what I work on AND what OpenClaw works on. Enables proactive behavior."}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Columns: Inbox | My Tasks | OpenClaw Tasks | In Progress | Completed"}}]}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "2. CONTENT PIPELINE"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Automate content from idea to publish."}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Stages: Ideas | Writing | Thumbnail | Filming | Published"}}]}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "3. CALENDAR"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "View all cron jobs and scheduled proactive work."}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Components: Daily Schedule | Cron Jobs | Weekly View | Reminders"}}]}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "4. MEMORY"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Beautiful UI for all memories. Global search across conversations."}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Features: Memory Documents | Global Search | Daily Logs | Tags"}}]}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "5. TEAM"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Treat OpenClaw like a company. Agents as employees."}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Team: Orchestrator | Chief of Staff | Writer Agent | CV Agent | Research Agent | Scheduler"}}]}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "quote", "quote": {"rich_text": [{"type": "text", "text": {"content": "The most powerful Mission Control is custom-built for YOUR workflows."}}]}},
]

for block in blocks:
    notion.blocks.children.append(mission_id, children=[block])

print("Mission Control created!")
print(f"https://notion.so/{mission_id.replace('-', '')}")
