#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
URL="${2:-}"
OUT="${3:-}"
SELECTOR="${4:-}"
WAIT_MS="${SCRAPLING_WAIT_MS:-0}"
TIMEOUT_MS="${SCRAPLING_TIMEOUT_MS:-30000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRAPLING_BIN="${SCRAPLING_BIN:-$SKILL_DIR/.venv/bin/scrapling}"

if [[ ! -x "$SCRAPLING_BIN" ]]; then
  SCRAPLING_BIN="$(command -v scrapling)"
fi

if [[ -z "$MODE" || -z "$URL" || -z "$OUT" ]]; then
  echo "Usage: $0 <get|fetch|stealthy-fetch> <url> <output-file> [css-selector]" >&2
  exit 2
fi

case "$MODE" in
  get)
    cmd=("$SCRAPLING_BIN" extract get "$URL" "$OUT" --timeout 30)
    ;;
  fetch)
    cmd=("$SCRAPLING_BIN" extract fetch "$URL" "$OUT" --headless --timeout "$TIMEOUT_MS")
    if [[ "$WAIT_MS" != "0" ]]; then
      cmd+=(--wait "$WAIT_MS")
    fi
    ;;
  stealthy-fetch)
    cmd=("$SCRAPLING_BIN" extract stealthy-fetch "$URL" "$OUT" --headless --timeout "$TIMEOUT_MS")
    if [[ "$WAIT_MS" != "0" ]]; then
      cmd+=(--wait "$WAIT_MS")
    fi
    ;;
  *)
    echo "Invalid mode: $MODE" >&2
    exit 2
    ;;
esac

if [[ -n "$SELECTOR" ]]; then
  cmd+=(--css-selector "$SELECTOR")
fi

mkdir -p "$(dirname "$OUT")"
"${cmd[@]}"
printf 'mode=%s\nout=%s\n' "$MODE" "$OUT"
