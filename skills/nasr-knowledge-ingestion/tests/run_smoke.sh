#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/root/.openclaw/workspace/labs/obsidian-aios-pilot/vault}"
python3 /root/.openclaw/workspace/skills/nasr-knowledge-ingestion/scripts/validate_vault.py "$ROOT"
