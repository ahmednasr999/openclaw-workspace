import base64

# Read the c1, c2, c3 files
with open("/tmp/c1.txt", "rb") as f:
    c1 = f.read().decode()
with open("/tmp/c2.txt", "rb") as f:
    c2 = f.read().decode()
with open("/tmp/c3.txt", "rb") as f:
    c3 = f.read().decode()

# Build the upload script for workbench
code = f"""import base64, requests

# HERE.NOW UPLOAD
body = {{"files":[{{"path":"post-image.jpg","size":61304,"contentType":"image/jpeg"}}]}}
r = requests.post("https://here.now/api/v1/publish", json=body, timeout=15)
data = r.json()
version_id = data["upload"]["versionId"]
upload_url = data["upload"]["uploads"][0]["url"]
finalize_url = data["upload"]["finalizeUrl"]

# WRITE BASE64 DATA IN CHUNKS
with open("/tmp/b.txt", "w") as f:
    f.write("{c1}")
with open("/tmp/b.txt", "a") as f:
    f.write("{c2}")
with open("/tmp/b.txt", "a") as f:
    f.write("{c3}")

# DECODE
with open("/tmp/b.txt") as f:
    b64 = f.read()
img = base64.b64decode(b64)
print(f"Decoded: {{len(img)}} bytes")

# UPLOAD TO R2
r2 = requests.put(upload_url, data=img, headers={{"Content-Type":"image/jpeg"}}, timeout=30)
print(f"R2: {{r2.status_code}}")

# FINALIZE
rf = requests.post(finalize_url, json={{"versionId":version_id}}, timeout=15)
print(f"Finalize: {{rf.status_code}}")

# WRITE IMAGE FILE
with open("/tmp/post-image.jpg", "wb") as f:
    f.write(img)

# UPLOAD TO S3
result, err = upload_local_file("/tmp/post-image.jpg")
if err:
    print(f"S3 error: {{err}}")
else:
    print(f"S3 key: {{result['s3key']}}")
    print("READY")
"""

# Write to file
with open("/tmp/wb_upload.txt", "w") as f:
    f.write(code)
print(f"Script written: {len(code)} chars")
print("===SCRIPT_START===")
print(code)
print("===SCRIPT_END===")
