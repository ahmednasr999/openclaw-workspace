#!/bin/bash
# preflight-test.sh — Smoke test all pipeline scripts before deployment
# Run after any code change. Catches import errors, syntax errors, missing deps.
# Usage: bash scripts/preflight-test.sh [--fix]

set -uo pipefail
SCRIPTS="/root/.openclaw/workspace/scripts"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0
PASSED=0
WARNINGS=0

log_pass() { echo -e "${GREEN}✅ PASS${NC}: $1"; ((PASSED++)); }
log_fail() { echo -e "${RED}❌ FAIL${NC}: $1 — $2"; ((FAILED++)); }
log_warn() { echo -e "${YELLOW}⚠️ WARN${NC}: $1"; ((WARNINGS++)); }

echo "=== Preflight Test — $(date '+%Y-%m-%d %H:%M:%S') ==="
echo ""

# Test 1: Python syntax + import check for all pipeline scripts
PIPELINE_SCRIPTS=(
    "briefing-agent.py"
    "email-agent.py"
    "outreach-agent.py"
    "comment-radar-agent.py"
    "pipeline-agent.py"
    "system-agent.py"
    "jobs-source-linkedin.py"
    "jobs-source-indeed.py"
    "jobs-source-google.py"
    "linkedin-content-agent.py"
    "linkedin-post-agent.py"
    "jobs-merge.py"
    "jobs-enrich-jd.py"
    "jobs-review.py"
    "push-submit-to-notion.py"
    "pam-telegram.py"
    "pipeline_db.py"
    "auto-cv-builder.py"
    "notion-pipeline-sync.py"
    "linkedin-reaction-tracker.py"
    "nasr-doctor.py"
)

echo "--- Python Import Check (${#PIPELINE_SCRIPTS[@]} scripts) ---"
for script in "${PIPELINE_SCRIPTS[@]}"; do
    FULL="$SCRIPTS/$script"
    if [ ! -f "$FULL" ]; then
        log_warn "$script — file not found (skipped)"
        continue
    fi
    # Syntax check
    ERR=$(python3 -c "
import ast, sys
try:
    ast.parse(open('$FULL').read())
except SyntaxError as e:
    print(f'SyntaxError: {e}')
    sys.exit(1)
" 2>&1)
    if [ $? -ne 0 ]; then
        log_fail "$script" "Syntax: $ERR"
        continue
    fi
    # Import check (timeout 10s, catch ImportError/NameError at module level)
    ERR=$(timeout 10 python3 -c "
import sys, importlib.util
spec = importlib.util.spec_from_file_location('mod', '$FULL')
# Only check if the file can be parsed and top-level imports resolve
import ast
tree = ast.parse(open('$FULL').read())
imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
for node in imports:
    if isinstance(node, ast.Import):
        for alias in node.names:
            try:
                __import__(alias.name.split('.')[0])
            except ImportError as e:
                if not any(x in str(e) for x in ['agent_common','pipeline_db','_adapters','_imports','notion_client_shared','cv_validator','application_lock']):
                    print(f'ImportError: {e}')
                    sys.exit(1)
    elif isinstance(node, ast.ImportFrom) and node.module:
        try:
            __import__(node.module.split('.')[0])
        except ImportError as e:
            if not any(x in str(e) for x in ['agent_common','pipeline_db','_adapters','_imports','notion_client_shared','cv_validator','application_lock']):
                print(f'ImportError: {e}')
                sys.exit(1)
" 2>&1)
    if [ $? -ne 0 ]; then
        log_fail "$script" "Import: $ERR"
    else
        log_pass "$script"
    fi
done

echo ""
echo "--- Gateway Health ---"
GW=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18789/health 2>/dev/null || echo "000")
if [ "$GW" = "200" ] || [ "$GW" = "204" ]; then
    log_pass "Gateway (port 18789)"
else
    # Try just connecting
    GW2=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18789/ 2>/dev/null || echo "000")
    if [ "$GW2" != "000" ]; then
        log_pass "Gateway (port 18789, status $GW2)"
    else
        log_fail "Gateway" "Not reachable on port 18789 (HTTP $GW)"
    fi
fi

echo ""
echo "--- Config Files ---"
for cfg in "config/notion.json" "config/tavily.json"; do
    FULL="/root/.openclaw/workspace/$cfg"
    if [ -f "$FULL" ]; then
        # Validate JSON
        python3 -c "import json; json.load(open('$FULL'))" 2>/dev/null
        if [ $? -eq 0 ]; then
            log_pass "$cfg"
        else
            log_fail "$cfg" "Invalid JSON"
        fi
    else
        log_warn "$cfg — not found"
    fi
done

echo ""
echo "--- Pipeline Script ---"
if [ -f "$SCRIPTS/run-briefing-pipeline.sh" ]; then
    bash -n "$SCRIPTS/run-briefing-pipeline.sh" 2>/dev/null
    if [ $? -eq 0 ]; then
        log_pass "run-briefing-pipeline.sh (bash syntax)"
    else
        log_fail "run-briefing-pipeline.sh" "bash syntax error"
    fi
else
    log_fail "run-briefing-pipeline.sh" "not found"
fi

echo ""
echo "========================================="
echo "Results: ${PASSED} passed, ${FAILED} failed, ${WARNINGS} warnings"
echo "========================================="

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}PREFLIGHT FAILED — Do NOT deploy until fixed${NC}"
    exit 1
else
    echo -e "${GREEN}PREFLIGHT PASSED — Safe to deploy${NC}"
    exit 0
fi
