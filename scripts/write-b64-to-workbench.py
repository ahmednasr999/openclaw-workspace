import base64, os

with open('/root/.openclaw/media/inbound/file_266---aade39c1-5899-46d4-b02c-6f2a88dfc8c1.jpg', 'rb') as f:
    img_data = f.read()

b64 = base64.b64encode(img_data).decode()
size = len(b64)
print(f"Image: {len(img_data)} bytes -> base64: {size} chars")

# Write to server temp file so workbench can read
with open('/tmp/linkedin-b64.txt', 'w') as f:
    f.write(b64)
print(f"Written base64 to /tmp/linkedin-b64.txt ({size} chars)")

# Also write image size info
with open('/tmp/linkedin-img-size.txt', 'w') as f:
    f.write(str(len(img_data)))
print(f"Image size: {len(img_data)}")
