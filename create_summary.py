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

# Create summary page
summary = notion.pages.create(
    parent={'page_id': parent_id},
    properties={'title': {'title': [{'text': {'content': 'All Enhanced Pages'}}]}}
)
summary_id = summary['id']
print(f"Created: {summary_id}")

summary_blocks = [
    {'object': 'block', 'type': 'heading_1', 'heading_1': {'rich_text': [{'type': 'text', 'text': {'content': 'COMPLETE ENHANCED PAGES'}}]}},
    {'object': 'block', 'type': 'callout', 'callout': {'rich_text': [{'type': 'text', 'text': {'content': 'All pages enhanced with proper Notion block types'}}], 'icon': {'emoji': '✅'}}},
    {'object': 'block', 'type': 'divider', 'divider': {}},
    {'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [{'type': 'text', 'text': {'content': 'Core Files'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Enhanced MEMORY'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Enhanced IDENTITY'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Enhanced USER'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Enhanced SOUL'}}]}},
    {'object': 'block', 'type': 'divider', 'divider': {}},
    {'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [{'type': 'text', 'text': {'content': 'Professional'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Enhanced TOOLS'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Enhanced AGENTS'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Enhanced MASTER_CV'}}]}},
    {'object': 'block', 'type': 'divider', 'divider': {}},
    {'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [{'type': 'text', 'text': {'content': 'LinkedIn Posts'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': '233x Growth Story'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': '$50M Healthcare'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Saudi Relocation'}}]}},
    {'object': 'block', 'type': 'divider', 'divider': {}},
    {'object': 'block', 'type': 'heading_2', 'heading_2', 'heading_2': {'rich_text': [{'type': 'text', 'text': {'content': 'Case Studies'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Talabat'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'SGH'}}]}},
    {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': 'Network'}}]}},
    {'object': 'block', 'type': 'divider', 'divider': {}},
    {'object': 'block', 'type': 'quote', 'quote': {'rich_text': [{'type': 'text', 'text': {'content': 'Done!'}}]}},
]

for block in summary_blocks:
    notion.blocks.children.append(summary_id, children=[block])

print(f"Added all blocks")
print(f"\nSummary: https://notion.so/{summary_id.replace('-', '')}")
