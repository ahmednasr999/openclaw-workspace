#!/usr/bin/env bash
set -euo pipefail

VERSION="0.36.0"
WORKSPACE="/root/.openclaw/workspace"
CACHE_DIR="${CRABBOX_CACHE_DIR:-/root/.cache/openclaw/crabbox/${VERSION}}"
CRABBOX_BIN="${CRABBOX_BIN:-${CACHE_DIR}/crabbox}"
DEFAULT_IMAGE="${CRABBOX_LOCAL_IMAGE:-debian:bookworm-slim}"
OUT_ROOT="${CRABBOX_PROOF_DIR:-${WORKSPACE}/reports/crabbox-local-proof}"
RELEASE_BASE="https://github.com/openclaw/crabbox/releases/download/v${VERSION}"
ARCHIVE="crabbox_${VERSION}_linux_amd64.tar.gz"

usage() {
  cat <<USAGE
Usage: scripts/crabbox-local-proof.sh [options] -- <command> [args...]

Runs a Git worktree command in a disposable Crabbox local-container lease and saves
proof artifacts locally. This is for CTO verification and repo experiments, not
for hostile code or secret-heavy worktrees.

Options:
  --repo PATH                 Git repository/worktree to sync. Default: current dir.
  --label LABEL               Human label for output directory and lease slug.
  --image IMAGE               local-container image. Default: ${DEFAULT_IMAGE}
  --timeout-seconds N         Remote command timeout. Default: 900.
  --output-root PATH          Proof output root. Default: ${OUT_ROOT}
  --allow-workspace-sync      Allow syncing /root/.openclaw/workspace.
  --keep-image                Do not remove the pulled container image afterward.
  -h, --help                  Show this help.

Examples:
  scripts/crabbox-local-proof.sh --repo /tmp/demo --label smoke -- echo OK
  scripts/crabbox-local-proof.sh --repo /path/to/repo --label tests -- pnpm test
USAGE
}

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/--+/-/g' | cut -c1-48
}

ensure_crabbox() {
  if [[ -x "$CRABBOX_BIN" ]] && [[ "$($CRABBOX_BIN --version 2>/dev/null || true)" == "$VERSION" ]]; then
    return 0
  fi

  mkdir -p "$CACHE_DIR"
  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN
  (
    cd "$tmp"
    curl -fsSLO "${RELEASE_BASE}/checksums.txt"
    curl -fsSLO "${RELEASE_BASE}/${ARCHIVE}"
    grep " ${ARCHIVE}$" checksums.txt | sha256sum -c - >/dev/null
    tar -xzf "$ARCHIVE" crabbox
    install -m 0755 crabbox "$CRABBOX_BIN"
  )
}

