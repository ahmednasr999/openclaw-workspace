import base64

with open('/tmp/linkedin-img-b64.txt', 'r') as f:
    b64 = f.read()

chunk_size = 24000
chunks = []
for i in range(0, len(b64), chunk_size):
    chunks.append(b64[i:i+chunk_size])

for i, c in enumerate(chunks):
    escaped = c.replace("'", "\\'")
    mode = "'a'" if i > 0 else "'w'"
    code = f"with open('/tmp/img_b64.txt', {mode}) as f:\\n    f.write('{escaped}')\\nprint('C{i} ok')"
    print(f"CHUNK{i}LEN={len(c)}")
    print(code)
    print()
