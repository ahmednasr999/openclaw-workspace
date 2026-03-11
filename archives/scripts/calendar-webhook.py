#!/usr/bin/env python3
"""
Google Calendar Webhook Handler
Receives push notifications from Google Calendar API
"""

import os
import sys
import json
import hmac
import hashlib
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Config
PORT = 8790
ACCOUNT = "ahmednasr999@gmail.com"
HOOK_URL = "http://127.0.0.1:18789/hooks/calendar"
GOG_PASSWORD = os.environ.get("GOG_KEYRING_PASSWORD", "")

class CalendarWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle incoming calendar push notifications"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path != "/calendar-webhook":
            self.send_error(404)
            return
        
        # Get headers
        channel_id = self.headers.get('X-Goog-Channel-ID', '')
        resource_id = self.headers.get('X-Goog-Resource-ID', '')
        resource_state = self.headers.get('X-Goog-Resource-State', '')
        
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
        
        print(f"[Calendar Webhook] State: {resource_state}, Channel: {channel_id}")
        
        # Calendar changed - fetch recent events
        if resource_state == 'sync':
            print("[Calendar] Sync notification - channel established")
        else:
            # Fetch today's events
            self.fetch_and_notify()
        
        # Acknowledge receipt
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
    
    def fetch_and_notify(self):
        """Fetch calendar events and notify OpenClaw"""
        try:
            import subprocess
            import datetime
            
            # Get today's events using gog
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            
            env = os.environ.copy()
            env['GOG_KEYRING_PASSWORD'] = GOG_PASSWORD
            
            result = subprocess.run(
                ['gog', 'calendar', 'events', 'primary', 
                 '--from', f"{today}T00:00:00Z",
                 '--to', f"{tomorrow}T23:59:59Z",
                 '-a', ACCOUNT,
                 '--json'],
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                events = json.loads(result.stdout)
                print(f"[Calendar] Found {len(events)} events")
                
                # Send to OpenClaw hook
                self.notify_openclaw(events)
            else:
                print(f"[Calendar] Error: {result.stderr}")
                
        except Exception as e:
            print(f"[Calendar] Fetch error: {e}")
    
    def notify_openclaw(self, events):
        """Send notification to OpenClaw"""
        try:
            import urllib.request
            
            data = json.dumps({
                "type": "calendar_update",
                "events": events,
                "account": ACCOUNT
            }).encode()
            
            req = urllib.request.Request(
                HOOK_URL,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                print(f"[Calendar] Notified OpenClaw: {response.status}")
                
        except Exception as e:
            print(f"[Calendar] Notify error: {e}")
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        print(f"[Calendar Webhook] {format % args}")

def run_server():
    server = HTTPServer(('127.0.0.1', PORT), CalendarWebhookHandler)
    print(f"[Calendar Webhook] Server running on http://127.0.0.1:{PORT}/calendar-webhook")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
