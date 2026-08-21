#!/usr/bin/env bash
set -euo pipefail

workspace_dir="/root/.openclaw/workspace"
source_image="$workspace_dir/output/seedance/ahmed-executive-reference-9x16.jpg"
subtitle_file="$workspace_dir/output/video-accountability/ai-accountability-motion.ass"
output_video="${1:-$workspace_dir/output/video-accountability/ahmed-nasr-ai-accountability-motion.mp4}"

if [[ ! -f "$source_image" ]]; then
  echo "Source image not found: $source_image" >&2
  exit 2
fi

if [[ ! -f "$subtitle_file" ]]; then
  echo "Graphics file not found: $subtitle_file" >&2
  exit 3
fi

mkdir -p "$(dirname "$output_video")"

ffmpeg -hide_banner -y \
  -loop 1 -framerate 25 -t 22 -i "$source_image" \
  -f lavfi -t 22 -i "anullsrc=channel_layout=stereo:sample_rate=48000" \
  -filter_complex "[0:v]scale=760:1351,crop=720:1280,zoompan=z='min(zoom+0.00010,1.035)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)-18':d=1:s=720x1280:fps=25,setsar=1,eq=contrast=1.06:saturation=0.80:brightness=-0.06,vignette=PI/5,ass='$subtitle_file',format=yuv420p[video]" \
  -map "[video]" -map 1:a:0 \
  -c:v libx264 -preset medium -crf 18 -profile:v high -level 4.0 \
  -c:a aac -b:a 128k -ar 48000 \
  -movflags +faststart -shortest \
  "$output_video"

ffprobe -v error \
  -show_entries format=duration,size:stream=index,codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of json \
  "$output_video"
