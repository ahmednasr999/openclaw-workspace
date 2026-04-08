import base64
# Read the base64 from server file - this runs on server
with open('/tmp/linkedin-img-b64.txt', 'r') as f:
    data = f.read()
half = len(data) // 2
print(f"TOTAL_CHARS={len(data)}")
print(f"HALF={half}")
# Write chunk 1 to a server file the workbench CAN'T see
with open('/tmp/img_b64_p1.txt', 'w') as f:
    f.write(data[:half])
print("CHUNK1_WRITTEN")
with open('/tmp/img_b64_p2.txt', 'w') as f:
    f.write(data[half:])
print("CHUNK2_WRITTEN")
