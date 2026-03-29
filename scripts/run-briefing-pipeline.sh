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
DATA_DIR="/root/.openclaw/workspace/data"
LOG_DIR="/var/log/briefing"
DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/$DATE.log"
LOCK_FILE="/tmp/briefing-pipeline.lock"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Robust lock to prevent overlapping runs
# Checks: PID alive + process is actually this script + lock age < 90 min
LOCK_MAX_AGE=5400  # 90 minutes in seconds
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    LOCK_STALE=1  # assume stale until proven active

    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        # PID exists - verify it's actually our script (not a recycled PID)
        LOCK_CMD=$(ps -p "$LOCK_PID" -o args= 2>/dev/null || echo "")
        if echo "$LOCK_CMD" | grep -q "run-briefing-pipeline"; then
            # Correct process - but check age (stuck runs)
            LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo "0") ))
            if [ "$LOCK_AGE" -lt "$LOCK_MAX_AGE" ]; then
                LOCK_STALE=0
                log "SKIP: Another pipeline run is active (PID $LOCK_PID, age ${LOCK_AGE}s)"
                exit 0
            else
                log "WARN: Lock held by PID $LOCK_PID for ${LOCK_AGE}s (>${LOCK_MAX_AGE}s), killing stale run"
                kill "$LOCK_PID" 2>/dev/null || true
                sleep 2
                kill -9 "$LOCK_PID" 2>/dev/null || true
            fi
        else
            log "WARN: Stale lock - PID $LOCK_PID is not briefing-pipeline (cmd: ${LOCK_CMD:0:80})"
        fi
    else
        log "WARN: Stale lock - PID $LOCK_PID no longer running"
    fi

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
PHASE_STATUS_FILE="$DATA_DIR/pipeline-phase-status.json"

# Initialize phase status tracker
echo '{"generated_at":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","phases":{}}' > "$PHASE_STATUS_FILE"

