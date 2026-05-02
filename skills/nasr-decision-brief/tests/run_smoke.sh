#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/root/.openclaw/workspace/skills/nasr-decision-brief}"
test -f "$ROOT/SKILL.md"
test -f "$ROOT/templates/decision-brief.md"
grep -q "Kill criteria" "$ROOT/SKILL.md"
grep -q "Decision boundary" "$ROOT/SKILL.md"
echo "OK: nasr-decision-brief skill files present"
