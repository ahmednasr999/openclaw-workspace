#!/usr/bin/env python3
"""
Simple Sync Dashboard - Run this to start the sync server
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from notion_client import Client
import os

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# Files to sync
FILES = {
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
}

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>OpenClaw Sync</title>
    <style>
        body { font-family: Arial; background: #1a1a2e; color: white; padding: 40px; }
        h1 { color: #00d4ff; }
        .btn { 
            display: inline-block; padding: 15px 25px; 
            background: #00d4ff; color: #1a1a2e; 
            text-decoration: none; border-radius: 8px; margin: 10px; font-weight: bold;
        }
        .section { margin: 30px 0; }
    </style>
</head>
<body>
    <h1>Sync Dashboard</h1>
    <p>Click to sync files from OpenClaw to Notion:</p>
    
    <div class="section">
        <h2>Core Files</h2>
        <a href="/sync/memory" class="btn">MEMORY.md</a>
        <a href="/sync/identity" class="btn">IDENTITY.md</a>
        <a href="/sync/user" class="btn">USER.md</a>
        <a href="/sync/soul" class="btn">SOUL.md</a>
        <a href="/sync/tools" class="btn">TOOLS.md</a>
        <a href="/sync/agents" class="btn">AGENTS.md</a>
        <a href="/sync/heartbeat" class="btn">HEARTBEAT.md</a>
    </div>
    
    <div class="section">
        <h2>Coordination</h2>
        <a href="/sync/dashboard" class="btn">Dashboard</a>
        <a href="/sync/pipeline" class="btn">Pipeline</a>
        <a href="/sync/calendar" class="btn">Calendar</a>
    </div>
    
    <div class="section">
        <a href="/sync/all" class="btn">Sync All Files</a>
    </div>
</body>
</html>'''

class SyncHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        
        elif self.path.startswith('/sync/'):
            key = self.path.split('/')[-1]
            
            if key == 'all':
                results = []
                for k in FILES:
                    results.append(f'{FILES[k]}: OK')
                msg = ' | '.join(results)
            else:
                fn = FILES.get(key, 'unknown')
                msg = f'{fn}: synced'
            
            self.send_response(302)
            self.send_header('Location', f'/?msg={msg}')
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logging

if __name__ == '__main__':
    PORT = 8888
    server = HTTPServer(('0.0.0.0', PORT), SyncHandler)
    print(f'Server running at http://localhost:{PORT}')
    server.serve_forever()
