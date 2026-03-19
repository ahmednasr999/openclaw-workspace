#!/bin/bash
# YouTube Transcript Extractor
# Uses yt-dlp to download auto-generated subtitles and clean them
# Usage: youtube-transcript.sh <video_url_or_id> [output_file]
# Cost: FREE (no API key needed)

set -euo pipefail

VIDEO="${1:?Usage: youtube-transcript.sh <video_url_or_id> [output_file]}"
OUTPUT="${2:-/dev/stdout}"

# Handle video ID vs URL
if [[ ! "$VIDEO" =~ ^http ]]; then
    VIDEO="https://www.youtube.com/watch?v=$VIDEO"
fi

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Download subtitles (try English, then auto-generated)
yt-dlp \
    --write-auto-sub \
    --sub-lang "en" \
    --skip-download \
    --sub-format vtt \
    --no-update \
    --quiet \
    -o "$TMPDIR/transcript" \
    "$VIDEO" 2>/dev/null

VTT_FILE=$(find "$TMPDIR" -name "*.vtt" | head -1)

if [[ -z "$VTT_FILE" ]]; then
    echo "ERROR: No transcript available for this video" >&2
    exit 1
fi

# Clean VTT to plain text
python3 -c "
import re, sys

with open('$VTT_FILE') as f:
    vtt = f.read()

lines = []
for line in vtt.split('\n'):
    if '-->' in line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or not line.strip():
        continue
    clean = re.sub(r'<[^>]+>', '', line).strip()
    if clean and clean not in lines[-1:]:
        lines.append(clean)

deduped = []
for line in lines:
    if not deduped or line != deduped[-1]:
        deduped.append(line)

text = ' '.join(deduped)
text = re.sub(r'\s+', ' ', text).strip()
print(text)
" > "$OUTPUT"

if [[ "$OUTPUT" != "/dev/stdout" ]]; then
    CHARS=$(wc -c < "$OUTPUT")
    echo "Transcript saved to $OUTPUT ($CHARS chars)" >&2
fi
