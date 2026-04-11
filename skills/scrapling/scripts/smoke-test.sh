#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-/tmp/scrapling-smoke}"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/quotes.txt"

bash /root/.openclaw/workspace/skills/scrapling/scripts/scrape.sh get \
  https://quotes.toscrape.com/ \
  "$OUT_FILE" \
  '.quote'

echo "Smoke output: $OUT_FILE"
wc -c "$OUT_FILE"
sed -n '1,20p' "$OUT_FILE"
