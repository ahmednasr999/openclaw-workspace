#!/bin/bash
set -e
cd /root
ls -1dt openclaw-snapshot-* 2>/dev/null | tail -n +4 | xargs -r rm -rf
echo "Snapshots retention cleanup completed - kept last 3"
