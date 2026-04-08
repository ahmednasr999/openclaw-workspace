#!/bin/bash
# NASR Browser Bridge - navigate Ahmed-Mac Chrome to a URL
# Usage: browser-navigate.sh "https://x.com/..."

URL="$1"
SECRET="${BRIDGE_SECRET:-nasr-bridge-2026}"
VPS="http://localhost:3010"

if [ -z "$URL" ]; then
  echo "Usage: $0 <url>"
  exit 1
fi

curl -s -X POST "$VPS/navigate" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$URL\", \"secret\": \"$SECRET\"}"
echo ""
