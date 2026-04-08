#!/bin/bash
# Daily local snapshot — runs at 1AM Cairo (23:00 UTC)
# Keeps last 3 snapshots (~6.3 GB cap)

set -e
DATE=$(date +%Y%m%d)

echo "=== Snapshot started: $(date -u) ==="

# Snapshot OpenClaw config
cp -r ~/.openclaw/ ~/openclaw-snapshot-${DATE}/
echo "✅ OpenClaw snapshot: ~/openclaw-snapshot-${DATE}/"

# Keep only last 3 snapshots
cd /root
ls -1dt openclaw-snapshot-* 2>/dev/null | tail -n +4 | xargs -r rm -rf
echo "🧹 Kept last 3 snapshots only"

echo "=== Snapshot complete: $(date -u) ==="
