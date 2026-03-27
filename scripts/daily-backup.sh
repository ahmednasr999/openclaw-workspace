#!/bin/bash
# daily-backup.sh — Git-based workspace backup with lock + retry
# Cron: 0 20 * * * (8 PM Cairo)
set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
LOCK_FILE="/tmp/daily-backup.lock"
LOG_FILE="/tmp/openclaw-backup.log"
MAX_RETRIES=3
RETRY_WAIT=15

cd "$WORKSPACE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ── Lock ──
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        log "SKIP: Backup already running (PID $LOCK_PID)"
        exit 0
    fi
    log "Stale lock found (PID $LOCK_PID), removing..."
    rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# ── Nothing to commit check ──
if git status --porcelain | grep -q .; then
    log "Changes detected, committing..."
else
    log "No changes — nothing to commit"
    exit 0
fi

# ── Commit ──
git add -A
COMMIT_MSG="Auto-backup $(date -u +%Y-%m-%d_%H:%M)"
log "Committing: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# ── Pull with merge (not rebase) ──
log "Pulling remote changes..."
if ! git pull --no-rebase origin main >> "$LOG_FILE" 2>&1; then
    log "WARN: git pull failed (diverged history or network) — continuing with push anyway"
fi

# ── Push with retry (handles race condition with other backup runs) ──
for attempt in $(seq 1 $MAX_RETRIES); do
    log "Push attempt $attempt/$MAX_RETRIES..."
    if git push origin main >> "$LOG_FILE" 2>&1; then
        log "SUCCESS: Pushed to origin main"
        exit 0
    else
        log "Push failed (attempt $attempt) — pulling and retrying..."
        git pull --no-rebase origin main >> "$LOG_FILE" 2>&1 || true
        if [ $attempt -lt $MAX_RETRIES ]; then
            log "Waiting ${RETRY_WAIT}s before retry..."
            sleep $RETRY_WAIT
        fi
    fi
done

log "ERROR: All $MAX_RETRIES push attempts failed — manual intervention needed"
exit 1
