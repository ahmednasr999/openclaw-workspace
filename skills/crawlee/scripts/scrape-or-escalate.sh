#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="/root/.openclaw/workspace"
CRAWLEE_SCRIPT="$SCRIPT_DIR/scrape.mjs"
SCRAPLING_SCRIPT="$WORKSPACE/skills/scrapling/scripts/scrape.sh"

AUTO_RUN="${SCRAPLING_AUTO_RUN:-0}"
SUGGEST_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto)
      AUTO_RUN=1
      shift
      ;;
    --suggest-only)
      SUGGEST_ONLY=1
      AUTO_RUN=0
      shift
      ;;
    --help)
      cat <<'EOF'
Usage: scrape-or-escalate.sh [--auto | --suggest-only] <url> [crawlee args...]

Options:
  --auto          Run the suggested Scrapling fallback automatically when escalation triggers
  --suggest-only  Only print the fallback suggestion, never auto-run it
  --help          Show this help

Notes:
- Default behavior is suggest-only unless SCRAPLING_AUTO_RUN=1 is already set.
- Any remaining flags are passed through to Crawlee.
EOF
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      break
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 [--auto | --suggest-only] <url> [crawlee args...]" >&2
  exit 2
fi

URL="$1"
shift || true
ARGS=("$@")

OUTPUT_FILE=""
for ((i=0; i<${#ARGS[@]}; i++)); do
  if [[ "${ARGS[$i]}" == "--output" && $((i+1)) -lt ${#ARGS[@]} ]]; then
    OUTPUT_FILE="${ARGS[$((i+1))]}"
    break
  fi
done

TEMP_OUT=""
if [[ -z "$OUTPUT_FILE" ]]; then
  TEMP_OUT="$(mktemp /tmp/crawlee-escalate-XXXXXX.md)"
  OUTPUT_FILE="$TEMP_OUT"
  ARGS+=(--output "$OUTPUT_FILE")
fi

STDERR_FILE="$(mktemp /tmp/crawlee-escalate-stderr-XXXXXX.log)"
STDOUT_FILE="$(mktemp /tmp/crawlee-escalate-stdout-XXXXXX.log)"
cleanup() {
  rm -f "$STDERR_FILE" "$STDOUT_FILE"
  if [[ -n "$TEMP_OUT" ]]; then
    :
  fi
}
trap cleanup EXIT

set +e
node "$CRAWLEE_SCRIPT" "$URL" "${ARGS[@]}" >"$STDOUT_FILE" 2>"$STDERR_FILE"
STATUS=$?
set -e

cat "$STDOUT_FILE"
cat "$STDERR_FILE" >&2

CONTENT=""
if [[ -f "$OUTPUT_FILE" ]]; then
  CONTENT="$(cat "$OUTPUT_FILE")"
fi

ESCALATE_REASON=""
ESCALATE_MODE="fetch"

if [[ $STATUS -ne 0 ]]; then
  ESCALATE_REASON="crawlee exited non-zero ($STATUS)"
elif grep -qiE 'javascript is not available|enable javascript|supported browser' <<< "$CONTENT"; then
  ESCALATE_REASON="page returned a JS wall instead of the requested content"
  ESCALATE_MODE="fetch"
elif grep -qiE 'sorry, something went wrong|try again|access denied|captcha|temporarily blocked|forbidden' <<< "$CONTENT"; then
  ESCALATE_REASON="page returned an error or anti-bot style response"
  ESCALATE_MODE="stealthy-fetch"
elif [[ ${#CONTENT} -lt 250 ]]; then
  ESCALATE_REASON="output is unusually small and may be a wall or partial page"
  ESCALATE_MODE="fetch"
fi

if [[ -n "$ESCALATE_REASON" ]]; then
  SUGGESTED_OUT="${OUTPUT_FILE%.*}.scrapling.txt"
  echo >&2
  echo "[escalation] Crawlee likely hit a bad-fit target: $ESCALATE_REASON" >&2
  echo "[escalation] Suggested next step:" >&2
  echo "SCRAPLING_WAIT_MS=2500 bash $SCRAPLING_SCRIPT $ESCALATE_MODE '$URL' '$SUGGESTED_OUT'" >&2

  if [[ "$AUTO_RUN" == "1" && "$SUGGEST_ONLY" != "1" ]]; then
    echo "[escalation] --auto enabled, running suggested fallback now" >&2
    SCRAPLING_WAIT_MS="${SCRAPLING_WAIT_MS:-2500}" bash "$SCRAPLING_SCRIPT" "$ESCALATE_MODE" "$URL" "$SUGGESTED_OUT"
  fi
fi
