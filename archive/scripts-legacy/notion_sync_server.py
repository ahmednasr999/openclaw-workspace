#!/usr/bin/env python3
"""
Notion Sync Trigger Server
Run this, then click links in Notion to sync content
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from notion_client import Client
import subprocess

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# File mappings
FILE_MAP = {
    'memory': 'MEMORY.md',
    'identity': 'IDENTITY.md',
    'user': 'USER.md',
    'soul': 'SOUL.md',
    'tools': 'TOOLS.md',
    'agents': 'AGENTS.md',
    'heartbeat': 'HEARTBEAT.md',
    'dashboard': 'dashboard.json',
    'pipeline': 'pipeline.json',
    'calendar': 'content-calendar.json',
    'outreach': 'outreach-queue.json',
}

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>OpenClaw Sync</title>
    <style>
        body { font-family: Arial; padding: 40px; background: #1a1a2e; color: white; }
        h1 { color: #00d4ff; }
        .btn { 
            display: inline-block; 
            padding: 15px 30px; 
            background: #00d4ff; 
            color: #1a1a2e; 
            text-decoration: none; 
            border-radius: 8px; 
            margin: 10px;
            font-weight: bold;
        }
        .btn:hover { background: #00a8cc; }
        .status { margin-top: 30px; padding: 20px; background: #16213e; border-radius: 8px; }
        .success { color: #00ff88; }
        .error { color: #ff6b6b; }
    </style>
</head>
<body>
    <h1>🔄 OpenClaw Sync Trigger</h1>
    <p>Click a button to sync that file from OpenClaw to Notion:</p>
    
    <h2>📄 Core Files</h2>
    <a href="/sync/memory" class="btn">📄 MEMORY.md</a>
    <a href="/sync/identity" class="btn">📄 IDENTITY.md</a>
    <a href="/sync/user" class="btn">📄 USER.md</a>
    <a href="/sync/soul" class="btn">📄 SOUL.md</a>
    <a href="/sync/tools" class="btn">📄 TOOLS.md</a>
    <a href="/sync/agents" class="btn">📄 AGENTS.md</a>
    <a href="/sync/heartbeat" class="btn">📄 HEARTBEAT.md</a>
    
    <h2>📊 Coordination</h2>
    <a href="/sync/dashboard" class="btn">📊 Dashboard</a>
    <a href="/sync/pipeline" class="btn">📊 Pipeline</a>
    <a href="/sync/calendar" class="btn">📊 Calendar</a>
    <a href="/sync/outreach" class="btn">📊 Outreach</a>
    
    <h2>🔄 Actions</h2>
    <a href="/sync/all" class="btn">🔄 Sync All</a>
    <a href="/" class="btn">🔄 Refresh</a>
    
    <div class="status">
        <h3>Last Sync:</h3>
        <p id="status">Click a button above to sync</p>
    </div>
    
    <script>
        const params = new URLSearchParams(window.location.search);
        if (params.get('success')) {
            document.getElementById('status').innerHTML = 
                '<span class="success">✅ ' + params.get('success') + '</span>';
        } else if (params.get('error')) {
            document.getElementById('status').innerHTML = 
                '<span class="error">❌ ' + params.get('error') + '</span>';
        }
    </script>
</body>
</html>
"""

def sync_file(filename, notion_key):
    """Sync a single file to Notion"""
    try:
        # Read file
        filepath = f"{WORKSPACE}/{FILE_MAP.get(filename, filename)}"
        if not os.path.exists(filepath):
            return f"File not found: {filepath}"
        
        with open(filepath, 'r') as f:
            content = f.read()[:5000]
        
        # Find Command Center
        results = notion.search(query="Nasr's Command Center", filter={'value': 'page', 'property': 'object'}, page_size=5)
        parent_id = None
        for r in results.get('results', []):
            title = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
            if 'Command Center' in title:
                parent_id = r['id']
                break
        
        if not parent_id:
            return "Command Center not found"
        
        # Create page title
        display_name = FILE_MAP.get(filename, filename)
        page_title = f"📄 {display_name}"
        
        # Check if exists
        results = notion.search(query=display_name, filter={'value': 'page', 'property': 'object'}, page_size=5)
        for r in results.get('results', []):
            if display_name in r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', ''):
                return f"Page already exists: {display_name}"
        
        # Create page
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': page_title}}]}
        )
        
        # Add content
        lines = content.strip().split('\n')[:30]
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
        
        return f"Synced: {display_name}"
        
    except Exception as e:
        return f"Error: {str(e)[:50]}"

class SyncHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
            
        elif self.path.startswith('/sync/'):
            filename = self.path.split('/')[-1]
            
            if filename == 'all':
                results = []
                for fn in FILE_MAP.keys():
                    results.append(sync_file(fn, NOTION_KEY))
                msg = ' | '.join(results)
                self.send_response(302)
                self.send_header('Location', f'/?success={msg}')
                self.end_headers()
            else:
                result = sync_file(filename, NOTION_KEY)
                self.send_response(302)
                if 'Error' in result or 'not found' in result:
                    self.send_header('Location', f'/?error={result}')
                else:
                    self.send_header('Location', f'/?success={result}')
                self.end_headers()
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == '__main__':
    PORT = 8080
    server = HTTPServer(('0.0.0.0', PORT), SyncHandler)
    print(f"="*60)
    print(f"🔄 OpenClaw Sync Server")
    print(f"="*60)
    print(f"\n🌐 Server running at:")
    print(f"   http://localhost:{PORT}")
    print(f"   http://YOUR_IP:{PORT}")
    print(f"\n📋 Links to add to Notion pages:")
    print(f"   http://localhost:{PORT}/sync/memory")
    print(f"   http://localhost:{PORT}/sync/identity")
    print(f"   etc...")
    print(f"\n⚠️  Press Ctrl+C to stop")
    print(f"="*60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        server.server_close()
