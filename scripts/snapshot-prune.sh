#!/usr/bin/env bash
set -euo pipefail

KEEP=5
ROOT=/root

prune_set() {
  local pattern="$1"
  mapfile -t dirs < <(ls -1dt ${ROOT}/${pattern} 2>/dev/null || true)
  local total=${#dirs[@]}
  if [ "$total" -le "$KEEP" ]; then
    echo "No prune needed for ${pattern}. Count=${total}."
    return
  fi
  echo "Pruning ${pattern}: keep ${KEEP}, remove $((total-KEEP))."
  for d in "${dirs[@]:$KEEP}"; do
    rm -rf "$d"
    echo "Removed: $d"
  done
}

prune_set "openclaw-snapshot-*"
prune_set "mission-control-snapshot-*"

echo "Snapshot prune complete."
