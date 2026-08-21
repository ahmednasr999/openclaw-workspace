#!/usr/bin/env python3
"""Prepare a remote or local video for evidence-based analysis.

The script performs deterministic media work only: retrieval, metadata extraction,
audio extraction, uniform frame sampling, storyboard creation, and caption cleanup.
It does not call an LLM or interpret the content.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"}
SUBTITLE_EXTENSIONS = {".vtt", ".srt"}
TIME_LINE = re.compile(
    r"(?P<start>(?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})\s+-->\s+"
    r"(?P<end>(?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})"
)
TAG = re.compile(r"<[^>]+>")


def fail(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
    except FileNotFoundError:
        fail(f"Required command is not installed: {command[0]}")
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        if len(detail) > 1200:
            detail = detail[-1200:]
        fail(f"Command failed ({command[0]}): {detail or exc}")
    raise AssertionError("unreachable")


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        fail("Only http and https URLs are supported")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def ensure_empty_target(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    meaningful = [item for item in path.iterdir() if item.name not in {".DS_Store"}]
    if meaningful:
        fail(f"Output directory is not empty: {path}")


def download_video(source: str, output_dir: Path, cookies: Path | None, languages: str) -> Path:
    command = [
        "yt-dlp",
        "--no-playlist",
        "--no-progress",
        "--format",
        "bv*+ba/b",
        "--merge-output-format",
        "mp4",
        "--write-info-json",
        "--write-description",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        languages,
        "--sub-format",
        "vtt",
        "--convert-subs",
        "vtt",
        "--output",
        str(output_dir / "source.%(ext)s"),
    ]
    if cookies:
        if not cookies.is_file():
            fail(f"Cookies file not found: {cookies}")
        command.extend(["--cookies", str(cookies)])
    command.append(source)
    run(command)

    candidates = sorted(
        path for path in output_dir.glob("source.*") if path.suffix.lower() in VIDEO_EXTENSIONS
    )
    if not candidates:
        fail("yt-dlp completed but no supported video file was produced")
    return max(candidates, key=lambda path: path.stat().st_size)


def find_local_sidecars(source: Path, output_dir: Path) -> None:
    for extension in (*SUBTITLE_EXTENSIONS, ".txt"):
        candidate = source.with_suffix(extension)
        if candidate.is_file():
            shutil.copy2(candidate, output_dir / f"source{extension}")


def probe_video(video: Path) -> dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(video),
        ],
        capture=True,
    )
    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"ffprobe returned invalid JSON: {exc}")

    video_stream = next(
        (stream for stream in raw.get("streams", []) if stream.get("codec_type") == "video"),
        {},
    )
    audio_stream = next(
        (stream for stream in raw.get("streams", []) if stream.get("codec_type") == "audio"),
        {},
    )
    duration_raw = raw.get("format", {}).get("duration") or video_stream.get("duration")
    try:
        duration = float(duration_raw)
    except (TypeError, ValueError):
        fail("Could not determine video duration")
    if not math.isfinite(duration) or duration <= 0:
        fail("Video duration is invalid")

    return {
        "duration_seconds": round(duration, 3),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio_stream.get("codec_name"),
        "has_audio": bool(audio_stream),
        "format_name": raw.get("format", {}).get("format_name"),
        "size_bytes": video.stat().st_size,
    }


def extract_audio(video: Path, output_dir: Path, has_audio: bool) -> Path | None:
    if not has_audio:
        return None
    audio = output_dir / "audio.m4a"
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            str(audio),
        ]
    )
    return audio


def extract_frames(video: Path, output_dir: Path, duration: float, frame_count: int) -> list[dict[str, Any]]:
    frame_dir = output_dir / "frames"
    frame_dir.mkdir()
    actual_count = max(1, min(frame_count, max(1, int(math.ceil(duration)))))
    sample_step = duration / actual_count
    index: list[dict[str, Any]] = []

    for number in range(actual_count):
        timestamp = min(duration - 0.05, (number + 0.5) * sample_step)
        timestamp = max(0.0, timestamp)
        frame_path = frame_dir / f"frame-{number + 1:03d}.jpg"
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-vf",
                "scale='min(1280,iw)':-2",
                "-q:v",
                "2",
                str(frame_path),
            ]
        )
        index.append(
            {
                "frame": str(frame_path.relative_to(output_dir)),
                "timestamp_seconds": round(timestamp, 3),
                "timestamp": format_timestamp(timestamp),
            }
        )

    (frame_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return index


def create_storyboard(output_dir: Path, frame_count: int) -> Path:
    columns = 4 if frame_count >= 8 else 3
    rows = math.ceil(frame_count / columns)
    storyboard = output_dir / "storyboard.jpg"
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-pattern_type",
            "glob",
            "-i",
            str(output_dir / "frames" / "frame-*.jpg"),
            "-vf",
            f"scale=320:-2,tile={columns}x{rows}:padding=8:margin=8:color=white",
            "-frames:v",
            "1",
            str(storyboard),
        ]
    )
    return storyboard


def format_timestamp(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def clean_caption_text(value: str) -> str:
    value = TAG.sub("", value)
    value = html.unescape(value)
    return " ".join(value.replace("&nbsp;", " ").split())


def normalize_subtitle(subtitle: Path, destination: Path) -> int:
    lines = subtitle.read_text(encoding="utf-8", errors="replace").splitlines()
    cues: list[tuple[str, str]] = []
    current_time: str | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_time, current_text
        text = clean_caption_text(" ".join(current_text))
        if current_time and text and (not cues or cues[-1][1] != text):
            cues.append((current_time, text))
        current_time = None
        current_text = []

    for line in lines:
        stripped = line.strip()
        match = TIME_LINE.search(stripped)
        if match:
            flush()
            start = match.group("start").replace(",", ".")
            parts = start.split(":")
            if len(parts) == 2:
                start = f"00:{start}"
            current_time = start.split(".")[0]
        elif not stripped:
            flush()
        elif current_time and not stripped.isdigit() and not stripped.startswith(("WEBVTT", "NOTE")):
            current_text.append(stripped)
    flush()

    destination.write_text(
        "\n".join(f"[{timestamp}] {text}" for timestamp, text in cues) + ("\n" if cues else ""),
        encoding="utf-8",
    )
    return len(cues)


def prepare_transcript(output_dir: Path) -> tuple[Path | None, int]:
    subtitles = sorted(
        path
        for path in output_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUBTITLE_EXTENSIONS
    )
    if not subtitles:
        text_sidecars = sorted(output_dir.glob("source*.txt"))
        if text_sidecars:
            transcript = output_dir / "transcript.txt"
            shutil.copy2(text_sidecars[0], transcript)
            return transcript, sum(1 for line in transcript.read_text(errors="replace").splitlines() if line.strip())
        return None, 0

    preferred = next((path for path in subtitles if ".en" in path.name.lower()), subtitles[0])
    transcript = output_dir / "transcript.txt"
    cue_count = normalize_subtitle(preferred, transcript)
    return transcript if cue_count else None, cue_count


def load_platform_metadata(output_dir: Path) -> dict[str, Any]:
    info_files = sorted(output_dir.glob("source*.info.json"))
    if not info_files:
        return {}
    try:
        raw = json.loads(info_files[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    keep = (
        "id",
        "title",
        "description",
        "uploader",
        "channel",
        "creator",
        "upload_date",
        "timestamp",
        "duration",
        "webpage_url",
        "extractor",
        "view_count",
        "like_count",
        "comment_count",
        "repost_count",
    )
    return {key: raw.get(key) for key in keep if raw.get(key) is not None}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="http(s) video URL or local video file")
    parser.add_argument("--output-dir", required=True, help="new, empty output directory")
    parser.add_argument("--cookies", help="optional Netscape-format cookies file for yt-dlp")
    parser.add_argument("--frame-count", type=int, default=12, help="uniform samples (4-40; default: 12)")
    parser.add_argument(
        "--subtitle-languages",
        default="en.*,en,ar.*,ar",
        help="yt-dlp subtitle language expression",
    )
    args = parser.parse_args()
    if not 4 <= args.frame_count <= 40:
        parser.error("--frame-count must be between 4 and 40")
    return args


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    ensure_empty_target(output_dir)
    cookies = Path(args.cookies).expanduser().resolve() if args.cookies else None
    remote = is_url(args.source)

    if remote:
        video = download_video(args.source, output_dir, cookies, args.subtitle_languages)
    else:
        video = Path(args.source).expanduser().resolve()
        if not video.is_file():
            fail(f"Local video not found: {video}")
        if video.suffix.lower() not in VIDEO_EXTENSIONS:
            fail(f"Unsupported local video extension: {video.suffix}")
        find_local_sidecars(video, output_dir)

    media = probe_video(video)
    audio = extract_audio(video, output_dir, bool(media["has_audio"]))
    frames = extract_frames(video, output_dir, float(media["duration_seconds"]), args.frame_count)
    storyboard = create_storyboard(output_dir, len(frames))
    transcript, cue_count = prepare_transcript(output_dir)
    platform = load_platform_metadata(output_dir)

    metadata = {
        "source": args.source,
        "source_type": "url" if remote else "local_file",
        "platform": platform,
        "media": media,
    }
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": args.source,
        "source_type": "url" if remote else "local_file",
        "artifacts": {
            "video": str(video),
            "audio": str(audio.relative_to(output_dir)) if audio else None,
            "metadata": str(metadata_path.relative_to(output_dir)),
            "storyboard": str(storyboard.relative_to(output_dir)),
            "frame_index": "frames/index.json",
            "transcript": str(transcript.relative_to(output_dir)) if transcript else None,
        },
        "frame_count": len(frames),
        "transcript": {
            "status": "available" if transcript else "unavailable",
            "source": "platform_caption_or_sidecar" if transcript else None,
            "cue_count": cue_count,
        },
        "analysis_status": "prepared_not_analyzed",
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(json.dumps({"status": "prepared", "output_dir": str(output_dir), **manifest}, indent=2))


if __name__ == "__main__":
    main()
