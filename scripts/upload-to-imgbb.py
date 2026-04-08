#!/usr/bin/env python3
import urllib.request
import urllib.parse
import base64
import json

image_path = "/root/.openclaw/media/inbound/file_266---aade39c1-5899-46d4-b02c-6f2a88dfc8c1.jpg"

with open(image_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

# imgbb free API - no account needed for temp uploads
data = urllib.parse.urlencode({"image": b64}).encode()
req = urllib.request.Request(
    "https://api.imgbb.com/1/upload?key=null",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.load(resp)
        url = result["data"]["url"]
        print(f"URL={url}")
except Exception as e:
    print(f"imgbb failed: {e}")
    # Try file.io as fallback
    with open(image_path, "rb") as f:
        image_data = f.read()
    boundary = "----Boundary"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"post.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n"
    ).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()
    req2 = urllib.request.Request(
        "https://file.io/?expires=1d",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req2, timeout=30) as resp2:
        result2 = json.load(resp2)
        print(f"URL={result2.get('link', result2)}")
