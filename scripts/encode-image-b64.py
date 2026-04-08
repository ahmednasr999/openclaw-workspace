#!/usr/bin/env python3
import base64, json
with open("/tmp/linkedin-post-image.jpg", "rb") as f:
    data = base64.b64encode(f.read()).decode()
# Write to a temp file for transfer
with open("/tmp/linkedin-image-b64.txt", "w") as f:
    f.write(data)
print(f"Encoded: {len(data)} chars")
print(f"Saved to: /tmp/linkedin-image-b64.txt")
