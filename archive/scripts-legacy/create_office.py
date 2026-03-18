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

print("Creating Digital Office...")

page = notion.pages.create(
    parent={'page_id': parent_id},
    properties={'title': {'title': [{'text': {'content': 'Digital Office - Mission Control'}}]}}
)
office_id = page['id']

blocks = [
    {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Digital Office - Mission Control"}}]}},
    {"object": "block", "type": "callout", "callout": {"rich_text": [{"type": "text", "text": {"content": "My AI team - All sub-agents organized by role. View status, assign work, track progress."}}], "icon": {"emoji": "🏢"}}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Developers Team"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Orchestrator - Task router & coordinator (MiniMax-M2.1)"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "CV Agent - Creates tailored CVs HTML->PDF (Opus 4.5)"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Research Agent - Web research & company analysis (MiniMax-M2.1)"}}]}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Writers Team"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Writer Agent - LinkedIn posts, emails, marketing copy (Sonnet 4.5)"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Content Agent - Blog posts, articles, case studies"}}]}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Strategic Team"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Chief of Staff (Max) - Agent coordination, briefs, strategy (Sonnet 4)"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Scheduler Agent - Cron jobs, reminders, automation"}}]}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "callout", "callout": {"rich_text": [{"type": "text", "text": {"content": "Status: Orchestrator Active | CV Agent Ready | Research Agent Ready | Writer Agent Ready | Scheduler Agent Monitoring"}}], "icon": {"emoji": "🟢"}}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "quote", "quote": {"rich_text": [{"type": "text", "text": {"content": "The most powerful way is to customize Mission Control for your workflows. Treat it as an art form - have fun!"}}]}},
]

for block in blocks:
    notion.blocks.children.append(office_id, children=[block])

print("Digital Office created!")
print(f"https://notion.so/{office_id.replace('-', '')}")
