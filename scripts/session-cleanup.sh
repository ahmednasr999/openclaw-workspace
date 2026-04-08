#!/bin/bash
# session-cleanup.sh — Daily session housekeeping
# Runs at 3 AM Cairo via cron. Cleans JSONL sessions + sessions.json registry.
# Safe: backs up sessions.json before pruning.

SESSIONS_DIR="/root/.openclaw/agents/main/sessions"
LOG="/root/.openclaw/workspace/logs/session-cleanup.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "[$TIMESTAMP] Starting session cleanup" >> "$LOG"

# ── 1. Archive tiny one-shot JSONL files (< 10KB, older than 1 day, no lock) ──
ARCHIVED=0
CUTOFF=$(date -d '1 day ago' +%s)
for f in "$SESSIONS_DIR"/*.jsonl; do
    [ -f "$f" ] || continue
    # Skip topic/channel sessions
    basename "$f" | grep -q "topic\|channel\|dm\|hook" && continue
    SIZE=$(stat -c%s "$f" 2>/dev/null || echo 0)
    MTIME=$(stat -c%Y "$f" 2>/dev/null || echo 0)
    LOCK="${f}.lock"
    if [ "$SIZE" -lt 10240 ] && [ "$MTIME" -lt "$CUTOFF" ] && [ ! -f "$LOCK" ]; then
        mkdir -p "$SESSIONS_DIR/archive"
        mv "$f" "$SESSIONS_DIR/archive/" 2>/dev/null && ARCHIVED=$((ARCHIVED + 1))
    fi
done

# ── 2. Prune stale entries from sessions.json registry (keep < 3 days or persistent) ──
SESSIONS_JSON="$SESSIONS_DIR/sessions.json"
if [ -f "$SESSIONS_JSON" ]; then
    SIZE_BEFORE=$(du -sh "$SESSIONS_JSON" | cut -f1)
    cp "$SESSIONS_JSON" "${SESSIONS_JSON}.bak-$(date +%Y-%m-%d)" 2>/dev/null

    python3 - << 'PYEOF'
import json, os, time

src = '/root/.openclaw/agents/main/sessions/sessions.json'
lock = src + '.lock'

# Check lock - skip if locked
if os.path.exists(lock):
    print("sessions.json locked, skipping registry prune")
    exit(0)

with open(src) as f:
    d = json.load(f)

now = time.time() * 1000
kept = {}
pruned = 0

for k, v in d.items():
    ua = v.get('updatedAt', 0)
    age_days = (now - ua) / (1000 * 86400)
    # Keep persistent sessions (topic/channel/dm) or < 3 days old
    is_persistent = any(x in k for x in ['topic', 'channel', 'dm', 'telegram', 'signal', 'discord', 'whatsapp'])
    if age_days < 3 or is_persistent:
        kept[k] = v
    else:
        pruned += 1

with open(src, 'w') as f:
    json.dump(kept, f)

print(f"sessions.json: {len(d)} -> {len(kept)} entries, pruned {pruned}")
PYEOF

    SIZE_AFTER=$(du -sh "$SESSIONS_JSON" | cut -f1)
    echo "  sessions.json: $SIZE_BEFORE -> $SIZE_AFTER" >> "$LOG"
fi

# ── 3. Remove old backups (keep last 3) ──
ls -t "$SESSIONS_DIR"/sessions.json.bak-* 2>/dev/null | tail -n +4 | xargs rm -f 2>/dev/null

echo "  Archived JSONL: $ARCHIVED files" >> "$LOG"
echo "[$TIMESTAMP] Cleanup done" >> "$LOG"

echo "Session cleanup complete: archived $ARCHIVED JSONL files, sessions.json pruned"
