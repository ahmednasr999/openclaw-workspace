#!/bin/bash
cd /root/.openclaw/workspace
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
HTML = '''<!DOCTYPE html><html><head><title>Sync</title><style>body{font-family:Arial;background:#1a1a2e;color:white;padding:40px}h1{color:#00d4ff}a{display:inline-block;padding:15px 25px;background:#00d4ff;color:#1a1a2e;text-decoration:none;border-radius:8px;margin:10px;font-weight:bold}</style></head><body><h1>Sync Dashboard</h1><p>Click to sync:</p><a href=/sync/memory>MEMORY.md</a> <a href=/sync/identity>IDENTITY.md</a> <a href=/sync/user>USER.md</a> <a href=/sync/soul>SOUL.md</a> <a href=/sync/tools>TOOLS.md</a> <a href=/sync/agents>AGENTS.md</a> <a href=/sync/heartbeat>HEARTBEAT.md</a> <br><br><a href=/sync/dashboard>Dashboard</a> <a href=/sync/pipeline>Pipeline</a> <br><br><a href=/sync/all style=background:#00ff88>Sync All</a></body></html>'''
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200); self.send_header('Content-type','text/html'); self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith('/sync/'):
            self.send_response(302); self.send_header('Location','/'); self.end_headers()
HTTPServer(('0.0.0.0',8888),H).serve_forever()
"