REPO="$PWD"
LABEL="crabbox-proof"
IMAGE="$DEFAULT_IMAGE"
TIMEOUT_SECONDS=900
ALLOW_WORKSPACE_SYNC=0
KEEP_IMAGE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --label)
      LABEL="${2:-}"
      shift 2
      ;;
    --image)
      IMAGE="${2:-}"
      shift 2
      ;;
    --timeout-seconds)
      TIMEOUT_SECONDS="${2:-}"
      shift 2
      ;;
    --output-root)
      OUT_ROOT="${2:-}"
      shift 2
      ;;
    --allow-workspace-sync)
      ALLOW_WORKSPACE_SYNC=1
      shift
      ;;
    --keep-image)
      KEEP_IMAGE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if [[ $# -lt 1 ]]; then
  echo "Missing command after --" >&2
  usage >&2
  exit 64
fi

case "$TIMEOUT_SECONDS" in
  ''|*[!0-9]*) echo "--timeout-seconds must be a positive integer" >&2; exit 64 ;;
esac
if [[ "$TIMEOUT_SECONDS" -le 0 ]]; then
  echo "--timeout-seconds must be greater than zero" >&2
  exit 64
fi

if ! command -v curl >/dev/null 2>&1 || ! command -v sha256sum >/dev/null 2>&1 || ! command -v tar >/dev/null 2>&1; then
  echo "Missing required local tools: curl, sha256sum, and tar are required." >&2
  exit 127
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for provider=local-container." >&2
  exit 127
fi

REPO_REAL="$(realpath "$REPO")"
WORKSPACE_REAL="$(realpath "$WORKSPACE")"
if [[ ! -d "$REPO_REAL" ]]; then
  echo "Repo path does not exist: $REPO_REAL" >&2
  exit 66
fi
if ! git -C "$REPO_REAL" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Repo path is not a Git worktree: $REPO_REAL" >&2
  echo "Crabbox sync is repo-oriented; initialize Git or pass a real checkout." >&2
  exit 66
fi
if [[ "$REPO_REAL" == "$WORKSPACE_REAL" && "$ALLOW_WORKSPACE_SYNC" -ne 1 ]]; then
  cat >&2 <<'MSG'
Refusing to sync the main OpenClaw workspace by default.
Use --allow-workspace-sync only after checking the worktree for secrets and large artifacts.
MSG
  exit 65
fi

ensure_crabbox

SAFE_LABEL="$(slugify "$LABEL")"
if [[ -z "$SAFE_LABEL" ]]; then
  SAFE_LABEL="crabbox-proof"
fi
STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"
RUN_ID="${SAFE_LABEL}-${STAMP}"
LEASE_SLUG="nasr-${SAFE_LABEL}-${STAMP}"
OUT_DIR="${OUT_ROOT}/${RUN_ID}"
mkdir -p "$OUT_DIR"

printf '%s\n' "# Crabbox Local Proof" > "$OUT_DIR/summary.md"
printf '\n- Started: %s\n- Repo: %s\n- Provider: local-container\n- Image: %s\n- Lease label: %s\n- Timeout seconds: %s\n- Command: ' "$(date -Is)" "$REPO_REAL" "$IMAGE" "$LEASE_SLUG" "$TIMEOUT_SECONDS" >> "$OUT_DIR/summary.md"
printf '`' >> "$OUT_DIR/summary.md"
printf '%q ' "$@" >> "$OUT_DIR/summary.md"
printf '`\n' >> "$OUT_DIR/summary.md"

RC=0
(
  cd "$REPO_REAL"
  "$CRABBOX_BIN" run \
    --provider local-container \
    --target linux \
    --slug "$LEASE_SLUG" \
    --local-container-image "$IMAGE" \
    --capture-stdout "$OUT_DIR/stdout.txt" \
    --capture-stderr "$OUT_DIR/stderr.txt" \
    --emit-proof "$OUT_DIR/proof.md" \
    -- timeout "${TIMEOUT_SECONDS}s" "$@"
) 2>&1 | tee "$OUT_DIR/crabbox.log" || RC=${PIPESTATUS[0]}

FINISHED="$(date -Is)"
{
  printf '\n- Finished: %s\n- Exit code: %s\n' "$FINISHED" "$RC"
  if [[ -f "$OUT_DIR/proof.md" ]]; then
    printf -- '- Proof: `%s`\n' "$OUT_DIR/proof.md"
  fi
  printf -- '- Log: `%s`\n- Stdout: `%s`\n- Stderr: `%s`\n' "$OUT_DIR/crabbox.log" "$OUT_DIR/stdout.txt" "$OUT_DIR/stderr.txt"
  if [[ -s "$OUT_DIR/stdout.txt" ]]; then
    printf '\n## Stdout Tail\n\n```text\n'
    tail -80 "$OUT_DIR/stdout.txt"
    printf '\n```\n'
  fi
  if [[ -s "$OUT_DIR/stderr.txt" ]]; then
    printf '\n## Stderr Tail\n\n```text\n'
    tail -80 "$OUT_DIR/stderr.txt"
    printf '\n```\n'
  fi
} >> "$OUT_DIR/summary.md"

if [[ "$KEEP_IMAGE" -ne 1 ]]; then
  docker image rm "$IMAGE" >/dev/null 2>&1 || true
fi

if docker ps -a --format '{{.Names}} {{.Image}}' | grep -F "$LEASE_SLUG" >/dev/null 2>&1; then
  echo "Warning: a matching Crabbox container may remain for ${LEASE_SLUG}; inspect docker ps -a." >&2
fi

printf 'crabbox-local-proof: rc=%s summary=%s\n' "$RC" "$OUT_DIR/summary.md"
exit "$RC"
