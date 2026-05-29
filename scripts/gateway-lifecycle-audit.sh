#!/usr/bin/env bash
set -euo pipefail

echo "Gateway lifecycle audit"
echo "OpenClaw: $(openclaw --version 2>/dev/null || true)"
echo "Systemd service:"
systemctl status openclaw-gateway.service --no-pager --lines 4 2>/dev/null || true
echo "Live gateway processes:"
pgrep -af 'openclaw.*gateway --port 18789' || true
echo "Port 18789:"
ss -ltnp 2>/dev/null | grep ':18789' || true
echo "Policy: do not restart the live gateway from user-facing work unless Ahmed explicitly asks for gateway lifecycle maintenance."
