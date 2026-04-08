#!/bin/bash
set -e
# delete cache files older than 14 days (keeps recent to avoid constant re-downloads)
find /root/.cache/uv -type f -mtime +14 -delete 2>/dev/null || true
find /root/.cache/qmd -type f -mtime +14 -delete 2>/dev/null || true
find /root/.cache/puppeteer -type f -mtime +14 -delete 2>/dev/null || true
find /root/.npm/_cacache -type f -mtime +14 -delete 2>/dev/null || true
find /root/.npm/_npx -type f -mtime +14 -delete 2>/dev/null || true
echo "Cache retention cleanup completed - deleted files older than 14 days"
