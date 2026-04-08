#!/bin/bash
set -e
cd /root
ls -1t openclaw-backup-*.tar.gz 2>/dev/null | tail -n +4 | xargs -r rm -f
echo "Backups retention cleanup completed - kept last 3"
