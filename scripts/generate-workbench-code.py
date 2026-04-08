import base64

with open('/tmp/linkedin-img-b64.txt', 'r') as f:
    b64 = f.read()

# Split into ~25K char chunks
chunk_size = 25000
chunks = []
for i in range(0, len(b64), chunk_size):
    chunks.append(b64[i:i+chunk_size])

print(f"Total chars: {len(b64)}, Chunks: {len(chunks)}")
for i, c in enumerate(chunks):
    print(f"\n=== CHUNK {i} ({len(c)} chars) ===")
    # Generate workbench Python code for this chunk
    # Use a safe format - write to file in append mode
    code = f"""\
with open('/tmp/img_b64.txt', 'a' if __import__('os').path.exists('/tmp/img_b64.txt') else 'w') as f:
    f.write('''{c}''')
print('Chunk {i} done: {len(c)} chars')
"""
    print(code)
    print(f"=== END CHUNK {i} ===\n")
