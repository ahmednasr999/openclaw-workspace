#!/bin/bash
cd ~/.openclaw/workspace
git add -A
git diff --cached --quiet && exit 0  # Nothing to commit
git commit -m "Auto-backup $(date -u +%Y-%m-%d_%H:%M)"
git push origin main
