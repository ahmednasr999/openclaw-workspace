#!/usr/bin/env bash
set -euo pipefail

PCT=$(df --output=pcent / | tail -1 | tr -dc '0-9')
FREE=$(df -h / | tail -1 | awk '{print $4}')
USED=$(df -h / | tail -1 | awk '{print $3}')
TOTAL=$(df -h / | tail -1 | awk '{print $2}')

if [ "$PCT" -ge 80 ]; then
  echo "🚨 Disk urgent: ${PCT}% used (${USED}/${TOTAL}, ${FREE} free). Action needed now."
elif [ "$PCT" -ge 70 ]; then
  echo "⚠️ Disk warning: ${PCT}% used (${USED}/${TOTAL}, ${FREE} free). Plan cleanup today."
else
  echo "✅ Disk healthy: ${PCT}% used (${USED}/${TOTAL}, ${FREE} free)."
fi
