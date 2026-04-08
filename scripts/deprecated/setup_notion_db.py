import urllib.request, ssl, json, time
TOKEN = json.load(open('/root/.openclaw/workspace/config/notion.json'))['token']
ctx = ssl.create_default_context()
DB = "32e8d599-a162-8134-8677-cac152970c0a"

def patch(props):
    url = f"https://api.notion.com/v1/databases/{DB}"
    data = json.dumps({"properties": props}).encode()
    req = urllib.request.Request(url, data=data, method="PATCH", headers={
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read())

patches = [
    {"Category": {"multi_select": {"options": [
        {"name": "FinTech", "color": "blue"},
        {"name": "Healthcare", "color": "green"},
        {"name": "HealthTech", "color": "teal"},
        {"name": "Digital Transformation", "color": "purple"},
        {"name": "PMO", "color": "orange"},
        {"name": "Strategy", "color": "yellow"},
        {"name": "Operation Excellence", "color": "red"},
        {"name": "AI", "color": "pink"},
    ]}}},
    {"Source": {"rich_text": {}}},
    {"URL": {"url": {}}},
    {"Published": {"date": {}}},
    {"Summary": {"rich_text": {}}},
    {"Status": {"select": {"options": [
        {"name": "New", "color": "blue"},
        {"name": "Read", "color": "gray"},
        {"name": "Archived", "color": "brown"},
    ]}}},
]

for props in patches:
    name = list(props.keys())[0]
    result = patch(props)
    print(f"OK added {name}")
    time.sleep(0.5)

url = f"https://api.notion.com/v1/databases/{DB}"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28"})
with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
    db = json.loads(r.read())
props = list(db.get('properties', {}).keys())
print(f"\nFinal properties ({len(props)}): {props}")

import os
config = {
    'notion_token': TOKEN,
    'database_id': DB,
    'feeds': {
        'FinTech': 'https://connectingthedotsinfin.tech/rss/',
        'Healthcare': 'https://www.healthcareittoday.com/feed/',
        'HealthTech': 'https://www.mobihealthnews.com/feed/',
        'Digital Transformation': 'https://sloanreview.mit.edu/tag/digital-transformation/feed/',
        'Strategy': 'https://fs.blog/feed/',
    },
    'state_file': '/root/.openclaw/workspace/data/rss-intelligence-state.json',
}
os.makedirs('/root/.openclaw/workspace/data', exist_ok=True)
cfg_path = '/root/.openclaw/workspace/config/rss-intelligence.json'
json.dump(config, open(cfg_path, 'w'), indent=2)
print(f"Config saved: {cfg_path}")
