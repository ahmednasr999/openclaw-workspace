import base64

with open('/tmp/linkedin-img-b64.txt', 'r') as f:
    b64 = f.read()

# Split into 3 chunks of ~27K chars each
size = len(b64)
chunk_size = size // 3 + 1
chunks = []
for i in range(0, size, chunk_size):
    chunks.append(b64[i:i+chunk_size])

for i, c in enumerate(chunks):
    print(f"CHUNK{i}|{len(c)}")
    print(c[:50])
    print("...")
