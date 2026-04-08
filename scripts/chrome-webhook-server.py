#!/usr/bin/env python3
"""
Chrome Webhook Server - runs on Ahmed-Mac
Exposes Chrome CDP (port 9222) as a simple HTTP API for the VPS to call.

Usage: python3 chrome-webhook-server.py
Listens on: http://localhost:9111
"""

import json
import urllib.request
import urllib.parse
import time
import http.server
import threading
import sys
import os

CDP_PORT = 9222
LISTEN_PORT = 9111
TIMEOUT = 15  # seconds


def cdp_request(session_url, method, params=None):
    """Send a CDP command to Chrome."""
    payload = json.dumps({"id": 1, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(
        session_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def get_tabs():
    """Get list of Chrome tabs via CDP."""
    try:
        with urllib.request.urlopen(f"http://localhost:{CDP_PORT}/json", timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return []


def fetch_page_text(url, reuse_tab_id=None):
    """
    Navigate to URL in Chrome and extract text content.
    Optionally reuse an existing tab by targetId.
    """
    tabs = get_tabs()
    if not tabs:
        return {"ok": False, "error": "Chrome not accessible on port 9222"}

    # Find tab to use
    tab = None
    if reuse_tab_id:
        for t in tabs:
            if t.get("id") == reuse_tab_id:
                tab = t
                break

    # If no specific tab, use first non-devtools tab
    if not tab:
        for t in tabs:
            if t.get("type") == "page" and "devtools" not in t.get("url", ""):
                tab = t
                break

    if not tab:
        return {"ok": False, "error": "No usable Chrome tab found"}

    target_id = tab["id"]
    # Use WebSocket URL for CDP session
    ws_url = tab.get("webSocketDebuggerUrl", "")
    if not ws_url:
        return {"ok": False, "error": "No WebSocket debugger URL for tab"}

    # Use the HTTP/JSON endpoint instead (simpler, no WS needed)
    # Activate the tab
    try:
        urllib.request.urlopen(
            f"http://localhost:{CDP_PORT}/json/activate/{target_id}", timeout=5
        )
    except:
        pass

    # Navigate using CDP over HTTP (available in newer Chrome)
    # Actually use the /json/protocol endpoint for navigation
    # We'll use the evaluate approach via a simpler method

    # Build CDP session URL
    cdp_session = f"http://localhost:{CDP_PORT}/json/runtime/evaluate"

    # Use Page.navigate via the devtools protocol
    nav_url = f"http://localhost:{CDP_PORT}/json/new"

    # Simplest approach: use urllib to hit Chrome's CDP JSON endpoint
    # Navigate the tab
    nav_payload = json.dumps({
        "id": 1,
        "method": "Page.navigate",
        "params": {"url": url}
    }).encode()

    # We need WebSocket for real CDP. Use a subprocess approach instead.
    import subprocess

    # Use a node.js one-liner or Python websocket if available
    # Try websockets library first
    try:
        import websockets
        import asyncio

        async def _fetch():
            async with websockets.connect(ws_url) as ws:
                # Navigate
                await ws.send(json.dumps({
                    "id": 1, "method": "Page.navigate",
                    "params": {"url": url}
                }))
                await asyncio.sleep(0.5)
                await ws.recv()  # navigation result

                # Wait for load
                await asyncio.sleep(3)

                # Extract text
                await ws.send(json.dumps({
                    "id": 2, "method": "Runtime.evaluate",
                    "params": {
                        "expression": "document.body.innerText",
                        "returnByValue": True
                    }
                }))
                result = json.loads(await ws.recv())
                text = result.get("result", {}).get("result", {}).get("value", "")

                # Get title
                await ws.send(json.dumps({
                    "id": 3, "method": "Runtime.evaluate",
                    "params": {
                        "expression": "document.title",
                        "returnByValue": True
                    }
                }))
                title_result = json.loads(await ws.recv())
                title = title_result.get("result", {}).get("result", {}).get("value", "")

                return {"ok": True, "text": text[:50000], "title": title, "url": url}

        loop = asyncio.new_event_loop()
        return loop.run_until_complete(_fetch())

    except ImportError:
        pass

    # Fallback: use osascript to run JavaScript in Chrome
    try:
        # Navigate
        nav_script = f'''
        tell application "Google Chrome"
            set URL of active tab of front window to "{url}"
        end tell
        '''
        subprocess.run(["osascript", "-e", nav_script], timeout=5, capture_output=True)
        time.sleep(3)  # wait for page load

        # Extract text
        extract_script = '''
        tell application "Google Chrome"
            set pageText to execute active tab of front window javascript "document.body.innerText"
            return pageText
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", extract_script],
            timeout=15, capture_output=True, text=True
        )
        text = result.stdout.strip()

        title_script = '''
        tell application "Google Chrome"
            return title of active tab of front window
        end tell
        '''
        title_result = subprocess.run(
            ["osascript", "-e", title_script],
            timeout=5, capture_output=True, text=True
        )
        title = title_result.stdout.strip()

        return {"ok": True, "text": text[:50000], "title": title, "url": url}

    except Exception as e:
        return {"ok": False, "error": f"osascript failed: {e}"}


class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[chrome-webhook] {format % args}")

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            tabs = get_tabs()
            self.wfile.write(json.dumps({
                "ok": True,
                "chrome_tabs": len(tabs),
                "tabs": [{"id": t.get("id"), "url": t.get("url", "")[:80]} for t in tabs]
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        if self.path == "/fetch":
            url = data.get("url")
            tab_id = data.get("targetId")
            if not url:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "url required"}')
                return

            result = fetch_page_text(url, reuse_tab_id=tab_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        elif self.path == "/evaluate":
            # Run arbitrary JS in current Chrome tab
            expression = data.get("expression", "document.body.innerText")
            tab_id = data.get("targetId")
            tabs = get_tabs()
            tab = None
            if tab_id:
                for t in tabs:
                    if t.get("id") == tab_id:
                        tab = t
                        break
            if not tab and tabs:
                tab = next((t for t in tabs if t.get("type") == "page"), tabs[0])

            if not tab:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"ok": false, "error": "no tab"}')
                return

            import subprocess
            script = f'''
            tell application "Google Chrome"
                set r to execute active tab of front window javascript "{expression.replace('"', '\\"')}"
                return r
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                timeout=15, capture_output=True, text=True
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": result.returncode == 0,
                "result": result.stdout.strip(),
                "error": result.stderr.strip() if result.returncode != 0 else None
            }).encode())

        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    print(f"[chrome-webhook] Starting on port {LISTEN_PORT}")
    print(f"[chrome-webhook] Chrome CDP expected at localhost:{CDP_PORT}")

    # Verify Chrome is accessible
    tabs = get_tabs()
    if tabs:
        print(f"[chrome-webhook] ✅ Chrome connected — {len(tabs)} tabs found")
    else:
        print(f"[chrome-webhook] ⚠️  Chrome not found on port {CDP_PORT}")
        print(f"[chrome-webhook]    Start Chrome with: open -a 'Google Chrome' --args --remote-debugging-port=9222")

    server = http.server.HTTPServer(("127.0.0.1", LISTEN_PORT), WebhookHandler)
    print(f"[chrome-webhook] Listening on http://127.0.0.1:{LISTEN_PORT}")
    server.serve_forever()
