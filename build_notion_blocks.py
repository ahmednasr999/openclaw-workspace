#!/usr/bin/env python3
"""
Create comprehensive Notion structure with proper block types
"""
from notion_client import Client

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)

# Get Command Center
results = notion.search(query="Nasr's Command Center", filter={'value': 'page', 'property': 'object'}, page_size=5)
parent_id = None
for r in results.get('results', []):
    title = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
    if 'Command Center' in title:
        parent_id = r['id']
        break

print("="*60)
print("CREATING COMPREHENSIVE NOTION SYSTEM")
print("="*60)
print(f"Parent ID: {parent_id}")

# Page mappings
PAGES = {
    'MEMORY': '30c8d599a16281f6b72df2daf10182bf',
    'IDENTITY': '30c8d599a162818996aceafbd9dd76fe',
    'USER': '30c8d599a162817ab1c7d40dafb234cf',
    'SOUL': '30c8d599a162815c8f1afa22907f3d01',
    'TOOLS': '30c8d599a16281d6921ac5a6196093c9',
    'AGENTS': '30c8d599a16281529436d5de1fb7f819',
    'HEARTBEAT': '30c8d599a162814183f7f5b451d7bfc4',
    'MASTER_CV': '30c8d599a162811da127cfd0ab16dedc',
    'QUICKREF': '30c8d599a162811da127cfd0ab16dedc',
    'TAILORED': '30c8d599a16281dea8a8f6d4cfd56339',
}

# Block type builder functions
def heading_1(text):
    return {'object': 'block', 'type': 'heading_1', 'heading_1': {'rich_text': [{'type': 'text', 'text': {'content': text}}]}}

def heading_2(text):
    return {'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [{'type': 'text', 'text': {'content': text}}]}}

def heading_3(text):
    return {'object': 'block', 'type': 'heading_3', 'heading_3': {'rich_text': [{'type': 'text', 'text': {'content': text}}]}}

def paragraph(text):
    return {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': text}}]}}

def callout(text, emoji="💡"):
    return {'object': 'block', 'type': 'callout', 'callout': {'rich_text': [{'type': 'text', 'text': {'content': text}}], 'icon': {'emoji': emoji}}}

def divider():
    return {'object': 'block', 'type': 'divider', 'divider': {}}

def to_do(text, checked=False):
    return {'object': 'block', 'type': 'to_do', 'to_do': {'rich_text': [{'type': 'text', 'text': {'content': text}}], 'checked': checked}}

def quote(text):
    return {'object': 'block', 'type': 'quote', 'quote': {'rich_text': [{'type': 'text', 'text': {'content': text}}]}}

def toggle(text):
    return {'object': 'block', 'type': 'toggle', 'toggle': {'rich_text': [{'type': 'text', 'text': {'content': text}}]}}

def link_to_page(page_id):
    return {'object': 'block', 'type': 'link_to_page', 'link_to_page': {'page_id': page_id}}

def bulleted_list(text):
    return {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': text}}]}}

print("\nBlock type functions ready!")
print("="*60)
PYEOF