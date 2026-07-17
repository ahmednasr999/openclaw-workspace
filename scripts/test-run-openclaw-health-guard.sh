#!/usr/bin/env bash
set -euo pipefail

ROOT=$(mktemp -d)
trap 'rm -rf "$ROOT"' EXIT

make_dashboard() {
  local path=$1
  local code=$2
  local label=$3
  printf 'import sys\nprint("%s")\nsys.exit(%s)\n' "$label" "$code" >"$path"
}

make_dashboard "$ROOT/ok.py" 0 HEALTH_OK
make_dashboard "$ROOT/critical.py" 2 HEALTH_CRITICAL
make_dashboard "$ROOT/error.py" 7 HEALTH_BROKEN

OPENCLAW_HEALTH_DASHBOARD="$ROOT/ok.py" scripts/run-openclaw-health-guard.sh >"$ROOT/ok.out"
grep -q HEALTH_OK "$ROOT/ok.out"

OPENCLAW_HEALTH_DASHBOARD="$ROOT/critical.py" scripts/run-openclaw-health-guard.sh >"$ROOT/critical.out"
grep -q HEALTH_CRITICAL "$ROOT/critical.out"
grep -q 'HEALTH_ALERT_EXIT=2' "$ROOT/critical.out"

set +e
OPENCLAW_HEALTH_DASHBOARD="$ROOT/error.py" scripts/run-openclaw-health-guard.sh >"$ROOT/error.out" 2>&1
rc=$?
set -e
test "$rc" -eq 7
grep -q 'HEALTH_EXECUTION_ERROR=7' "$ROOT/error.out"

echo 'health guard wrapper tests passed'
