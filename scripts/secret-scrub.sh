#!/bin/bash
# secret-scrub.sh — Remove committed secrets from git history using git filter-branch
# Run this ONCE to scrub all secrets from history, then force-push
# WARNING: Rewrites git history. Coordinate with team first.

set -euo pipefail
WORKSPACE="/root/.openclaw/workspace"
cd "$WORKSPACE"

echo "⚠️  WARNING: This will rewrite git history."
echo "   Make sure no one else is working on this repo simultaneously."
echo ""
echo "Secrets to scrub:"
echo "  - notion API token (ntn_...) in config/notion.json"
echo ""

read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Backing up original refs..."
git branch backup-pre-scrub

echo "Rewriting config/notion.json in all commits..."
# Replace notion token with placeholder in all commits
git filter-branch -f --tree-filter '
    if [ -f config/notion.json ]; then
        python3 -c "
import json, sys
try:
    with open(\"config/notion.json\") as f:
        d = json.load(f)
    if \"token\" in d:
        d[\"token\"] = \"REMOVED_SCRUBBED\"
    with open(\"config/notion.json\", \"w\") as f:
        json.dump(d, f, indent=2)
except: pass
" 2>/dev/null || true
    fi
' HEAD

echo ""
echo "✅ History rewritten. Notion token replaced with REMOVED_SCRUBBED."
echo ""
echo "Next steps:"
echo "  1. Verify: git log --oneline (should show REMOVED, not real token)"
echo "  2. Force push: git push origin master --force"
echo "  3. Notify GitHub that secret was scrubbed (github.com/$REPO/security/secret-scanning)"
echo "  4. Add real token back to config/notion.json"
echo ""
echo "To undo: git checkout backup-pre-scrub"
