#!/usr/bin/env bash
set -euo pipefail

workspace_dir="/root/.openclaw/workspace"
input_video="${1:-$workspace_dir/output/video-accountability/ahmed-nasr-ai-accountability-talking.mp4}"
output_video="${2:-$workspace_dir/output/video-accountability/ahmed-nasr-ai-accountability-briefing-board.mp4}"
subtitle_file="$workspace_dir/output/video-accountability/ai-accountability-briefing-board.ass"

if [[ ! -f "$input_video" ]]; then
  echo "Input video not found: $input_video" >&2
  exit 2
fi

if [[ ! -f "$subtitle_file" ]]; then
  echo "Graphics subtitle file not found: $subtitle_file" >&2
  exit 3
fi

mkdir -p "$(dirname "$output_video")"

ffmpeg -hide_banner -y \
  -i "$input_video" \
  -filter_complex "[0:v]split=2[source_bg][source_portrait];[source_bg]crop=720:718:0:281,scale=720:1280,setsar=1,gblur=sigma=42,eq=brightness=-0.55:saturation=0.50[background];[source_portrait]crop=420:718:150:281,scale=370:633,setsar=1,eq=brightness=-0.08:saturation=0.92[portrait];[background][portrait]overlay=316:250:enable='lt(t,19.24)',ass='$subtitle_file',format=yuv420p[video]" \
  -map "[video]" -map 0:a:0 \
  -c:v libx264 -preset medium -crf 18 -profile:v high -level 4.0 \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 160k \
  -movflags +faststart \
  "$output_video"

ffprobe -v error \
  -show_entries format=duration,size:stream=index,codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of json \
  "$output_video"
