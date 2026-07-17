#!/usr/bin/env python3
"""Validate and register a Fintech Radar LinkedIn visual.

The contract is fail-closed: completion requires a real 1080x1350 PNG in both
the workspace output directory and OpenClaw's Telegram-safe media directory,
plus a hash manifest proving the two files are identical.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "fintech-radar"
MEDIA_DIR = Path("/root/.openclaw/media/fintech-radar")
EXPECTED_SIZE = (1080, 1350)


def paths(date_key: str) -> tuple[Path, Path, Path]:
    filename = f"fintech-radar-linkedin-{date_key}.png"
    output = OUTPUT_DIR / filename
    media = MEDIA_DIR / filename
    return output, media, output.with_suffix(".manifest.json")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def inspect(path: Path, require_exact: bool = True) -> dict:
    with Image.open(path) as image:
        image.load()
        if image.format != "PNG":
            raise ValueError(f"expected PNG, got {image.format}")
        if require_exact and image.size != EXPECTED_SIZE:
            raise ValueError(f"expected {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}, got {image.size[0]}x{image.size[1]}")
        return {"format": image.format, "width": image.width, "height": image.height, "mode": image.mode}


def status(date_key: str) -> dict:
    output, media, manifest = paths(date_key)
    result = {"date": date_key, "output": str(output), "media": str(media), "manifest": str(manifest)}
    if not output.is_file() or not media.is_file() or not manifest.is_file():
        return {**result, "ready": False, "reason": "required artifact missing"}
    try:
        output_meta = inspect(output)
        media_meta = inspect(media)
        same_hash = digest(output) == digest(media)
    except Exception as exc:
        return {**result, "ready": False, "reason": str(exc)}
    return {**result, "ready": same_hash, "reason": "ready" if same_hash else "workspace/media hash mismatch", "image": output_meta, "media_image": media_meta, "sha256": digest(output)}


def main() -> int:
    parser = argparse.ArgumentParser()
    # Default to a read-only status check so legacy/ad-hoc verification calls
    # cannot fail merely because the subcommand was omitted.
    parser.add_argument("command", nargs="?", choices=["register", "status"], default="status")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--source")
    args = parser.parse_args()
    output, media, manifest = paths(args.date)
    if args.command == "register":
        if not args.source:
            parser.error("register requires --source")
        source = Path(args.source).resolve()
        source_meta = inspect(source, require_exact=False)
        source_ratio = source_meta["width"] / source_meta["height"]
        expected_ratio = EXPECTED_SIZE[0] / EXPECTED_SIZE[1]
        if abs(source_ratio - expected_ratio) > 0.01:
            raise ValueError(f"source aspect ratio {source_ratio:.4f} is not 4:5")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            normalized = image.convert("RGB").resize(EXPECTED_SIZE, Image.Resampling.LANCZOS)
            normalized.save(output, format="PNG", optimize=True)
        metadata = inspect(output)
        shutil.copy2(output, media)
        payload = {
            "registered_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": str(source),
            "output": str(output),
            "telegram_media": str(media),
            "image": metadata,
            "sha256": digest(output),
            "delivery_state": "READY_FOR_CURRENT_CHAT_FINAL_OR_EXPLICIT_SEND",
            "publishing_state": "APPROVAL_REQUIRED",
        }
        manifest.write_text(json.dumps(payload, indent=2) + "\n")
    result = status(args.date)
    print(json.dumps(result, indent=2))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
