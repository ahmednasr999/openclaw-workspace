import base64, os

# Read the base64 from server
with open('/tmp/linkedin-img-b64.txt', 'r') as f:
    data = f.read()

total = len(data)
chunk_size = 27000  # safe chunk size
chunks = []
for i in range(0, total, chunk_size):
    chunks.append(data[i:i+chunk_size])

print(f"Total: {total} chars, {len(chunks)} chunks")
for i, c in enumerate(chunks):
    path = f'/tmp/imgchunk{i}.txt'
    with open(path, 'w') as f:
        f.write(c)
    print(f"Chunk {i}: {len(c)} chars -> {path}")
