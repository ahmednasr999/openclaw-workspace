import base64, os
# Read base64 from server file
with open('/tmp/linkedin-img-b64.txt', 'r') as f:
    data = f.read()
# Write to workbench-accessible path
with open('/tmp/img_b64_full.txt', 'w') as f:
    f.write(data)
print(f"Written {len(data)} chars")
