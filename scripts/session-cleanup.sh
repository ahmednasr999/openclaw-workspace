#!/bin/bash
# session-cleanup.sh — Daily session housekeeping
# Runs at 3 AM Cairo via cron. Cleans JSONL sessions + sessions.json registry.
# Safe: backs up sessions.json before pruning.

set -euo pipefail

SESSIONS_DIR="${SESSION_CLEANUP_DIR:-/root/.openclaw/agents/main/sessions}"
LOG="${SESSION_CLEANUP_LOG:-/root/.openclaw/workspace/logs/session-cleanup.log}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "$(dirname "$LOG")"

echo "[$TIMESTAMP] Starting session cleanup" >> "$LOG"

# ── 1. Archive tiny one-shot JSONL files (< 10KB, older than 1 day, no lock) ──
ARCHIVED=0
CUTOFF=$(date -d '1 day ago' +%s)
for f in "$SESSIONS_DIR"/*.jsonl; do
    [ -f "$f" ] || continue
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
PRUNED=0
REGISTRY_STATUS="missing"
REGISTRY_BEFORE=0
REGISTRY_AFTER=0
if [ -f "$SESSIONS_JSON" ]; then
    SIZE_BEFORE=$(du -sh "$SESSIONS_JSON" | cut -f1)
    cp "$SESSIONS_JSON" "${SESSIONS_JSON}.bak-$(date +%Y-%m-%d)" 2>/dev/null || true

    PRUNE_ENV=$(mktemp)
    python3 - "$SESSIONS_JSON" > "$PRUNE_ENV" <<'PYEOF'
import json, os, sys, time

src = sys.argv[1]
lock = src + '.lock'

status = 'ok'
before = 0
after = 0
pruned = 0

try:
    if os.path.exists(lock):
        status = 'locked'
    else:
        with open(src) as f:
            data = json.load(f)

        now = time.time() * 1000
        kept = {}
        before = len(data)

        for key, value in data.items():
            updated_at = value.get('updatedAt', 0)
            age_days = (now - updated_at) / (1000 * 86400)
            is_persistent = any(x in key for x in ['topic', 'channel', 'dm', 'telegram', 'signal', 'discord', 'whatsapp'])
            if age_days < 3 or is_persistent:
                kept[key] = value
            else:
                pruned += 1

        after = len(kept)
        with open(src, 'w') as f:
            json.dump(kept, f)
except Exception:
    status = 'error'

print(f'PRUNE_STATUS={status}')
print(f'PRUNE_BEFORE={before}')
print(f'PRUNE_AFTER={after}')
print(f'PRUNE_COUNT={pruned}')
PYEOF
    # shellcheck disable=SC1090
    source "$PRUNE_ENV"
    rm -f "$PRUNE_ENV"

    REGISTRY_STATUS="${PRUNE_STATUS:-error}"
    REGISTRY_BEFORE="${PRUNE_BEFORE:-0}"
    REGISTRY_AFTER="${PRUNE_AFTER:-0}"
    PRUNED="${PRUNE_COUNT:-0}"

    SIZE_AFTER=$(du -sh "$SESSIONS_JSON" | cut -f1)
    echo "  sessions.json: $SIZE_BEFORE -> $SIZE_AFTER (${REGISTRY_STATUS}, pruned ${PRUNED})" >> "$LOG"
fi

# ── 3. Remove old backups (keep last 3) ──
BACKUPS_REMOVED=0
mapfile -t OLD_BACKUPS < <(ls -1t "$SESSIONS_DIR"/sessions.json.bak-* 2>/dev/null | tail -n +4 || true)
if [ ${#OLD_BACKUPS[@]} -gt 0 ]; then
    rm -f -- "${OLD_BACKUPS[@]}"
    BACKUPS_REMOVED=${#OLD_BACKUPS[@]}
fi

END_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "  Archived JSONL: $ARCHIVED files" >> "$LOG"
echo "[$END_TIMESTAMP] Cleanup done" >> "$LOG"

if [ "$ARCHIVED" -gt 0 ] || [ "$PRUNED" -gt 0 ] || [ "$BACKUPS_REMOVED" -gt 0 ] || [ "$REGISTRY_STATUS" = "locked" ] || [ "$REGISTRY_STATUS" = "error" ]; then
    echo "session-cleanup: archived=$ARCHIVED pruned=$PRUNED backups_removed=$BACKUPS_REMOVED registry=$REGISTRY_STATUS"
fi
