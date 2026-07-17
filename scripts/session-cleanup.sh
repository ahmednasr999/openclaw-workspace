#!/bin/bash
# session-cleanup.sh - Daily session housekeeping
# Runs at 3 AM Cairo via cron. Cleans JSONL sessions + sessions.json registries.
# Safe: backs up sessions.json before pruning and rotates older generated backups.

set -euo pipefail

SESSION_CLEANUP_SINGLE_DIR="${SESSION_CLEANUP_DIR:-}"
SESSION_CLEANUP_ROOT="${SESSION_CLEANUP_ROOT:-/root/.openclaw/agents}"
SESSION_ARCHIVE_DIR="${SESSION_CLEANUP_ARCHIVE_DIR:-/root/.openclaw/session-archives}"
RETIRE_DAYS="${SESSION_CLEANUP_RETIRE_DAYS:-14}"
LOOSE_ARCHIVE_DAYS="${SESSION_CLEANUP_LOOSE_ARCHIVE_DAYS:-7}"
CODEX_SESSION_RETIRE_DAYS="${SESSION_CLEANUP_CODEX_RETIRE_DAYS:-14}"
LOG="${SESSION_CLEANUP_LOG:-/root/.openclaw/workspace/logs/session-cleanup.log}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "$(dirname "$LOG")"

echo "[$TIMESTAMP] Starting session cleanup" >> "$LOG"

TOTAL_ARCHIVED=0
TOTAL_PRUNED=0
TOTAL_BACKUPS_REMOVED=0
TOTAL_BACKUP_BYTES=0
TOTAL_RETIRED_ARCHIVED=0
TOTAL_RETIRED_BYTES=0
TOTAL_CODEX_SESSION_ARCHIVED=0
TOTAL_CODEX_SESSION_BYTES=0
STATUS_NOTES=()

