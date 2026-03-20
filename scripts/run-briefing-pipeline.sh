#!/bin/bash
# run-briefing-pipeline.sh — Master orchestrator for morning briefing data pipeline
# Runs deterministic Python scripts. No LLM needed.
# Usage: bash run-briefing-pipeline.sh [--jobs-only] [--data-only] [--all]
#
# Crontab entries:
#   0 */2 * * *       bash /root/.openclaw/workspace/scripts/run-briefing-pipeline.sh --data-only
#   0 4,8,12,16 * * * bash /root/.openclaw/workspace/scripts/run-briefing-pipeline.sh --jobs-only
#   0 5 * * 0-4       bash /root/.openclaw/workspace/scripts/run-briefing-pipeline.sh --all

set -euo pipefail

SCRIPTS="/root/.openclaw/workspace/scripts"
LOG_DIR="/var/log/briefing"
DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/$DATE.log"
LOCK_FILE="/tmp/briefing-pipeline.lock"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Simple lock to prevent overlapping runs
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        log "SKIP: Another pipeline run is active (PID $LOCK_PID)"
        exit 0
    fi
    # Stale lock
    rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

run_agent() {
    local name="$1"
    local script="$2"
    local timeout="${3:-60}"
    
    log "START $name"
    local start=$(date +%s)
    
    if timeout "$timeout" python3 "$SCRIPTS/$script" >> "$LOG_FILE" 2>&1; then
        local elapsed=$(( $(date +%s) - start ))
        log "OK    $name (${elapsed}s)"
        return 0
    else
        local code=$?
        local elapsed=$(( $(date +%s) - start ))
        if [ $code -eq 124 ]; then
            log "TIMEOUT $name (>${timeout}s)"
        else
            log "FAIL  $name (exit $code, ${elapsed}s)"
        fi
        return $code
    fi
}

run_parallel() {
    local label="$1"
    shift
    local pids=()
    local names=()
    
    log "--- $label (parallel) ---"
    
    while [ $# -gt 0 ]; do
        local name="$1"
        local script="$2"
        local timeout="${3:-60}"
        shift 3
        
        run_agent "$name" "$script" "$timeout" &
        pids+=($!)
        names+=("$name")
    done
    
    local failures=0
    for i in "${!pids[@]}"; do
        if ! wait "${pids[$i]}"; then
            log "WARN: ${names[$i]} failed"
            ((failures++)) || true
        fi
    done
    
    return $failures
}

MODE="${1:---all}"

case "$MODE" in
    --data-only)
        log "=== DATA AGENTS (every 2h) ==="
        run_parallel "Data Agents" \
            "pipeline"  "pipeline-agent.py"  30 \
            "email"     "email-agent.py"     30 \
            "content"   "content-agent.py"   30 \
            "outreach"  "outreach-agent.py"  15 \
            "system"    "system-agent.py"    30
        ;;
    
    --jobs-only)
        log "=== JOB SOURCES (4x/day) ==="
        # Google Jobs & Bayt: blocked from VPS (403). Disabled.
        run_parallel "Job Sources" \
            "exa"       "jobs-source-exa.py"      180 \
            "linkedin"  "jobs-source-linkedin.py"  120 \
            "indeed"    "jobs-source-indeed.py"    120
        
        log "--- Merge (sequential) ---"
        run_agent "merge" "jobs-merge.py" 30
        
        log "--- LLM Review (sequential) ---"
        run_agent "review" "jobs-review.py" 180
        ;;
    
    --all)
        log "========================================="
        log "  FULL BRIEFING PIPELINE"
        log "========================================="
        
        # Phase 1: Data agents + job sources in parallel
        # Google Jobs & Bayt: blocked from VPS (403). Disabled.
        run_parallel "Phase 1: Data + Sources" \
            "pipeline"  "pipeline-agent.py"       30 \
            "email"     "email-agent.py"           30 \
            "content"   "content-agent.py"         30 \
            "outreach"  "outreach-agent.py"        15 \
            "system"    "system-agent.py"           30 \
            "exa"       "jobs-source-exa.py"       180 \
            "linkedin"  "jobs-source-linkedin.py"  120 \
            "indeed"    "jobs-source-indeed.py"    120
        
        # Phase 2: Merge + Review (sequential, depends on sources)
        log "--- Phase 2: Merge ---"
        run_agent "merge" "jobs-merge.py" 30
        
        log "--- Phase 3: LLM Review ---"
        run_agent "review" "jobs-review.py" 180
        
        log "========================================="
        log "  PIPELINE COMPLETE"
        log "========================================="
        ;;
    
    --learner)
        log "=== DAILY LEARNER (11 PM) ==="
        run_agent "learner" "daily-learner.py" 120
        ;;
    
    *)
        echo "Usage: $0 [--data-only|--jobs-only|--all|--learner]"
        exit 1
        ;;
esac

# Summary
ERRORS=$(grep -c -E "FAIL|TIMEOUT" "$LOG_FILE" 2>/dev/null || true)
ERRORS=${ERRORS:-0}
if [ "$ERRORS" -gt 0 ]; then
    log "⚠️  $ERRORS errors in this run"
    exit 1
else
    log "✅ All clear"
    exit 0
fi
