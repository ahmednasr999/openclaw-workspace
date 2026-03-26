#!/bin/bash
# youtube_transcript.sh
# Usage: youtube_transcript.sh <youtube_url> [output_file]
# Requires: yt-dlp, ~/.cookie-jar/youtube_cookies.txt

set -e

URL="$1"
OUTPUT="${2:-/tmp/transcript.txt}"
COOKIES="$HOME/.cookie-jar/youtube_cookies.txt"
TMP_DIR="/tmp/yt_transcript_$$"

if [ -z "$URL" ]; then
    echo "Usage: $0 <youtube_url> [output_file]" >&2
    exit 1
fi

COOKIE_COUNT=$(grep -c "." "$COOKIES" 2>/dev/null || echo "0")
if [ "$COOKIE_COUNT" -lt 5 ]; then
    echo "ERROR: Cookie file has only $COOKIE_COUNT lines - cookies may be expired" >&2
    echo "Re-fetch cookies from Mac using CDP script" >&2
    exit 1
fi

mkdir -p "$TMP_DIR"

echo "[youtube_transcript] Fetching: $URL" >&2

yt-dlp --no-update \
    --write-auto-sub \
    --sub-lang en \
    --skip-download \
    --cookies "$COOKIES" \
    -o "$TMP_DIR/sub" \
    "$URL" 2>/dev/null

VTT_FILE=$(ls "$TMP_DIR"/*.en.vtt 2>/dev/null | head -1)

if [ -z "$VTT_FILE" ] || [ ! -f "$VTT_FILE" ]; then
    echo "ERROR: No subtitles downloaded. Cookies may be expired." >&2
    echo "Re-fetch cookies from Mac." >&2
    rm -rf "$TMP_DIR"
    exit 1
fi

# Parse VTT -> clean plain text
# VTT format: timestamp line + caption lines (some with inline <00:xx> tags, some clean)
# We want: clean caption lines only, deduplicated
python3 -c "
import sys, re

seen = set()
for line in open('$VTT_FILE'):
    line = line.strip()
    if not line: continue
    if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'): continue
    if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}', line): continue
    if '<00:' in line: continue  # skip HTML-tagged caption lines
    line = re.sub(r'<[^>]+>', '', line)
    line = re.sub(r'align:start position:[0-9]+%', '', line).strip()
    if line and line not in seen:
        seen.add(line)
        print(line)
" > "$OUTPUT"

CHAR_COUNT=$(wc -c < "$OUTPUT")
LINE_COUNT=$(wc -l < "$OUTPUT")
echo "[youtube_transcript] Done: ${LINE_COUNT} lines, ${CHAR_COUNT} chars -> $OUTPUT" >&2
rm -rf "$TMP_DIR"
