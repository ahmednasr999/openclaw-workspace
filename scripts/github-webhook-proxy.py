#!/usr/bin/env python3
"""GitHub webhook proxy with HMAC verification and environment-backed secrets."""

import hashlib
import hmac
import http.server
import json
import os
import urllib.error
import urllib.request


PORT = 8791
HOOK_URL = "http://127.0.0.1:18789/hooks/github"
WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]
HOOK_TOKEN = os.environ["OPENCLAW_HOOKS_TOKEN"]


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 1_000_000:
            self.send_response(413 if content_length > 1_000_000 else 400)
            self.end_headers()
            return

        body = self.rfile.read(content_length)
        sig_header = self.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if not sig_header or not hmac.compare_digest(sig_header, expected):
            print("[github-proxy] missing or invalid HMAC signature", flush=True)
            self.send_response(403)
            self.end_headers()
            return

        event = self.headers.get("X-GitHub-Event", "unknown")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        payload["_github_event"] = event
        payload["headers"] = {"x-github-event": event}
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
                resp.read()
            forwarded = 200 <= status < 300
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"[github-proxy] forward failed: {type(exc).__name__}", flush=True)
            status = 502
            forwarded = False

        print(f"[github-proxy] {event} -> {status}", flush=True)
        self.send_response(200 if forwarded else 502)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps({"ok": forwarded, "forwarded_status": status}).encode()
        )

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[github-proxy] listening on 127.0.0.1:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
