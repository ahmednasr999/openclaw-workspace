import base64

# Read the actual image file and encode it fresh
img_path = "/root/.openclaw/media/inbound/file_266---aade39c1-5899-46d4-b02c-6f2a88dfc8c1.jpg"
with open(img_path, "rb") as f:
    img_data = f.read()
print(f"Image size: {len(img_data)} bytes")

# Encode as base64
b64 = base64.b64encode(img_data).decode()
print(f"Base64 length: {len(b64)} chars")

# Split into 3 parts: 25K, 25K, rest
s1 = b64[:25000]
s2 = b64[25000:50000]
s3 = b64[50000:]
print(f"s1={len(s1)} s2={len(s2)} s3={len(s3)}")

# Write each as a Python variable file
with open("/tmp/b64_s1.py", "w") as f:
    f.write(f"B64S1 = {repr(s1)}\n")
with open("/tmp/b64_s2.py", "w") as f:
    f.write(f"B64S2 = {repr(s2)}\n")
with open("/tmp/b64_s3.py", "w") as f:
    f.write(f"B64S3 = {repr(s3)}\n")
print("Written to /tmp/b64_s*.py")
