#!/usr/bin/env python3
"""Common helpers for Slides Lane v2 source ingestion.

Copyright (c) OpenAI. All rights reserved.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

TASK_DIRS = [
    "sources",
    "normalized",
    "assets",
    "planning",
    "authoring",
    "authoring/generated_assets",
    "rendered",
    "qa",
    "exports",
]

REGISTRY_VERSION = 1
REGISTRY_REL_PATH = Path("sources") / "sources.json"
INTAKE_JSON_REL_PATH = Path("planning") / "intake.json"
INTAKE_MD_REL_PATH = Path("planning") / "intake.md"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".svg", ".heic", ".heif"}
TEXT_EXTS = {".md", ".markdown", ".txt", ".rst"}
MARKITDOWN_FRIENDLY_EXTS = {
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
    ".html",
    ".htm",
    ".epub",
    ".csv",
    ".tsv",
    ".rtf",
    ".odt",
}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        elif tag in {"p", "div", "section", "article", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in {"p", "div", "section", "article", "li"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            cleaned = data.strip()
            if cleaned:
                self._chunks.append(cleaned)

    def get_text(self) -> str:
        joined = " ".join(self._chunks)
        joined = re.sub(r"\n\s+", "\n", joined)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        joined = re.sub(r"[ \t]{2,}", " ", joined)
        return joined.strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_task_dirs(task_dir: Path) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    for rel in TASK_DIRS:
        (task_dir / rel).mkdir(parents=True, exist_ok=True)


def task_rel(path: Path, task_dir: Path) -> str:
    return str(path.resolve().relative_to(task_dir.resolve()))


def task_abs(rel_path: str | Path, task_dir: Path) -> Path:
    return task_dir / Path(rel_path)


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def slugify(value: str, max_len: int = 80) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-._")
    return value[:max_len] or "source"


def load_registry(task_dir: Path) -> dict[str, Any]:
    ensure_task_dirs(task_dir)
    path = task_dir / REGISTRY_REL_PATH
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    registry = {
        "version": REGISTRY_VERSION,
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
        "taskDir": str(task_dir.resolve()),
        "entries": [],
    }
    save_registry(task_dir, registry)
    return registry


def save_registry(task_dir: Path, registry: dict[str, Any]) -> Path:
    registry["updatedAt"] = now_iso()
    registry["taskDir"] = str(task_dir.resolve())
    path = task_dir / REGISTRY_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def next_source_id(registry: dict[str, Any]) -> str:
    count = len(registry.get("entries", [])) + 1
    return f"src_{count:03d}"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_file_source(task_dir: Path, source_input: str, move: bool = False) -> dict[str, Any]:
    registry = load_registry(task_dir)
    source_id = next_source_id(registry)
    src_path = Path(source_input).expanduser().resolve()
    if not src_path.exists() or not src_path.is_file():
        raise FileNotFoundError(f"Source file not found: {source_input}")

    ext = src_path.suffix.lower()
    name_slug = slugify(src_path.stem)
    imported_name = f"{source_id}-{name_slug}{ext}"
    imported_path = _unique_path(task_dir / "sources" / imported_name)

    if move:
        shutil.move(str(src_path), str(imported_path))
        import_mode = "move"
    else:
        shutil.copy2(src_path, imported_path)
        import_mode = "copy"

    entry: dict[str, Any] = {
        "id": source_id,
        "inputType": "file",
        "originalInput": str(src_path),
        "displayName": src_path.name,
        "ext": ext,
        "mimeType": mimetypes.guess_type(str(imported_path))[0],
        "sourcePath": task_rel(imported_path, task_dir),
        "importMode": import_mode,
        "importedAt": now_iso(),
        "sizeBytes": imported_path.stat().st_size,
        "sourceSha256": sha256_file(imported_path),
        "sourceKind": infer_source_kind(ext),
        "extractionStatus": "pending",
    }
    registry["entries"].append(entry)
    save_registry(task_dir, registry)
    return entry


def register_url_source(task_dir: Path, url: str) -> dict[str, Any]:
    registry = load_registry(task_dir)
    source_id = next_source_id(registry)
    parsed = urlparse(url)
    base_name = parsed.netloc + ("-" + parsed.path.strip("/").replace("/", "-") if parsed.path.strip("/") else "")
    slug = slugify(base_name)
    url_note_path = _unique_path(task_dir / "sources" / f"{source_id}-{slug}.url")
    url_note_path.write_text(url + "\n", encoding="utf-8")

    entry = {
        "id": source_id,
        "inputType": "url",
        "originalInput": url,
        "displayName": url,
        "ext": ".url",
        "mimeType": "text/uri-list",
        "sourcePath": task_rel(url_note_path, task_dir),
        "importMode": "url",
        "importedAt": now_iso(),
        "sizeBytes": url_note_path.stat().st_size,
        "sourceSha256": sha256_file(url_note_path),
        "sourceKind": "url",
        "extractionStatus": "pending",
        "url": url,
    }
    registry["entries"].append(entry)
    save_registry(task_dir, registry)
    return entry


def infer_source_kind(ext: str) -> str:
    ext = ext.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in TEXT_EXTS:
        return "text"
    if ext in {".pptx", ".ppt"}:
        return "presentation"
    if ext in {".pdf"}:
        return "pdf"
    if ext in {".docx", ".doc", ".odt", ".rtf"}:
        return "document"
    if ext in {".html", ".htm"}:
        return "web"
    if ext in {".csv", ".tsv", ".xlsx", ".xls"}:
        return "data"
    return "file"


def run_markitdown(input_value: str) -> tuple[bool, str, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "markitdown", input_value],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0, proc.stdout, proc.stderr


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _copy_to_assets_if_image(task_dir: Path, entry: dict[str, Any]) -> str | None:
    source_rel = entry.get("sourcePath")
    if not source_rel:
        return None
    source_path = task_abs(source_rel, task_dir)
    ext = source_path.suffix.lower()
    if ext not in IMAGE_EXTS:
        return None
    asset_path = _unique_path(task_dir / "assets" / source_path.name)
    if not asset_path.exists():
        shutil.copy2(source_path, asset_path)
    return task_rel(asset_path, task_dir)


def _simple_url_extract(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 SlidesLaneV2/1.0"})
    with urlopen(req, timeout=20) as resp:
        raw = resp.read()
        content_type = resp.headers.get_content_type()
        charset = resp.headers.get_content_charset() or "utf-8"
    text = raw.decode(charset, errors="replace")
    if content_type == "text/html" or "<html" in text.lower():
        parser = _HTMLTextExtractor()
        parser.feed(text)
        body = parser.get_text()
        if body:
            return body
    return text.strip()


def _normalized_target_path(task_dir: Path, entry: dict[str, Any]) -> Path:
    display_slug = slugify(Path(entry.get("displayName") or entry["id"]).stem)
    return _unique_path(task_dir / "normalized" / f"{entry['id']}-{display_slug}.md")


def extract_entry(task_dir: Path, entry: dict[str, Any], force: bool = False) -> dict[str, Any]:
    if not force and entry.get("normalizedPath"):
        normalized_path = task_abs(entry["normalizedPath"], task_dir)
        if normalized_path.exists() and entry.get("extractionStatus") == "completed":
            return entry

    normalized_path = _normalized_target_path(task_dir, entry)
    source_kind = entry.get("sourceKind") or infer_source_kind(entry.get("ext", ""))
    method = ""
    quality = ""
    body = ""

    try:
        if entry.get("inputType") == "url":
            ok, stdout, stderr = run_markitdown(entry["url"])
            if ok and stdout.strip():
                body = stdout.strip()
                method = "markitdown-url"
                quality = "full"
            else:
                body = _simple_url_extract(entry["url"])
                method = "urllib-html-fallback"
                quality = "basic"
                if stderr.strip():
                    entry["extractionWarning"] = stderr.strip()
        else:
            source_path = task_abs(entry["sourcePath"], task_dir)
            ext = source_path.suffix.lower()
            if ext in TEXT_EXTS:
                body = source_path.read_text(encoding="utf-8", errors="replace").strip()
                method = "direct-text-copy"
                quality = "full"
            elif ext in MARKITDOWN_FRIENDLY_EXTS:
                ok, stdout, stderr = run_markitdown(str(source_path))
                if ok and stdout.strip():
                    body = stdout.strip()
                    method = "markitdown-file"
                    quality = "full"
                else:
                    body = (
                        f"# Source extraction fallback\n\n"
                        f"Original file: `{entry.get('displayName', source_path.name)}`\n\n"
                        f"The source was imported successfully, but structured extraction failed.\n"
                        f"Use the original file from `{entry.get('sourcePath')}` for manual review.\n"
                    )
                    method = "fallback-stub"
                    quality = "stub"
                    if stderr.strip():
                        entry["extractionWarning"] = stderr.strip()
            elif source_kind == "image":
                asset_rel = _copy_to_assets_if_image(task_dir, entry)
                if asset_rel:
                    entry["assetPath"] = asset_rel
                body = (
                    f"# Image reference\n\n"
                    f"Image source: `{entry.get('displayName')}`\n\n"
                    f"- Source path: `{entry.get('sourcePath')}`\n"
                    + (f"- Asset path: `{asset_rel}`\n" if asset_rel else "")
                    + "\nUse this as a visual/style reference during deck planning and authoring.\n"
                )
                method = "image-reference-note"
                quality = "basic"
            else:
                body = (
                    f"# Source file note\n\n"
                    f"Imported source: `{entry.get('displayName')}`\n\n"
                    f"- Source path: `{entry.get('sourcePath')}`\n"
                    f"- Source kind: `{source_kind}`\n\n"
                    "This source type does not yet have structured extraction in Slides Lane v2. "
                    "Review the original file directly if needed.\n"
                )
                method = "source-note"
                quality = "stub"

        if not body.strip():
            body = (
                f"# Empty extraction result\n\n"
                f"Source: `{entry.get('displayName')}`\n\n"
                "The extractor returned no readable content. Review the original source manually.\n"
            )
            if not method:
                method = "empty-result-fallback"
            if not quality:
                quality = "stub"

        _write_text(normalized_path, body)
        entry["normalizedPath"] = task_rel(normalized_path, task_dir)
        entry["normalizedSha256"] = sha256_file(normalized_path)
        entry["normalizedSizeBytes"] = normalized_path.stat().st_size
        entry["extractionStatus"] = "completed"
        entry["extractionMethod"] = method
        entry["extractionQuality"] = quality
        entry["extractedAt"] = now_iso()
        return entry
    except (OSError, URLError, subprocess.SubprocessError, TimeoutError) as exc:
        entry["extractionStatus"] = "failed"
        entry["extractionMethod"] = method or "error"
        entry["extractionQuality"] = quality or "none"
        entry["extractionError"] = str(exc)
        entry["extractedAt"] = now_iso()
        return entry


def extract_all_sources(task_dir: Path, force: bool = False) -> dict[str, Any]:
    registry = load_registry(task_dir)
    updated_entries = []
    for entry in registry.get("entries", []):
        updated_entries.append(extract_entry(task_dir, entry, force=force))
    registry["entries"] = updated_entries
    save_registry(task_dir, registry)
    return registry


def _entry_summary(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry.get("id"),
        "displayName": entry.get("displayName"),
        "inputType": entry.get("inputType"),
        "sourceKind": entry.get("sourceKind"),
        "sourcePath": entry.get("sourcePath"),
        "normalizedPath": entry.get("normalizedPath"),
        "assetPath": entry.get("assetPath"),
        "extractionStatus": entry.get("extractionStatus", "pending"),
        "extractionMethod": entry.get("extractionMethod"),
        "extractionQuality": entry.get("extractionQuality"),
        "sizeBytes": entry.get("sizeBytes"),
        "normalizedSizeBytes": entry.get("normalizedSizeBytes"),
        "sourceSha256": entry.get("sourceSha256"),
        "normalizedSha256": entry.get("normalizedSha256"),
        "warning": entry.get("extractionWarning"),
        "error": entry.get("extractionError"),
    }


def build_intake_manifest(task_dir: Path) -> dict[str, Any]:
    registry = load_registry(task_dir)
    entries = registry.get("entries", [])
    status_counts: dict[str, int] = {}
    quality_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for entry in entries:
        status = entry.get("extractionStatus", "pending")
        quality = entry.get("extractionQuality", "none")
        kind = entry.get("sourceKind", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        quality_counts[quality] = quality_counts.get(quality, 0) + 1
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    manifest = {
        "version": REGISTRY_VERSION,
        "generatedAt": now_iso(),
        "taskDir": str(task_dir.resolve()),
        "registryPath": str(REGISTRY_REL_PATH),
        "sourceCount": len(entries),
        "statusCounts": status_counts,
        "qualityCounts": quality_counts,
        "kindCounts": kind_counts,
        "entries": [_entry_summary(entry) for entry in entries],
    }

    intake_json_path = task_dir / INTAKE_JSON_REL_PATH
    intake_json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_intake_markdown(task_dir, manifest)
    return manifest


def write_intake_markdown(task_dir: Path, manifest: dict[str, Any]) -> Path:
    lines = [
        "# Slides Intake Summary",
        "",
        f"- Generated: {manifest.get('generatedAt')}",
        f"- Source count: {manifest.get('sourceCount', 0)}",
        f"- Status counts: {json.dumps(manifest.get('statusCounts', {}), ensure_ascii=False)}",
        f"- Quality counts: {json.dumps(manifest.get('qualityCounts', {}), ensure_ascii=False)}",
        f"- Kind counts: {json.dumps(manifest.get('kindCounts', {}), ensure_ascii=False)}",
        "",
        "## Sources",
        "",
    ]
    for entry in manifest.get("entries", []):
        lines.extend(
            [
                f"### {entry.get('id')} - {entry.get('displayName')}",
                f"- Type: {entry.get('inputType')} / {entry.get('sourceKind')}",
                f"- Source: `{entry.get('sourcePath')}`" if entry.get("sourcePath") else "- Source: n/a",
                f"- Normalized: `{entry.get('normalizedPath')}`" if entry.get("normalizedPath") else "- Normalized: not created",
                f"- Asset: `{entry.get('assetPath')}`" if entry.get("assetPath") else "- Asset: n/a",
                f"- Extraction: {entry.get('extractionStatus')} via {entry.get('extractionMethod') or 'n/a'} ({entry.get('extractionQuality') or 'n/a'})",
            ]
        )
        if entry.get("warning"):
            lines.append(f"- Warning: {entry['warning']}")
        if entry.get("error"):
            lines.append(f"- Error: {entry['error']}")
        lines.append("")

    output_path = task_dir / INTAKE_MD_REL_PATH
    _write_text(output_path, "\n".join(lines))
    return output_path
