#!/usr/bin/env bash
set -euo pipefail

# conservative cleanup only
if command -v npm >/dev/null 2>&1; then
  npm cache clean --force >/dev/null 2>&1 || true
fi

find /tmp -mindepth 1 -maxdepth 1 -type d -mtime +7 -print -exec rm -rf {} + 2>/dev/null || true

# trim large log archives older than 30 days
find /var/log -type f -name "*.gz" -mtime +30 -size +20M -print -delete 2>/dev/null || true

echo "Monthly cache cleanup complete."
