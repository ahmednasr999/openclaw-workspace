#!/usr/bin/env python3
"""Serve the LinkedIn post image once on a random port, print the URL."""
import http.server
import threading
import socket
import os
import shutil

IMAGE_PATH = "/root/.openclaw/media/inbound/file_266---aade39c1-5899-46d4-b02c-6f2a88dfc8c1.jpg"

# Find a free port
s = socket.socket()
s.bind(('', 0))
port = s.getsockname()[1]
s.close()

# Get server's outbound IP
s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s2.connect(("8.8.8.8", 80))
ip = s2.getsockname()[0]
s2.close()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(os.path.getsize(IMAGE_PATH)))
        self.end_headers()
        with open(IMAGE_PATH, "rb") as f:
            shutil.copyfileobj(f, self.wfile)
        threading.Thread(target=self.server.shutdown, daemon=True).start()
    def log_message(self, *a): pass

server = http.server.HTTPServer(('0.0.0.0', port), Handler)
print(f"http://{ip}:{port}/image.jpg", flush=True)
server.serve_forever()
