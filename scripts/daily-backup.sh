#!/bin/bash
# daily-backup.sh — Git-based workspace backup with lock + retry + secret-safe push
# Cron: 0 20 * * * (8 PM Cairo)
set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
LOCK_FILE="/tmp/daily-backup.lock"
LOG_FILE="/root/.openclaw/workspace/logs/openclaw-backup.log"
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
# Stage source and explicitly approved non-secret config only. Runtime state
# (data, logs, memory, sessions, archives, media, jobs, and databases) must
# remain local and is deliberately excluded even when already tracked.
if ! git diff --cached --quiet; then
    log "ERROR: Git index already has staged changes; refusing to mix them into backup"
    exit 1
fi
for path in \
    scripts skills docs tests templates prompts cron-skills .github \
    AGENTS.md TOOLS.md .gitignore \
    config/root-crontab.managed \
    config/tool-hooks.yaml \
    config/tool-permissions.yaml; do
    [ -e "$path" ] && git add -- "$path" 2>/dev/null || true
done

# Refuse generated, backup, database, archive, and log artifacts even if one
# appears beneath an approved source directory.
while IFS= read -r -d '' path; do
    case "$path" in
        *.db|*.db-*|*.sqlite|*.sqlite3|*.log|*.jsonl|*.gz|*.zip|*.bak|*.backup|*.orig|*~)
            git reset -q -- "$path" 2>/dev/null || true
            ;;
    esac
done < <(git diff --cached --name-only -z)

if ! git diff --cached --quiet; then
    log "Changes detected, committing..."
else
    log "No significant changes — nothing to commit"
    exit 0
fi

# ── Commit (non-blocking) ──
COMMIT_MSG="Auto-backup $(date -u +%Y-%m-%d_%H:%M)"
log "Committing: $COMMIT_MSG"
git commit -m "$COMMIT_MSG" 2>/dev/null || true

# ── Push with retry ──
for attempt in $(seq 1 $MAX_RETRIES); do
    log "Push attempt $attempt/$MAX_RETRIES..."
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    PUSH_OUT=$(git push origin "$BRANCH:$BRANCH" 2>&1)
    PUSH_EXIT=$?
    
    if [ $PUSH_EXIT -eq 0 ]; then
        log "SUCCESS: Pushed to origin $BRANCH"
        exit 0
    fi
    
    # Check if blocked by secret scanning
    if echo "$PUSH_OUT" | grep -qi "secret-scanning\|secret scanning\|rule violations\|blocked push"; then
        log "WARN: Push blocked by GitHub secret scanning (secret in committed file)"
        log "WARN: Run: bash scripts/secret-scrub.sh to remove secrets from history"
        log "WARN: Commit succeeded locally — remote sync needs manual attention"
        exit 0  # Don't fail the backup for this
    fi
    
    # Try pull + retry for normal divergence
    log "Push failed — attempting merge-and-retry..."
    git pull --no-rebase origin "$BRANCH" 2>/dev/null || true
    if [ $attempt -lt $MAX_RETRIES ]; then
        log "Waiting ${RETRY_WAIT}s before retry..."
        sleep $RETRY_WAIT
    fi
done

log "ERROR: All $MAX_RETRIES push attempts failed"
exit 1
