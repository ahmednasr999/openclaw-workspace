#!/bin/bash
cd ~/.openclaw/workspace
git add -A
git diff --cached --quiet && exit 0  # Nothing to commit
git commit -m "Auto-backup $(date -u +%Y-%m-%d_%H:%M)"
# Merge remote changes (not rebase - avoids conflict hell with diverged histories)
git pull --no-rebase origin main 2>&1 || true
git push origin main 2>&1
