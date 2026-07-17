#!/usr/bin/env bash
set -euo pipefail

NO_SEND=0
if [[ "${1:-}" == "--no-send" ]]; then
  NO_SEND=1
fi

pct=$(df -P / | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
line=$(df -h / | awk 'NR==2 {print $3 " used / " $4 " free / " $5 " used"}')
inodes=$(df -ih / | awk 'NR==2 {print $5 " inodes used"}')
status="Healthy"
if (( pct >= 85 )); then
  status="Critical"
elif (( pct >= 75 )); then
  status="Watch"
fi
snapshot_size=$(du -ch /root/openclaw-snapshot-*.tar.zst 2>/dev/null | awk '/total$/ {print $1}' || true)
snapshot_size=${snapshot_size:-0}
archive_size=$(du -sh /root/.openclaw/session-archives 2>/dev/null | awk '{print $1}' || echo 0)
agents_size=$(du -sh /root/.openclaw/agents 2>/dev/null | awk '{print $1}' || echo unknown)
hermes_size=$(du -sh /srv/hermes-pilot 2>/dev/null | awk '{print $1}' || echo absent)

top=$(du -xh --max-depth=1 /root /srv /var 2>/dev/null | sort -h | tail -12 | sed 's#\t#  #')

message=$(cat <<EOF
**Weekly VPS Disk Report**

| Metric | Value |
|---|---:|
| Status | ${status} |
| Root disk | ${line} |
| Inodes | ${inodes} |
| Agent state | ${agents_size} |
| Hermes pilot | ${hermes_size} |
| Session archives | ${archive_size} |
| Latest snapshot | ${snapshot_size} |

**Largest areas**
\`\`\`
${top}
\`\`\`
EOF
)

if [[ "$NO_SEND" == "1" ]]; then
  printf '%s\n' "$message"
  exit 0
fi

openclaw message send --channel telegram --target 866838380 --message "$message" --json >/dev/null
