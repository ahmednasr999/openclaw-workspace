#!/bin/bash
set -euo pipefail
cd /root
ls -1dt openclaw-snapshot-* 2>/dev/null | tail -n +2 | xargs -r rm -rf --one-file-system
echo "Snapshots retention cleanup completed - kept latest 1"
