#!/usr/bin/env python3
import os
path = "/tmp/linkedin-post-image.jpg"
if os.path.exists(path):
    size = os.path.getsize(path)
    print(f"EXISTS: {path} ({size} bytes)")
else:
    print(f"MISSING: {path}")
    # Also check workspace
    alt = "/root/.openclaw/workspace/linkedin/posts/2026-04-02-image.png"
    if os.path.exists(alt):
        print(f"FALLBACK EXISTS: {alt} ({os.path.getsize(alt)} bytes)")
    else:
        print(f"FALLBACK MISSING: {alt}")
