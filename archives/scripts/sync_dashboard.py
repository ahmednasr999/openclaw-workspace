#!/usr/bin/env python3
"""
OpenClaw Sync Dashboard with Buttons
Click buttons to sync files to Notion
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from notion_client import Client
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# Sync mappings
FILES = {
    'memory': {'file': 'MEMORY.md', 'title': '📄 MEMORY.md'},
    'identity': {'file': 'IDENTITY.md', 'title': '📄 IDENTITY.md'},
    'user': {'file': 'USER.md', 'title': '📄 USER.md'},
    'soul': {'file': 'SOUL.md', 'title': '📄 SOUL.md'},
    'tools': {'file': 'TOOLS.md', 'title': '📄 TOOLS.md'},
    'agents': {'file': 'AGENTS.md', 'title': '📄 AGENTS.md'},
    'heartbeat': {'file': 'HEARTBEAT.md', 'title': '📄 HEARTBEAT.md'},
    'dashboard': {'file': 'dashboard.json', 'title': '📊 Dashboard'},
    'pipeline': {'file': 'pipeline.json', 'title': '📊 Pipeline'},
    'calendar': {'file': 'content-calendar.json', 'title': '📊 Calendar'},
    'outreach': {'file': 'outreach-queue.json', 'title': '📊 Outreach'},
}

def sync_file(key):
    """Sync a single file"""
    try:
        info = FILES[key]
        filepath = f"{WORKSPACE}/{info['file']}"
        
        if not os.path.exists(filepath):
            return f"File not found: {info['file']}"
        
        with open(filepath, 'r') as f:
            content = f.read()[:4000]
        
        # Find Command Center
        results = notion.search(
            query="Nasr's Command Center",
            filter={'value': 'page', 'property': 'object'},
            page_size=5
        )
        parent_id = None
        for r in results.get('results', []):
            title = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
            if 'Command Center' in title:
                parent_id = r['id']
                break
        
        if not parent_id:
            return "Command Center not found"
        
        # Check if exists
        page_title = info['title']
        results = notion.search(query=info['file'], filter={'value': 'page', 'property': 'object'}, page_size=5)
        for r in results.get('results', []):
            ptitle = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
            if info['file'] in ptitle and r.get('parent', {}).get('page_id') == parent_id:
                return f"Already synced: {info['file']}"
        
        # Create page
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': page_title}}]}
        )
        
        # Add content
        lines = content.strip().split('\n')[:25]
        for line in lines:
            if line.strip():
                try:
                    notion.blocks.children.append(
                        page['id'],
                        children=[{
                            'object': 'block',
                            'type': 'paragraph',
                            'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': line}}]}
                        }]
                    )
                except:
                    pass
        
        return f"Synced: {info['file']}"
        
    except Exception as e:
        return f"Error: {str(e)[:50]}"

HTML = """<!DOCTYPE html>
<html>
<head>
    <title>🔄 OpenClaw Sync Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 40px;
            min-height: 100vh;
        }
        h1 { 
            color: #00d4ff; 
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle { 
            color: #8892b0; 
            margin-bottom: 40px;
        }
        .section { margin-bottom: 40px; }
        h2 { 
            color: #ccd6f6;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        .btn { 
            display: inline-block;
            padding: 15px 25px;
            margin: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
            cursor: pointer;
            border: none;
            font-size: 14px;
        }
        .btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .btn:active { transform: translateY(0); }
        .btn-sync { background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 100%); }
        .btn-sync:hover { box-shadow: 0 10px 30px rgba(0, 212, 255, 0.4); }
        .btn-all { 
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            padding: 20px 40px;
            font-size: 18px;
        }
        .btn-all:hover { box-shadow: 0 10px 30px rgba(56, 239, 125, 0.4); }
        .status {
            margin-top: 40px;
            padding: 25px;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .status h3 { color: #00d4ff; margin-top: 0; }
        .log { 
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.8;
            color: #8892b0;
            max-height: 300px;
            overflow-y: auto;
        }
        .log-entry { margin: 5px 0; padding: 5px 10px; border-radius: 5px; }
        .log-entry.success { background: rgba(0, 255, 136, 0.1); color: #00ff88; }
        .log-entry.error { background: rgba(255, 107, 107, 0.1); color: #ff6b6b; }
        .log-entry.info { background: rgba(0, 212, 255, 0.1); color: #00d4ff; }
        .timestamp { color: #5a6a8a; font-size: 11px; }
    </style>
</head>
<body>
    <h1>🔄 OpenClaw Sync Dashboard</h1>
    <p class="subtitle">Sync OpenClaw files to Notion with one click</p>
    
    <div class="section">
        <h2>📄 Core Files</h2>
        <a href="/sync/memory" class="btn btn-sync">📄 MEMORY.md</a>
        <a href="/sync/identity" class="btn btn-sync">📄 IDENTITY.md</a>
        <a href="/sync/user" class="btn btn-sync">📄 USER.md</a>
        <a href="/sync/soul" class="btn btn-sync">📄 SOUL.md</a>
        <a href="/sync/tools" class="btn btn-sync">📄 TOOLS.md</a>
        <a href="/sync/agents" class="btn btn-sync">📄 AGENTS.md</a>
        <a href="/sync/heartbeat" class="btn btn-sync">📄 HEARTBEAT.md</a>
    </div>
    
    <div class="section">
        <h2>📊 Coordination Files</h2>
        <a href="/sync/dashboard" class="btn btn-sync">📊 Dashboard</a>
        <a href="/sync/pipeline" class="btn btn-sync">📊 Pipeline</a>
        <a href="/sync/calendar" class="btn btn-sync">📊 Calendar</a>
        <a href="/sync/outreach" class="btn btn-sync">📊 Outreach</a>
    </div>
    
    <div class="section">
        <a href="/sync/all" class="btn btn-all">🚀 Sync All Files</a>
        <a href="/" class="btn" style="background: rgba(255,255,255,0.1);">🔄 Refresh</a>
    </div>
    
    <div class="status">
        <h3>📋 Sync Log</h3>
        <div class="log" id="log">
            <div class="log-entry info"><span class="timestamp">[SYSTEM]</span> Ready to sync</div>
        </div>
    </div>
    
    <script>
        // Auto-refresh log every 5 seconds
        setTimeout(function() {
            fetch('/log').then(r => r.json()).then(log => {
                const logDiv = document.getElementById('log');
                logDiv.innerHTML = log.reverse().map(entry => 
                    `<div class="log-entry ${entry.type}"><span class="timestamp">[${entry.time}]</span> ${entry.message}</div>`
                ).join('');
            });
        }, 1000);
    </script>
</body>
</html>
"""

LOG_FILE = '/root/.openclaw/workspace/sync.log'

def log(message, msg_type='info'):
    timestamp = datetime.now().strftime('%H:%M:%S')
    entry = json.dumps({'time': timestamp, 'message': message, 'type': msg_type})
    with open(LOG_FILE, 'a') as f:
        f.write(entry + '\n')

def get_log():
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()[-20:]
            return [json.loads(l) for l in lines if l.strip()]
    except:
        return []

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
            
        elif self.path.startswith('/sync/'):
            key = self.path.split('/')[-1]
            
            if key == 'all':
                results = []
                for k in FILES.keys():
                    results.append(sync_file(k))
                msg = ' | '.join(results)
                log(msg, 'success' if all('Synced' in r for r in results) else 'error')
            else:
                msg = sync_file(key)
                log(msg, 'success' if 'Synced' in msg else 'error')
            
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            
        elif self.path == '/log':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_log()).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

if __name__ == '__main__':
    PORT = 8080
    server = HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    
    print("="*60)
    print("🔄 OPENCLAW SYNC DASHBOARD")
    print("="*60)
    print(f"\n🌐 Dashboard: http://localhost:{PORT}")
    print(f"🌐 Network: http://YOUR_IP:{PORT}")
    print("\n📋 Click buttons to sync files to Notion")
    print("="*60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
        server.server_close()
