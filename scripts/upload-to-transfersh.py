#!/usr/bin/env python3
import urllib.request

image_path = "/root/.openclaw/media/inbound/file_266---aade39c1-5899-46d4-b02c-6f2a88dfc8c1.jpg"

with open(image_path, "rb") as f:
    image_data = f.read()

req = urllib.request.Request(
    "https://transfer.sh/post-image.jpg",
    data=image_data,
    headers={"Content-Type": "image/jpeg"}
)
req.get_method = lambda: "PUT"

with urllib.request.urlopen(req, timeout=30) as resp:
    url = resp.read().decode().strip()

print(f"URL={url}")
