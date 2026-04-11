#!/usr/bin/env python3
import json
from datetime import datetime, UTC
from pathlib import Path

QUEUE = Path('/root/.openclaw/workspace/data/cmo-outreach-queue.json')
if not QUEUE.exists():
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps({"last_updated": datetime.utcnow().isoformat() + 'Z', "items": []}, indent=2))

payload = json.loads(QUEUE.read_text())
items = payload.get('items', [])
queued = [i for i in items if i.get('status', 'queued') == 'queued']

lines = []
lines.append(f"📬 CMO Outreach Queue — {datetime.now().strftime('%d %b %Y')}")
lines.append("━━━━━━━━━━━━━━━━━━━━")
lines.append(f"- Companies queued: {len(queued)}")
if queued:
    for item in queued[:20]:
        lines.append(f"- {item.get('company')} | {item.get('job_title')} | source={item.get('source')} | queued={item.get('queued_at')}")
    if len(queued) > 20:
        lines.append(f"- ... plus {len(queued) - 20} more")
else:
    lines.append("- No queued companies this week")

for item in queued:
    item['status'] = 'exported'
    item['exported_at'] = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
payload['last_updated'] = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
QUEUE.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

print('\n'.join(lines))
