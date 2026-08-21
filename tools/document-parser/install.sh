#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
runtime_dir="$workspace_dir/tools/document-parser-venv"
lock_file="$workspace_dir/tools/document-parser/requirements.lock"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to install the document parser runtime" >&2
  exit 1
fi

if [[ ! -x "$runtime_dir/bin/python" ]]; then
  uv venv --python 3.13 "$runtime_dir"
fi

uv pip sync --python "$runtime_dir/bin/python" "$lock_file"
"$runtime_dir/bin/python" -c \
  'import importlib.metadata as m; print("AnyDoc", m.version("firecrawl-anydoc"), "MarkItDown", m.version("markitdown"))'
