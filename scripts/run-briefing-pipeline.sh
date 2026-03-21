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

classify_failure() {
    # Classify failure type from exit code and recent log output
    local code="$1"
    local name="$2"
    local tail_output
    tail_output=$(tail -5 "$LOG_FILE" 2>/dev/null || echo "")
    
    # Timeout = transient
    if [ "$code" -eq 124 ]; then
        echo "TRANSIENT:timeout"
        return
    fi
    
    # Auth/config errors
    if echo "$tail_output" | grep -qiE '401|403|unauthorized|forbidden|invalid.*token|invalid.*key|auth.*fail'; then
        echo "CONFIG:auth"
        return
    fi
    
    # Connection errors = transient
    if echo "$tail_output" | grep -qiE 'connection.*refused|connection.*reset|dns|resolve|ETIMEDOUT|network.*unreachable|ssl.*error|socket.*timeout'; then
        echo "TRANSIENT:network"
        return
    fi
    
    # Rate limits = transient
    if echo "$tail_output" | grep -qiE '429|rate.limit|too.many.requests|throttl'; then
        echo "TRANSIENT:ratelimit"
        return
    fi
    
    # Schema/logic errors
    if echo "$tail_output" | grep -qiE 'KeyError|TypeError|ValueError|IndexError|AttributeError|schema|validation.*error|invalid.*param|missing.*field'; then
        echo "LOGIC:script_bug"
        return
    fi
    
    # Import/dependency errors
    if echo "$tail_output" | grep -qiE 'ModuleNotFoundError|ImportError|No module named'; then
        echo "CONFIG:dependency"
        return
    fi
    
    # Unknown
    echo "UNKNOWN:exit_$code"
}

FAILURE_LOG="/var/log/briefing/failures-$(date +%Y-%m-%d).jsonl"

log_failure() {
    local name="$1"
    local classification="$2"
    local code="$3"
    local elapsed="$4"
    local category="${classification%%:*}"
    local detail="${classification#*:}"
    
    printf '{"ts":"%s","agent":"%s","category":"%s","detail":"%s","exit_code":%d,"elapsed":%d}\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$name" "$category" "$detail" "$code" "$elapsed" \
        >> "$FAILURE_LOG"
}

run_agent() {
    local name="$1"
    local script="$2"
    local timeout="${3:-60}"
    local max_retries="${4:-1}"
    local attempt=1
    
    while [ $attempt -le $max_retries ]; do
        if [ $attempt -gt 1 ]; then
            local wait_secs=$(( (attempt - 1) * 30 ))
            log "RETRY $name (attempt $attempt/$max_retries, waiting ${wait_secs}s)"
            sleep "$wait_secs"
        fi
        
        log "START $name"
        local start=$(date +%s)
        
        if timeout "$timeout" python3 "$SCRIPTS/$script" >> "$LOG_FILE" 2>&1; then
            local elapsed=$(( $(date +%s) - start ))
            log "OK    $name (${elapsed}s)"
            return 0
        else
            local code=$?
            local elapsed=$(( $(date +%s) - start ))
            local classification
            classification=$(classify_failure "$code" "$name")
            local category="${classification%%:*}"
            
            if [ $code -eq 124 ]; then
                log "TIMEOUT $name (>${timeout}s) [$classification]"
            else
                log "FAIL  $name (exit $code, ${elapsed}s) [$classification]"
            fi
            
            log_failure "$name" "$classification" "$code" "$elapsed"
            
            # Only retry transient failures
            if [ "$category" = "TRANSIENT" ] && [ $attempt -lt $max_retries ]; then
                attempt=$((attempt + 1))
                continue
            fi
            
            # Config/logic failures: no retry, escalate immediately
            if [ "$category" = "CONFIG" ] || [ "$category" = "LOGIC" ]; then
                log "ESCALATE $name - $classification (not retryable)"
            fi
            
            return $code
        fi
    done
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
            "outreach"  "outreach-agent.py"  30 \
            "system"    "system-agent.py"    30
        ;;
    
    --jobs-only)
        log "=== JOB SOURCES (4x/day) ==="
        # Google Jobs & Bayt: blocked from VPS (403). Disabled.
        # Exa dropped — unreliable (stale URLs, wrong locations, profile pages)
        run_parallel "Job Sources" \
            "linkedin"  "jobs-source-linkedin.py"  300 \
            "indeed"    "jobs-source-indeed.py"    120
        
        log "--- Sync Applied IDs from Notion ---"
        timeout 15 python3 "$SCRIPTS_DIR/sync-applied-from-notion.py" >> "$LOG" 2>&1 || log "WARN: Notion sync failed (non-blocking)"
        
        log "--- Merge (sequential) ---"
        run_agent "merge" "jobs-merge.py" 30
        
        log "--- JD Enrichment (sequential) ---"
        run_agent "enrich" "jobs-enrich-jd.py" 120
        
        log "--- LLM Review (sequential) ---"
        run_agent "review" "jobs-review.py" 180
        
        log "--- Push to Notion Pipeline (sequential) ---"
        run_agent "pipeline-push" "push-submit-to-notion.py" 120
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
            "linkedin"  "jobs-source-linkedin.py"  300 \
            "indeed"    "jobs-source-indeed.py"    120 \
            "comment-radar" "comment-radar-agent.py" 60 \
            "li-post"   "linkedin-post-agent.py"   30
        
        # Phase 2: Merge + Review (sequential, depends on sources)
        log "--- Phase 2: Sync Applied IDs ---"
        timeout 15 python3 "$SCRIPTS_DIR/sync-applied-from-notion.py" >> "$LOG" 2>&1 || log "WARN: Notion sync failed (non-blocking)"
        
        log "--- Phase 2: Merge ---"
        run_agent "merge" "jobs-merge.py" 30
        
        log "--- Phase 2b: JD Enrichment ---"
        run_agent "enrich" "jobs-enrich-jd.py" 120
        
        log "--- Phase 3: LLM Review ---"
        run_agent "review" "jobs-review.py" 180
        
        log "--- Phase 4: Push to Notion Pipeline ---"
        run_agent "pipeline-push" "push-submit-to-notion.py" 120
        
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

# Summary with failure classification
ERRORS=$(grep -c -E "FAIL|TIMEOUT" "$LOG_FILE" 2>/dev/null || true)
ERRORS=${ERRORS:-0}

if [ -f "$FAILURE_LOG" ]; then
    TRANSIENT_COUNT=$(grep -c '"TRANSIENT"' "$FAILURE_LOG" 2>/dev/null || true)
    CONFIG_COUNT=$(grep -c '"CONFIG"' "$FAILURE_LOG" 2>/dev/null || true)
    LOGIC_COUNT=$(grep -c '"LOGIC"' "$FAILURE_LOG" 2>/dev/null || true)
    
    if [ "${CONFIG_COUNT:-0}" -gt 0 ] || [ "${LOGIC_COUNT:-0}" -gt 0 ]; then
        log "🔴 ESCALATE: ${CONFIG_COUNT:-0} config + ${LOGIC_COUNT:-0} logic failures (need human)"
        grep -E '"CONFIG"|"LOGIC"' "$FAILURE_LOG" | while read -r line; do
            log "  -> $line"
        done
    fi
    
    if [ "${TRANSIENT_COUNT:-0}" -gt 0 ]; then
        log "🟡 ${TRANSIENT_COUNT:-0} transient failures (will auto-retry next run)"
    fi
fi

if [ "$ERRORS" -gt 0 ]; then
    log "⚠️  $ERRORS errors in this run"
    exit 1
else
    log "✅ All clear"
    exit 0
fi
