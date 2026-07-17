#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/claude-cli-smoke-test.sh [--auth-only] [--all-models] [--model MODEL --expect TEXT]

Checks Claude CLI auth before any prompt is sent. By default it verifies auth and
runs one exact-output Sonnet smoke test. Use --all-models to also check Opus.
USAGE
}

redact() {
  sed -E \
    -e 's/sk-ant-[A-Za-z0-9_-]+/[REDACTED_KEY]/g' \
    -e 's/(Bearer )[A-Za-z0-9._-]+/\1[REDACTED_TOKEN]/g' \
    -e 's/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/[REDACTED_EMAIL]/g'
}

AUTH_ONLY=0
ALL_MODELS=0
CUSTOM_MODEL=""
CUSTOM_EXPECT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auth-only)
      AUTH_ONLY=1
      shift
      ;;
    --all-models)
      ALL_MODELS=1
      shift
      ;;
    --model)
      CUSTOM_MODEL="${2:-}"
      shift 2
      ;;
    --expect)
      CUSTOM_EXPECT="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if ! command -v claude >/dev/null 2>&1; then
  echo "Claude CLI not found on PATH." >&2
  exit 127
fi

status_output=""
status_code=0
status_output="$(claude auth status 2>&1)" || status_code=$?

if [[ "$status_code" -ne 0 ]]; then
  echo "Claude CLI auth preflight failed." >&2
  printf '%s\n' "$status_output" | redact >&2
  echo "Next: run claude auth login outside the agent session, then rerun scripts/claude-cli-smoke-test.sh --auth-only" >&2
  exit 2
fi

printf '%s\n' "$status_output" | redact

if [[ "$AUTH_ONLY" -eq 1 ]]; then
  echo "Claude CLI auth preflight passed."
  exit 0
fi

run_model_check() {
  local model="$1"
  local expected="$2"
  local prompt="Reply: ${expected}"
  local output=""
  local code=0

  output="$(claude -p --model "$model" "$prompt" 2>&1)" || code=$?
  printf '%s\n' "$output" | redact
  if [[ "$code" -ne 0 ]]; then
    echo "Claude smoke test failed for model: ${model}" >&2
    exit 3
  fi
  case "$output" in
    *"$expected"*) echo "Claude smoke test passed for model: ${model}" ;;
    *)
      echo "Claude smoke test did not return the expected confirmation for model: ${model}" >&2
      exit 4
      ;;
  esac
}

if [[ -n "$CUSTOM_MODEL" || -n "$CUSTOM_EXPECT" ]]; then
  if [[ -z "$CUSTOM_MODEL" || -z "$CUSTOM_EXPECT" ]]; then
    echo "--model and --expect must be supplied together." >&2
    exit 64
  fi
  run_model_check "$CUSTOM_MODEL" "$CUSTOM_EXPECT"
  exit 0
fi

run_model_check sonnet "Sonnet 4.6 confirmed"

if [[ "$ALL_MODELS" -eq 1 ]]; then
  run_model_check opus "Opus 4.6 confirmed"
fi
