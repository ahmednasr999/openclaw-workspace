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

print("Creating Task Dashboard...")

page = notion.pages.create(
    parent={'page_id': parent_id},
    properties={'title': {'title': [{'text': {'content': 'Task Dashboard'}}]}}
)
dash_id = page['id']

blocks = [
    {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Task Dashboard"}}]}},
    {"object": "block", "type": "callout", "callout": {"rich_text": [{"type": "text", "text": {"content": "Track all tasks: Future, Current, Completed"}}], "icon": {"emoji": "📊"}}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Future Tasks"}}]}},
    {"object": "block", "type": "to_do", "to_do": {"rich_text": [{"type": "text", "text": {"content": "Publish EMR ROI post"}}], "checked": False}},
    {"object": "block", "type": "to_do", "to_do": {"rich_text": [{"type": "text", "text": {"content": "Follow up with Dr. Ahmed Al-Mansour"}}], "checked": False}},
    {"object": "block", "type": "to_do", "to_do": {"rich_text": [{"type": "text", "text": {"content": "Apply to 5 new roles"}}], "checked": False}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Completed"}}]}},
    {"object": "block", "type": "to_do", "to_do": {"rich_text": [{"type": "text", "text": {"content": "Set up Notion integration"}}], "checked": True}},
    {"object": "block", "type": "to_do", "to_do": {"rich_text": [{"type": "text", "text": {"content": "Create LinkedIn posts"}}], "checked": True}},
]

for block in blocks:
    notion.blocks.children.append(dash_id, children=[block])

print("Task Dashboard created!")
print(f"https://notion.so/{dash_id.replace('-', '')}")
