#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${OPENCLAW_ROOT_DIR:-$HOME/.openclaw}"
AGENT_FILTER=""
THRESHOLD_TOKENS=1200
OUTPUT_JSON=0

usage() {
  cat <<'USAGE'
Usage: scripts/nasr-context-audit.sh [--agent main|cto|hr|cmo|jobzoom] [--threshold-tokens N] [--json]

Audits bootstrap-sensitive AGENTS.md, MEMORY.md, and SOUL*.md files under the main
workspace and workspace-* roots. This is read-only and intentionally ignores vendor,
node_modules, and archived paths.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT_FILTER="${2:-}"
      shift 2
      ;;
    --threshold-tokens)
      THRESHOLD_TOKENS="${2:-1200}"
      shift 2
      ;;
    --json)
      OUTPUT_JSON=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$THRESHOLD_TOKENS" in
  ''|*[!0-9]*)
    printf 'Invalid --threshold-tokens value: %s\n' "$THRESHOLD_TOKENS" >&2
    exit 1
    ;;
esac

python3 - "$ROOT_DIR" "$AGENT_FILTER" "$THRESHOLD_TOKENS" "$OUTPUT_JSON" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def root_candidates(root: Path):
    roots = []
    main = root / "workspace"
    if main.is_dir():
        roots.append(("main", main))
    for child in sorted(root.iterdir()):
        if child.is_dir() and child.name.startswith("workspace-"):
            label = child.name.replace("workspace-", "", 1)
            roots.append((label, child))
    return roots


def iso_mtime(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def class_for(path: Path, workspace_root: Path):
    rel = path.relative_to(workspace_root)
    if rel.parent == Path('.'):
        return "root-bootstrap"
    if rel.parts[:1] in {("skills",), ("agents",)}:
        return "nested-persona"
    return "other"


root = Path(sys.argv[1]).expanduser()
agent_filter = sys.argv[2]
threshold_tokens = int(sys.argv[3])
output_json = sys.argv[4] == "1"

results = []
for label, workspace_root in root_candidates(root):
    if agent_filter and agent_filter != label:
        continue

    for path in workspace_root.rglob("*.md"):
        if any(part in {"node_modules", ".git", ".venv", "archive", "_archived", "tmp"} for part in path.parts):
            continue
        if not (
            path.name == "AGENTS.md"
            or path.name == "MEMORY.md"
            or (path.name.startswith("SOUL") and path.suffix == ".md")
        ):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            stat = path.stat()
        except OSError:
            continue

        chars = len(content)
        token_estimate = chars // 4
        if token_estimate < threshold_tokens:
            continue

        results.append(
            {
                "workspace": label,
                "path": str(path),
                "class": class_for(path, workspace_root),
                "chars": chars,
                "lines": content.count("\n") + 1,
                "token_estimate": token_estimate,
                "mtime": iso_mtime(stat.st_mtime),
            }
        )

class_rank = {"root-bootstrap": 0, "nested-persona": 1, "other": 2}
results.sort(key=lambda item: (class_rank.get(item["class"], 9), -item["token_estimate"], item["path"]))
payload = {"threshold_tokens": threshold_tokens, "results": results}

if output_json:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(0)

if not results:
    target = f" for {agent_filter}" if agent_filter else ""
    print(f"No context files at or above {threshold_tokens} tokens found{target}.")
    raise SystemExit(0)

print(f"Context files at or above {threshold_tokens} tokens:")
for item in results:
    print(
        f"- [{item['workspace']}] {item['class']} | {item['token_estimate']} tok | "
        f"{item['lines']} lines | {item['path']}"
    )
PY
