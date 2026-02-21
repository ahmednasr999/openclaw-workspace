#!/bin/bash
# OpenClaw Sync Server
# Run this to start the sync dashboard

cd /root/.openclaw/workspace

# Kill any existing servers
lsof -ti:8080 | xargs kill -9 2>/dev/null
lsof -ti:8888 | xargs kill -9 2>/dev/null

# Use port 8888
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler

HTML = '''<!DOCTYPE html>
<html>
<head><title>OpenClaw Sync</title>
<style>
body{font-family:Arial;background:#1a1a2e;color:white;padding:40px}
h1{color:#00d4ff}
a{display:inline-block;padding:15px 25px;background:#00d4ff;color:#1a1a2e;
   text-decoration:none;border-radius:8px;margin:10px;font-weight:bold}
</style>
</head>
<body>
<h1>Sync Dashboard</h1>
<p>Click to sync from OpenClaw to Notion:</p>
<a href=/sync/memory>MEMORY.md</a>
<a href=/sync/identity>IDENTITY.md</a>
<a href=/sync/user>USER.md</a>
<a href=/sync/soul>SOUL.md</a>
<a href=/sync/tools>TOOLS.md</a>
<a href=/sync/agents>AGENTS.md</a>
<a href=/sync/heartbeat>HEARTBEAT.md</a>
<br><br>
<a href=/sync/dashboard>Dashboard</a>
<a href=/sync/pipeline>Pipeline</a>
<br><br>
<a href=/sync/all style=background:#00ff88>Sync All</a>
</body></html>'''

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith('/sync/'):
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

server = HTTPServer(('0.0.0.0', 8888), H)
print('Server running at http://localhost:8888')
server.serve_forever()
"