cleanup_dir() {
    local SESSIONS_DIR="$1"
    local label
    label="${SESSIONS_DIR#/root/.openclaw/agents/}"

    [ -d "$SESSIONS_DIR" ] || return 0

    echo "  [$label]" >> "$LOG"

    # 1. Archive tiny one-shot JSONL files (< 10KB, older than 1 day, no lock).
    local ARCHIVED=0
    local CUTOFF
    CUTOFF=$(date -d '1 day ago' +%s)
    for f in "$SESSIONS_DIR"/*.jsonl; do
        [ -f "$f" ] || continue
        basename "$f" | grep -q "topic\|channel\|dm\|hook" && continue
        local SIZE MTIME LOCK
        SIZE=$(stat -c%s "$f" 2>/dev/null || echo 0)
        MTIME=$(stat -c%Y "$f" 2>/dev/null || echo 0)
        LOCK="${f}.lock"
        if [ "$SIZE" -lt 10240 ] && [ "$MTIME" -lt "$CUTOFF" ] && [ ! -f "$LOCK" ]; then
            mkdir -p "$SESSIONS_DIR/archive"
            mv "$f" "$SESSIONS_DIR/archive/" 2>/dev/null && ARCHIVED=$((ARCHIVED + 1))
        fi
    done

    # 2. Prune stale entries from sessions.json registry (keep < 3 days or persistent).
    local SESSIONS_JSON="$SESSIONS_DIR/sessions.json"
    local PRUNED=0
    local REGISTRY_STATUS="missing"
    local REGISTRY_BEFORE=0
    local REGISTRY_AFTER=0
    if [ -f "$SESSIONS_JSON" ]; then
        local SIZE_BEFORE SIZE_AFTER PRUNE_ENV
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
        echo "    sessions.json: $SIZE_BEFORE -> $SIZE_AFTER (${REGISTRY_STATUS}, pruned ${PRUNED})" >> "$LOG"
    fi

    # 3. Rotate generated backup churn. Keep latest 3 sessions.json backups and
    # latest 2 JSONL edit backups per source transcript.
    local BACKUP_ENV BACKUPS_REMOVED BACKUP_BYTES
    BACKUP_ENV=$(mktemp)
    python3 - "$SESSIONS_DIR" > "$BACKUP_ENV" <<'PYEOF'
from pathlib import Path
import os
import sys

root = Path(sys.argv[1])
removed = 0
freed = 0

def remove_file(path: Path) -> None:
    global removed, freed
    try:
        size = path.stat().st_size
        path.unlink()
    except FileNotFoundError:
        return
    except OSError:
        return
    removed += 1
    freed += size

json_backups = []
for pattern in ("sessions.json.bak-*", "sessions.json.bak.*", "sessions.json.bak-gpt55-*"):
    json_backups.extend(root.glob(pattern))
json_backups = sorted(set(json_backups), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
for path in json_backups[3:]:
    remove_file(path)

groups = {}
for pattern in ("*.jsonl.bak-*", "*.jsonl.bak.*"):
    for path in root.glob(pattern):
        key = path.name.split(".jsonl.bak", 1)[0]
        groups.setdefault(key, []).append(path)

for paths in groups.values():
    paths = sorted(set(paths), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    for path in paths[2:]:
        remove_file(path)

print(f'BACKUPS_REMOVED={removed}')
print(f'BACKUP_BYTES={freed}')
PYEOF
    # shellcheck disable=SC1090
    source "$BACKUP_ENV"
    rm -f "$BACKUP_ENV"

    BACKUPS_REMOVED="${BACKUPS_REMOVED:-0}"
    BACKUP_BYTES="${BACKUP_BYTES:-0}"

    # 4. Preserve and remove retired transcript artifacts older than the retention
    # window. Live/current JSONL files are not included.
    local RETIRED_ENV RETIRED_ARCHIVED RETIRED_BYTES RETIRED_ARCHIVE
    RETIRED_ENV=$(mktemp)
    python3 - "$SESSIONS_DIR" "$SESSION_ARCHIVE_DIR" "$label" "$RETIRE_DAYS" "$LOOSE_ARCHIVE_DAYS" > "$RETIRED_ENV" <<'PYEOF'
from pathlib import Path
import re
import sys
import tarfile
import time

sessions_dir = Path(sys.argv[1])
archive_root = Path(sys.argv[2])
label = re.sub(r'[^A-Za-z0-9_.-]+', '-', sys.argv[3]).strip('-') or 'sessions'
retire_days = int(sys.argv[4])
loose_days = int(sys.argv[5])
now = time.time()
retire_cutoff = now - retire_days * 86400
loose_cutoff = now - loose_days * 86400

def old_enough(path: Path, cutoff: float) -> bool:
    try:
        return path.is_file() and path.stat().st_mtime < cutoff and not Path(str(path) + '.lock').exists()
    except OSError:
        return False

def retired_candidate(path: Path) -> bool:
    name = path.name
    markers = ('.jsonl.bak', '.jsonl.deleted', '.trajectory.jsonl.deleted', '.jsonl.reset.')
    return old_enough(path, retire_cutoff) and (name.endswith('.trajectory.jsonl') or any(marker in name for marker in markers))

candidates = [p for p in sessions_dir.iterdir() if retired_candidate(p)]
archive_dir = sessions_dir / 'archive'
if archive_dir.is_dir():
    candidates.extend(p for p in archive_dir.iterdir() if p.name.endswith('.jsonl') and old_enough(p, loose_cutoff))

# Preserve deterministic order and avoid duplicate paths.
candidates = sorted(set(candidates), key=lambda p: str(p))
if not candidates:
    print('RETIRED_ARCHIVED=0')
    print('RETIRED_BYTES=0')
    print('RETIRED_ARCHIVE=')
    raise SystemExit(0)

archive_root.mkdir(parents=True, exist_ok=True)
archive_path = archive_root / f"session-retired-{label}-{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"
bytes_total = sum(p.stat().st_size for p in candidates)
with tarfile.open(archive_path, 'w:gz') as tar:
    for path in candidates:
        tar.add(path, arcname=f"{label}/{path.relative_to(sessions_dir)}")

with tarfile.open(archive_path, 'r:gz') as tar:
    members = [m for m in tar.getmembers() if m.isfile()]
if len(members) != len(candidates):
    raise SystemExit(f'archive verification failed: expected {len(candidates)} files, got {len(members)}')

removed = 0
for path in candidates:
    try:
        path.unlink()
        removed += 1
    except OSError:
        pass

print(f'RETIRED_ARCHIVED={removed}')
print(f'RETIRED_BYTES={bytes_total}')
print(f'RETIRED_ARCHIVE={archive_path}')
PYEOF
    # shellcheck disable=SC1090
    source "$RETIRED_ENV"
    rm -f "$RETIRED_ENV"

    RETIRED_ARCHIVED="${RETIRED_ARCHIVED:-0}"
    RETIRED_BYTES="${RETIRED_BYTES:-0}"
    RETIRED_ARCHIVE="${RETIRED_ARCHIVE:-}"

    echo "    Archived JSONL: $ARCHIVED files" >> "$LOG"
    echo "    Backup rotation: removed $BACKUPS_REMOVED files, freed ${BACKUP_BYTES} bytes" >> "$LOG"
    if [ "$RETIRED_ARCHIVED" -gt 0 ]; then
        echo "    Retired transcript archive: archived $RETIRED_ARCHIVED files, preserved ${RETIRED_BYTES} bytes at $RETIRED_ARCHIVE" >> "$LOG"
    fi

    TOTAL_ARCHIVED=$((TOTAL_ARCHIVED + ARCHIVED))
    TOTAL_PRUNED=$((TOTAL_PRUNED + PRUNED))
    TOTAL_BACKUPS_REMOVED=$((TOTAL_BACKUPS_REMOVED + BACKUPS_REMOVED))
    TOTAL_BACKUP_BYTES=$((TOTAL_BACKUP_BYTES + BACKUP_BYTES))
    TOTAL_RETIRED_ARCHIVED=$((TOTAL_RETIRED_ARCHIVED + RETIRED_ARCHIVED))
    TOTAL_RETIRED_BYTES=$((TOTAL_RETIRED_BYTES + RETIRED_BYTES))
    if [ "$REGISTRY_STATUS" = "locked" ] || [ "$REGISTRY_STATUS" = "error" ]; then
        STATUS_NOTES+=("$label:$REGISTRY_STATUS")
    fi
}

cleanup_codex_sessions_dir() {
    local CODEX_SESSIONS_DIR="$1"
    local label
    label="${CODEX_SESSIONS_DIR#/root/.openclaw/agents/}"

    [ -d "$CODEX_SESSIONS_DIR" ] || return 0

    local CODEX_ENV CODEX_ARCHIVED CODEX_BYTES CODEX_ARCHIVE
    CODEX_ENV=$(mktemp)
    python3 - "$CODEX_SESSIONS_DIR" "$SESSION_ARCHIVE_DIR" "$label" "$CODEX_SESSION_RETIRE_DAYS" > "$CODEX_ENV" <<'PYEOF'
from pathlib import Path
import re
import sys
import tarfile
import time

sessions_root = Path(sys.argv[1])
archive_root = Path(sys.argv[2])
label = re.sub(r'[^A-Za-z0-9_.-]+', '-', sys.argv[3]).strip('-') or 'codex-sessions'
retire_days = int(sys.argv[4])
cutoff = time.time() - retire_days * 86400

candidates = []
for path in sessions_root.rglob('*.jsonl'):
    try:
        if not path.is_file():
            continue
        if Path(str(path) + '.lock').exists():
            continue
        if path.stat().st_mtime >= cutoff:
            continue
    except OSError:
        continue
    candidates.append(path)

candidates = sorted(set(candidates), key=lambda p: str(p))
if not candidates:
    print('CODEX_ARCHIVED=0')
    print('CODEX_BYTES=0')
    print('CODEX_ARCHIVE=')
    raise SystemExit(0)

archive_root.mkdir(parents=True, exist_ok=True)
archive_path = archive_root / f"codex-sessions-{label}-{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"
bytes_total = sum(p.stat().st_size for p in candidates)
with tarfile.open(archive_path, 'w:gz') as tar:
    for path in candidates:
        tar.add(path, arcname=f"{label}/{path.relative_to(sessions_root)}")

with tarfile.open(archive_path, 'r:gz') as tar:
    members = [m for m in tar.getmembers() if m.isfile()]
if len(members) != len(candidates):
    raise SystemExit(f'archive verification failed: expected {len(candidates)} files, got {len(members)}')

removed = 0
for path in candidates:
    try:
        path.unlink()
        removed += 1
    except OSError:
        pass

# Remove empty date folders left behind, deepest first.
for folder in sorted(sessions_root.rglob('*'), key=lambda p: len(p.parts), reverse=True):
    if folder.is_dir():
        try:
            folder.rmdir()
        except OSError:
            pass

print(f'CODEX_ARCHIVED={removed}')
print(f'CODEX_BYTES={bytes_total}')
print(f'CODEX_ARCHIVE={archive_path}')
PYEOF
    # shellcheck disable=SC1090
    source "$CODEX_ENV"
    rm -f "$CODEX_ENV"

    CODEX_ARCHIVED="${CODEX_ARCHIVED:-0}"
    CODEX_BYTES="${CODEX_BYTES:-0}"
    CODEX_ARCHIVE="${CODEX_ARCHIVE:-}"

    if [ "$CODEX_ARCHIVED" -gt 0 ]; then
        echo "  [codex:$label] archived $CODEX_ARCHIVED rollout transcripts, preserved $CODEX_BYTES bytes at $CODEX_ARCHIVE" >> "$LOG"
    fi

    TOTAL_CODEX_SESSION_ARCHIVED=$((TOTAL_CODEX_SESSION_ARCHIVED + CODEX_ARCHIVED))
    TOTAL_CODEX_SESSION_BYTES=$((TOTAL_CODEX_SESSION_BYTES + CODEX_BYTES))
}

if [ -n "$SESSION_CLEANUP_SINGLE_DIR" ]; then
    cleanup_dir "$SESSION_CLEANUP_SINGLE_DIR"
else
    while IFS= read -r dir; do
        cleanup_dir "$dir"
    done < <(find "$SESSION_CLEANUP_ROOT" -mindepth 2 -maxdepth 2 -type d -name sessions 2>/dev/null | sort)
    while IFS= read -r dir; do
        cleanup_codex_sessions_dir "$dir"
    done < <(find "$SESSION_CLEANUP_ROOT" -mindepth 4 -maxdepth 4 -type d -path "*/agent/codex-home/sessions" 2>/dev/null | sort)
fi

END_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "[$END_TIMESTAMP] Cleanup done" >> "$LOG"

if [ "$TOTAL_ARCHIVED" -gt 0 ] || [ "$TOTAL_PRUNED" -gt 0 ] || [ "$TOTAL_BACKUPS_REMOVED" -gt 0 ] || [ "$TOTAL_RETIRED_ARCHIVED" -gt 0 ] || [ "$TOTAL_CODEX_SESSION_ARCHIVED" -gt 0 ] || [ ${#STATUS_NOTES[@]} -gt 0 ]; then
    note=""
    if [ ${#STATUS_NOTES[@]} -gt 0 ]; then
        note=" notes=$(IFS=,; echo "${STATUS_NOTES[*]}")"
    fi
    echo "session-cleanup: archived=$TOTAL_ARCHIVED pruned=$TOTAL_PRUNED backups_removed=$TOTAL_BACKUPS_REMOVED backup_bytes=$TOTAL_BACKUP_BYTES retired_archived=$TOTAL_RETIRED_ARCHIVED retired_bytes=$TOTAL_RETIRED_BYTES codex_archived=$TOTAL_CODEX_SESSION_ARCHIVED codex_bytes=$TOTAL_CODEX_SESSION_BYTES$note"
fi
