#!/usr/bin/env bash
set -euo pipefail

PIPELINE="/root/.openclaw/workspace/jobs-bank/pipeline.md"
HANDOFF_DIR="/root/.openclaw/workspace/jobs-bank/handoff"

if [[ ! -f "$PIPELINE" || ! -d "$HANDOFF_DIR" ]]; then
  echo "ERROR: required paths missing"
  exit 1
fi

issues=0

for f in "$HANDOFF_DIR"/*.json; do
  [[ -e "$f" ]] || continue

  company=$(grep -oP '"company"\s*:\s*"\K[^"]+' "$f" | head -1 || true)
  role=$(grep -oP '"role"\s*:\s*"\K[^"]+' "$f" | head -1 || true)

  [[ -n "$company" && -n "$role" ]] || continue

  in_applied=$(grep -F "| $company | $role |" "$PIPELINE" | grep -F "| ✅ Applied |" || true)
  in_closed=$(grep -F "| $company | $role |" "$PIPELINE" | grep -F "| ⚪ Closed |" || true)

  if [[ -n "$in_applied" || -n "$in_closed" ]]; then
    base="${f%.json}"
    if [[ -f "$base.trigger" ]]; then
      echo "STALE_TRIGGER: $(basename "$base.trigger")"
      issues=$((issues+1))
    fi
  fi

done

if [[ $issues -eq 0 ]]; then
  echo "OK: no stale handoff triggers"
else
  echo "FOUND: $issues stale handoff trigger(s)"
  exit 2
fi
