#!/usr/bin/env python3
"""
GitHub Webhook Handler
Receives GitHub events and forwards to OpenClaw
"""

import os
import sys
import json
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8791
HOOK_URL = "http://127.0.0.1:18789/hooks/github"

class GitHubWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/github":
            self.send_error(404)
            return
        
        # Get headers
        event_type = self.headers.get('X-GitHub-Event', 'unknown')
        delivery_id = self.headers.get('X-GitHub-Delivery', '')
        signature = self.headers.get('X-Hub-Signature-256', '')
        
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        
        try:
            payload = json.loads(body.decode('utf-8'))
        except:
            payload = {}
        
        # Build summary
        summary = {
            "event": event_type,
            "delivery": delivery_id,
            "repository": payload.get('repository', {}).get('full_name'),
            "action": payload.get('action'),
            "sender": payload.get('sender', {}).get('login'),
            "ref": payload.get('ref'),
            "commits": len(payload.get('commits', [])) if 'commits' in payload else 0
        }
        
        print(f"[GitHub] {event_type}: {summary.get('action') or summary.get('ref')} by {summary.get('sender')} in {summary.get('repository')}")
        
        # Forward to OpenClaw
        self.notify_openclaw(summary, payload)
        
        # Acknowledge
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
    
    def notify_openclaw(self, summary, payload):
        """Send to OpenClaw"""
        try:
            import urllib.request
            
            data = json.dumps({
                "type": "github",
                "summary": summary,
                "payload": payload
            }).encode()
            
            req = urllib.request.Request(
                HOOK_URL,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                print(f"[GitHub] Notified OpenClaw: {response.status}")
                
        except Exception as e:
            print(f"[GitHub] Notify error: {e}")
    
    def log_message(self, format, *args):
        print(f"[GitHub Webhook] {format % args}")

def run_server():
    server = HTTPServer(('127.0.0.1', PORT), GitHubWebhookHandler)
    print(f"[GitHub Webhook] Server running on http://127.0.0.1:{PORT}/github")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
