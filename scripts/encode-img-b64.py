import base64
with open('/root/.openclaw/media/inbound/file_266---aade39c1-5899-46d4-b02c-6f2a88dfc8c1.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
print(len(b64), 'chars base64')
with open('/tmp/linkedin-img-b64.txt', 'w') as f:
    f.write(b64)
print('Saved to /tmp/linkedin-img-b64.txt')
