#!/bin/bash
cd ~/.openclaw/workspace
git add -A
git diff --cached --quiet && exit 0  # Nothing to commit
git commit -m "Auto-backup $(date -u +%Y-%m-%d_%H:%M)"
# Pull-rebase first to handle remote changes, then push
git pull --rebase origin main 2>&1 || true
git push origin main 2>&1
