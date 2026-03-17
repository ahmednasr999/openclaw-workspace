#!/usr/bin/env python3
"""GitHub Webhook Proxy - Verifies HMAC signature and forwards to OpenClaw hooks."""

import hashlib
import hmac
import http.server
import json
import urllib.request
import sys

PORT = 8791
WEBHOOK_SECRET = "cfb8500c0d6411e7ea4624649e1e62f1dd0508f5"
HOOK_URL = "http://127.0.0.1:18789/hooks/github"
HOOK_TOKEN = "2d8923a5d3b32d1f693cd9f03f0fb21f3d42409341e267e5"


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 1_000_000:  # 1MB max
            self.send_response(413)
            self.end_headers()
            return

        body = self.rfile.read(content_length)

        # Verify HMAC signature
        sig_header = self.headers.get("X-Hub-Signature-256", "")
        if sig_header:
            expected = "sha256=" + hmac.new(
                WEBHOOK_SECRET.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig_header, expected):
                print(f"[github-proxy] HMAC mismatch, rejecting", flush=True)
                self.send_response(403)
                self.end_headers()
                return

        # Parse and enrich payload with event type header
        event = self.headers.get("X-GitHub-Event", "unknown")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        # Inject event type into payload for the template
        payload["_github_event"] = event
        payload["headers"] = {"x-github-event": event}

        # Forward to OpenClaw hooks
        try:
            req = urllib.request.Request(
                HOOK_URL,
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {HOOK_TOKEN}",
                    "X-GitHub-Event": event,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                resp_body = resp.read().decode()
        except Exception as e:
            print(f"[github-proxy] Forward failed: {e}", flush=True)
            status = 502
            resp_body = str(e)

        print(f"[github-proxy] {event} -> {status}", flush=True)
        self.send_response(200)  # Always 200 to GitHub
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "forwarded": status}).encode())

    def log_message(self, format, *args):
        pass  # Suppress default logging


if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[github-proxy] Listening on 127.0.0.1:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
