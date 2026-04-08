#!/usr/bin/env python3
import urllib.request

image_path = "/tmp/linkedin-post-image.jpg"

with open(image_path, "rb") as f:
    image_data = f.read()

boundary = "----FormBoundary7MA4YWxkTrZu0gW"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="post-image.jpg"\r\n'
    f"Content-Type: image/jpeg\r\n\r\n"
).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()

req = urllib.request.Request(
    "https://0x0.st",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)

with urllib.request.urlopen(req, timeout=30) as resp:
    url = resp.read().decode().strip()

print(f"URL={url}")
