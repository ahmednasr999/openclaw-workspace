#!/usr/bin/env bash
# Daily local snapshot - compressed OpenClaw state snapshot.
# Runs at 23:00 Cairo. Keeps the latest verified archive only.
# Streams directly to zstd so no large uncompressed snapshot directory is created.

set -Eeuo pipefail
umask 077

DATE="${OPENCLAW_SNAPSHOT_DATE:-$(date +%Y%m%d)}"
SRC="${OPENCLAW_SNAPSHOT_SRC:-/root/.openclaw}"
SNAPSHOT_ROOT="${OPENCLAW_SNAPSHOT_ROOT:-/root}"
SNAPSHOT_NAME="openclaw-snapshot-${DATE}"
ARCHIVE="${SNAPSHOT_ROOT}/${SNAPSHOT_NAME}.tar.zst"
TMP_ARCHIVE="${ARCHIVE}.tmp.$$"
LOCK_FILE="${OPENCLAW_SNAPSHOT_LOCK_FILE:-/tmp/openclaw-daily-snapshot.lock}"
SQLITE_STAGE="${SNAPSHOT_ROOT}/.${SNAPSHOT_NAME}.sqlite-stage.$$"
SQLITE_TREE="${SQLITE_STAGE}/__sqlite__"
SQLITE_EXCLUDES="${SQLITE_STAGE}/exclude-live-sqlite.txt"
SQLITE_PATHS="${SQLITE_STAGE}/sqlite-paths.txt"

log() { echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $*"; }

if [ -f "$LOCK_FILE" ]; then
  old_pid=$(cat "$LOCK_FILE" 2>/dev/null || true)
  if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
    log "SKIP: snapshot already running (PID $old_pid)"
    exit 0
  fi
fi
echo $$ > "$LOCK_FILE"
cleanup() {
  rm -f -- "$LOCK_FILE" "$TMP_ARCHIVE"
  rm -rf --one-file-system -- "$SQLITE_STAGE"
}
trap cleanup EXIT

log "Snapshot started"

if [[ ! -d "$SRC" ]]; then
  log "ERROR: snapshot source does not exist: $SRC"
  exit 1
fi
if ! command -v tar >/dev/null 2>&1 \
  || ! command -v zstd >/dev/null 2>&1 \
  || ! command -v sqlite3 >/dev/null 2>&1; then
  log "ERROR: tar, zstd, and sqlite3 are required"
  exit 1
fi
mkdir -p "$SNAPSHOT_ROOT"
mkdir -p "$SQLITE_TREE"
: > "$SQLITE_EXCLUDES"
: > "$SQLITE_PATHS"

# Discover SQLite databases in the included tree. Their live files and volatile
# sidecars must not be read by tar: each database is captured with SQLite's
# online backup API and overlaid at its original path in the archive.
sqlite_bytes=0
sqlite_count=0
while IFS= read -r -d '' database; do
  if [[ "$(head -c 15 -- "$database" 2>/dev/null || true)" != 'SQLite format 3' ]]; then
    continue
  fi
  relative_path="${database#"$SRC"/}"
  printf '%s\n' "$relative_path" >> "$SQLITE_PATHS"
  printf './%s\n' "$relative_path" >> "$SQLITE_EXCLUDES"
  database_size=$(stat -c %s -- "$database" 2>/dev/null || printf '0')
  sqlite_bytes=$((sqlite_bytes + database_size))
  sqlite_count=$((sqlite_count + 1))
done < <(
  find "$SRC" -xdev \
    \( -path "$SRC/backups" \
      -o -path "$SRC/media" \
      -o -path "$SRC/browser" \
      -o -path "$SRC/plugin-runtime-deps" \
      -o -path "$SRC/lcm-files" \
      -o -path "$SRC/logs" \
      -o -name node_modules \
      -o -name .cache \) -prune \
    -o -type f \( -name '*.sqlite' \
      -o -name '*.sqlite3' \
      -o -name '*.db' \
      -o -name '*.sqlite.migrated' \
      -o -name '*.sqlite3.migrated' \
      -o -name '*.db.migrated' \) -print0
)

# Preserve the previous verified archive until its replacement is complete.
previous_size=0
if [[ -s "$ARCHIVE" ]]; then
  previous_size=$(stat -c %s "$ARCHIVE")
else
  previous_archive=$(find "$SNAPSHOT_ROOT" -maxdepth 1 -type f \
    -name 'openclaw-snapshot-*.tar.zst' -printf '%T@ %s\n' 2>/dev/null \
    | sort -nr | awk 'NR==1 {print $2}')
  previous_size="${previous_archive:-0}"
fi
available_bytes=$(df -PB1 "$SNAPSHOT_ROOT" | awk 'NR==2 {print $4}')
minimum_bytes=$((8 * 1024 * 1024 * 1024))
safe_reserve_bytes="${OPENCLAW_SNAPSHOT_SAFE_RESERVE_BYTES:-$((15 * 1024 * 1024 * 1024))}"
if (( previous_size > 0 )); then
  estimated_archive_bytes=$((previous_size + previous_size / 2))
  minimum_bytes=$((sqlite_bytes + estimated_archive_bytes + safe_reserve_bytes))
elif (( sqlite_bytes > 0 )); then
  minimum_bytes=$((sqlite_bytes + 8 * 1024 * 1024 * 1024 + safe_reserve_bytes))
else
  minimum_bytes=$((8 * 1024 * 1024 * 1024 + safe_reserve_bytes))
fi
if (( available_bytes < minimum_bytes )); then
  log "ERROR: insufficient free space for safe atomic snapshot: available=${available_bytes} required=${minimum_bytes}"
  exit 1
fi

log "Creating consistent online backups of ${sqlite_count} SQLite databases"
while IFS= read -r relative_path; do
  [[ -n "$relative_path" ]] || continue
  database="$SRC/$relative_path"
  staged_database="$SQLITE_TREE/$relative_path"
  mkdir -p -- "$(dirname -- "$staged_database")"
  sqlite3 -cmd '.timeout 30000' "$database" ".backup '$staged_database'"
  if [[ ! -s "$staged_database" ]] \
    || [[ "$(head -c 15 -- "$staged_database")" != 'SQLite format 3' ]] \
    || ! sqlite3 "$staged_database" 'PRAGMA schema_version;' >/dev/null; then
    log "ERROR: SQLite backup validation failed: $relative_path"
    exit 1
  fi
done < "$SQLITE_PATHS"
log "SQLite online backups complete"

log "Writing compressed snapshot directly to temporary archive"
tar -C "$SRC" \
  --one-file-system \
  --numeric-owner \
  --ignore-failed-read \
  --warning=no-file-changed \
  --transform="s|^\\./__sqlite__$|${SNAPSHOT_NAME}|;s|^\\./__sqlite__/|${SNAPSHOT_NAME}/|;s|^\\.|${SNAPSHOT_NAME}|" \
  --exclude='./backups' \
  --exclude='./media' \
  --exclude='./browser' \
  --exclude='./plugin-runtime-deps' \
  --exclude='./lcm-files' \
  --exclude='./logs' \
  --exclude='node_modules' \
  --exclude='.cache' \
  --exclude='*-wal' \
  --exclude='*-wal.*' \
  --exclude='*-shm' \
  --exclude='*-shm.*' \
  --exclude='*-journal' \
  --exclude='*-journal.*' \
  --exclude-from="$SQLITE_EXCLUDES" \
  -C "$SRC" . \
  -C "$SQLITE_STAGE" ./__sqlite__ \
  --use-compress-program='zstd -T2 -6' \
  -cf "$TMP_ARCHIVE"

log "Verifying compressed snapshot"
zstd -t "$TMP_ARCHIVE"
required_archive_paths=(
  "$SNAPSHOT_NAME/openclaw.json"
  "$SNAPSHOT_NAME/workspace/MEMORY.md"
)
while IFS= read -r relative_path; do
  [[ -n "$relative_path" ]] || continue
  required_archive_paths+=("$SNAPSHOT_NAME/$relative_path")
done < "$SQLITE_PATHS"
tar -I zstd -tf "$TMP_ARCHIVE" "${required_archive_paths[@]}" >/dev/null

mv -f -- "$TMP_ARCHIVE" "$ARCHIVE"
chmod 600 "$ARCHIVE"
log "Verified snapshot promoted: $ARCHIVE ($(du -h "$ARCHIVE" | awk '{print $1}'))"

# Remove stale raw directories left by the former design only after a valid archive exists.
find "$SNAPSHOT_ROOT" -xdev -maxdepth 1 -type d -name 'openclaw-snapshot-*' \
  -exec rm -rf --one-file-system {} +

# Retain only the newest verified compressed snapshot archive.
find "$SNAPSHOT_ROOT" -maxdepth 1 -type f -name 'openclaw-snapshot-*.tar.zst' \
  ! -path "$ARCHIVE" -print0 | xargs -0 -r rm -f --
log "Snapshot retention complete: kept latest verified archive"
log "Snapshot complete"
