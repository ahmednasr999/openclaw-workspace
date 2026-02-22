#!/bin/bash
# Daily local snapshot — runs at 1AM Cairo (23:00 UTC)
# Keeps last 7 snapshots, deletes older automatically

set -e
DATE=$(date +%Y%m%d)

echo "=== Snapshot started: $(date -u) ==="

# Snapshot OpenClaw config
cp -r ~/.openclaw/ ~/openclaw-snapshot-${DATE}/
echo "✅ OpenClaw snapshot: ~/openclaw-snapshot-${DATE}/"

# Snapshot Mission Control
cp -r ~/.openclaw/workspace/mission-control ~/mission-control-snapshot-${DATE}/
echo "✅ Mission Control snapshot: ~/mission-control-snapshot-${DATE}/"

# Delete OpenClaw snapshots older than 7 days
find ~/ -maxdepth 1 -type d -name "openclaw-snapshot-*" -mtime +7 -exec rm -rf {} + 2>/dev/null
echo "🧹 Cleaned openclaw snapshots older than 7 days"

# Delete Mission Control snapshots older than 7 days
find ~/ -maxdepth 1 -type d -name "mission-control-snapshot-*" -mtime +7 -exec rm -rf {} + 2>/dev/null
echo "🧹 Cleaned mission-control snapshots older than 7 days"

echo "=== Snapshot complete: $(date -u) ==="