record_phase() {
    local name="$1"
    local status="$2"
    local elapsed="$3"
    local detail="${4:-}"
    python3 -c "
import json, sys
f = '$PHASE_STATUS_FILE'
try:
    d = json.load(open(f))
except: d = {'phases':{}}
d['phases']['$name'] = {'status':'$status','elapsed_s':$elapsed,'detail':'$detail'}
json.dump(d, open(f,'w'), indent=2)
" 2>/dev/null || true
}

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
    local output_file="${5:-}"
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
            record_phase "$name" "OK" "$elapsed"
            # Track heartbeat on success
            if [ -n "$output_file" ]; then
                python3 "$SCRIPTS/heartbeat-tracker.py" --agent "$name" --output "$output_file" >> "$LOG_FILE" 2>&1 || true
            else
                python3 "$SCRIPTS/heartbeat-tracker.py" --agent "$name" >> "$LOG_FILE" 2>&1 || true
            fi
            return 0
        else
            local code=$?
            local elapsed=$(( $(date +%s) - start ))
            local classification
            classification=$(classify_failure "$code" "$name")
            local category="${classification%%:*}"
            
            if [ $code -eq 124 ]; then
                log "TIMEOUT $name (>${timeout}s) [$classification]"
                record_phase "$name" "TIMEOUT" "$elapsed" "$classification"
            else
                log "FAIL  $name (exit $code, ${elapsed}s) [$classification]"
                record_phase "$name" "FAIL" "$elapsed" "$classification"
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
    local scripts=()
    local timeouts=()
    
    log "--- $label (parallel) ---"
    
    while [ $# -gt 0 ]; do
        local name="$1"
        local script="$2"
        local timeout="${3:-60}"
        shift 3
        pids+=("$name")
        names+=("$name")
        scripts+=("$script")
        timeouts+=("$timeout")
    done
    
    # Launch all in background with retry on failure
    local bg_pids=()
    for i in "${!names[@]}"; do
        (
            local attempt=1
            local max_attempts=2
            while [ $attempt -le $max_attempts ]; do
                if [ $attempt -gt 1 ]; then
                    echo "[$(date '+%H:%M:%S')] RETRY ${names[$i]} (attempt $attempt)" >> "$LOG_FILE"
                    sleep 5
                fi
                timeout "${timeouts[$i]}" python3 "$SCRIPTS/${scripts[$i]}" >> "$LOG_FILE" 2>&1
                local code=$?
                if [ $code -eq 0 ]; then
                    python3 "$SCRIPTS/heartbeat-tracker.py" --agent "${names[$i]}" >> "$LOG_FILE" 2>&1 || true
                    exit 0
                fi
                ((attempt++))
            done
            # Both attempts failed — write failure marker for briefing
            echo "{\"agent\":\"${names[$i]}\",\"status\":\"FAILED\",\"ts\":\"$(date -Iseconds)\"}" >> "$DATA_DIR/source-failures.jsonl"
            exit 1
        ) &
        bg_pids+=($!)
    done
    
    local failures=0
    for i in "${!bg_pids[@]}"; do
        if ! wait "${bg_pids[$i]}" 2>/dev/null; then
            log "FAIL: ${names[$i]} (after retry)"
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
            "email"     "email-agent.py"    180 \
            "outreach"  "outreach-agent.py"  180 \
            "system"    "system-agent.py"    30
        ;;
    
    --jobs-only)
        log "=== JOB SOURCES (4x/day) ==="
        # Exa dropped — unreliable (stale URLs, wrong locations, profile pages)
        run_parallel "Job Sources" \
            "linkedin"  "jobs-source-linkedin.py"  480 \
            "indeed"    "jobs-source-indeed.py"    120 \
            "google"    "jobs-source-google.py"    120
        
        log "--- Sync Applied IDs from Notion ---"
        timeout 15 python3 "$SCRIPTS/sync-applied-from-notion.py" >> "$LOG_FILE" 2>&1 || log "WARN: Notion sync failed (non-blocking)"
        
        log "--- Merge (sequential) ---"
        run_agent "merge" "jobs-merge.py" 30 2
        
        log "--- JD Enrichment (sequential) ---"
        run_agent "enrich" "jobs-enrich-jd.py" 300 2
        
        log "--- LLM Review (sequential) ---"
        run_agent "review" "jobs-review.py" 3000 2
        
        log "--- Push to Notion Pipeline (sequential) ---"
        run_agent "pipeline-push" "push-submit-to-notion.py" 120 2
        
        log "--- Push to NocoDB + Telegram Alerts ---"
        run_agent "nocodb-push" "push-to-nocodb.py" 120 2
        ;;
    
    --all)
        log "========================================="
        log "  FULL BRIEFING PIPELINE"
        log "========================================="
        
        # Clear previous failure markers
        rm -f "$DATA_DIR/source-failures.jsonl"
        
        # Phase 0: Heartbeat check + cleanup
        log "--- Phase 0: Heartbeat Check ---"
        timeout 30 python3 "$SCRIPTS/heartbeat-checker.py" >> "$LOG_FILE" 2>&1 || true
        # Cleanup old calendar cache files (keep last 3 days)
        find /tmp -name "calendar-events-*.json" -mtime +3 -delete 2>/dev/null || true
        
        # Phase 1: Data agents + job sources in parallel
        run_parallel "Phase 1: Data + Sources" \
            "pipeline"  "pipeline-agent.py"       30 \
            "email"     "email-agent.py"          180 \
            "outreach"  "outreach-agent.py"       180 \
            "system"    "system-agent.py"           30 \
            "linkedin"  "jobs-source-linkedin.py"  480 \
            "indeed"    "jobs-source-indeed.py"    120 \
            "google"    "jobs-source-google.py"    120 \
            "comment-radar" "comment-radar-agent.py" 180 \
            "li-post"   "linkedin-post-agent.py"   30 \
            || log "⚠️ Phase 1 had failures (continuing to Phase 2+)"
        
        # Alert on source failures via Telegram
        if [ -f "$DATA_DIR/source-failures.jsonl" ]; then
            FAILED_SOURCES=$(cat "$DATA_DIR/source-failures.jsonl" | python3 -c "import sys,json; print(', '.join(json.loads(l).get('agent','?') for l in sys.stdin if l.strip()))" 2>/dev/null || echo "unknown")
            log "🔴 Source failures detected: $FAILED_SOURCES"
            openclaw message send --channel telegram --to "-1003882622947:10" --message "🔴 Morning Briefing Alert: Job sources FAILED after retry: $FAILED_SOURCES. Check pipeline logs." >> "$LOG_FILE" 2>&1 || true
        fi
        
        # Phase 2: Merge + Review (sequential, depends on sources)
        PHASE2_FAILURES=""
        
        log "--- Phase 2: Sync Applied IDs ---"
        timeout 15 python3 "$SCRIPTS/sync-applied-from-notion.py" >> "$LOG_FILE" 2>&1 || log "WARN: Notion sync failed (non-blocking)"
        
        log "--- Phase 2: Merge ---"
        run_agent "merge" "jobs-merge.py" 30 2 || PHASE2_FAILURES="${PHASE2_FAILURES}merge "
        
        log "--- Phase 2b: JD Enrichment ---"
        run_agent "enrich" "jobs-enrich-jd.py" 300 2 || PHASE2_FAILURES="${PHASE2_FAILURES}enrich "
        
        log "--- Phase 3: LLM Review ---"
        run_agent "review" "jobs-review.py" 3000 2 || PHASE2_FAILURES="${PHASE2_FAILURES}review "
        
        log "--- Phase 4: Push to Notion Pipeline ---"
        run_agent "pipeline-push" "push-submit-to-notion.py" 120 2 || PHASE2_FAILURES="${PHASE2_FAILURES}pipeline-push "

        log "--- Phase 4a: Push to NocoDB + Telegram Alerts ---"
        run_agent "nocodb-push" "push-to-nocodb.py" 120 2 || log "⚠️ Phase 4a (NocoDB push) failed — non-critical"

        log "--- Phase 4b: CV Autogen (Opus, budget-capped) ---"
        run_agent "cv-autogen" "jobs-cv-autogen.py" 7200 1 \
            || log "⚠️ Phase 4b (CV autogen) failed — briefing will show no CV links"

        # Alert on Phase 2+ failures
        if [ -n "$PHASE2_FAILURES" ]; then
            log "🔴 Phase 2+ failures: $PHASE2_FAILURES"
            openclaw message send --channel telegram --to "-1003882622947:10" --message "🔴 Morning Briefing Alert: Phase 2 FAILED after retry: ${PHASE2_FAILURES}. Jobs may be missing from briefing." >> "$LOG_FILE" 2>&1 || true
        fi

        # Phase 5: Newsletter REMOVED (2026-03-22) — pam-telegram.py reads fresh data directly
        
        log "--- Phase 6: Outreach Follow-up Tracker ---"
        run_agent "outreach-tracker" "outreach-followup-tracker.py" 30 \
            || log "⚠️ Phase 6 (Outreach tracker) failed — non-critical"

        log "--- Phase 7: Generate Notion Briefing ---"
        run_agent "briefing" "briefing-agent.py" 180 \
            || log "⚠️ Phase 7 (Notion briefing) failed — continuing"

        log "--- Phase 8: Telegram Summary ---"
        run_agent "pam-telegram" "pam-telegram.py" 60 \
            || log "⚠️ Phase 8 (Telegram summary) failed — continuing"

        log "--- Phase 9: Briefing Doctor (audit) ---"
        run_agent "briefing-doctor" "briefing-doctor.py" 30 \
            || log "⚠️ Phase 9 (Doctor) failed — non-critical"

        log "--- Phase 10: Completion Check ---"
        python3 "$SCRIPTS/briefing-completion-check.py" --alert >> "$LOG_FILE" 2>&1 || true

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
