# This script generates the workbench code for writing base64 chunks
# Run on server to generate the code, then paste into workbench

b64 = open('/tmp/linkedin-img-b64.txt').read()
total = len(b64)
chunk_size = 27000

output_parts = []
for i in range(0, total, chunk_size):
    chunk = b64[i:i+chunk_size]
    idx = i // chunk_size
    mode = "'a'" if i > 0 else "'w'"
    # Escape triple quotes - use double quotes for the outer string
    escaped = chunk.replace('"', '\\"')
    code = f"data = \\\"{escaped}\\\"\nwith open('/tmp/b64_img.txt', {mode}) as f:\n    f.write(data)\nprint('chunk {idx} ok: {len(chunk)}')"
    print(f"### CHUNK {idx} ({len(chunk)} chars) ###")
    print(code)
    print()
