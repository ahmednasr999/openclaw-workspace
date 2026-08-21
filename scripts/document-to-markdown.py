#!/usr/bin/env python3
"""Route local document extraction through AnyDoc with safe fallbacks.

AnyDoc is preferred for supported non-presentation files. MarkItDown remains
preferred for presentations because it emits explicit slide boundaries, and it
is the fallback when AnyDoc cannot produce meaningful text (for example,
scanned PDFs). Both parsers run locally from a pinned, isolated environment.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_PARSER_PYTHON = WORKSPACE / "tools" / "document-parser-venv" / "bin" / "python"
ANYDOC_EXTENSIONS = {
    ".csv",
    ".doc",
    ".docm",
    ".docx",
    ".epub",
    ".odp",
    ".ods",
    ".odt",
    ".pdf",
    ".rtf",
    ".xls",
    ".xlsb",
    ".xlsm",
    ".xlsx",
}
PRESENTATION_EXTENSIONS = {".pot", ".pps", ".ppsm", ".ppsx", ".ppt", ".pptm", ".pptx"}


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parser_python() -> Path:
    configured = os.environ.get("DOCUMENT_PARSER_PYTHON")
    return Path(configured).expanduser() if configured else DEFAULT_PARSER_PYTHON


def command_for(backend: str, source: str) -> list[str]:
    python = parser_python()
    if backend == "anydoc":
        return [str(python), str(Path(__file__).resolve()), "--anydoc-worker", source]
    return [str(python), "-m", "markitdown", source]


def backend_order(source: str, requested: str) -> list[str]:
    if requested != "auto":
        return [requested]
    if is_url(source):
        return ["markitdown"]
    suffix = Path(source).suffix.casefold()
    if suffix in PRESENTATION_EXTENSIONS:
        return ["markitdown", "anydoc"]
    if suffix in ANYDOC_EXTENSIONS:
        return ["anydoc", "markitdown"]
    return ["markitdown"]


def run_backend(backend: str, source: str, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command_for(backend, source),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def run_anydoc_worker(source: str) -> int:
    try:
        import anydoc

        markdown = anydoc.to_markdown(source)
        if not markdown.strip():
            print("AnyDoc returned no meaningful text", file=sys.stderr)
            return 2
        sys.stdout.write(markdown)
        return 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="Local document path or HTTP(S) URL")
    parser.add_argument("--backend", choices=("auto", "anydoc", "markitdown"), default="auto")
    parser.add_argument("--backend-marker", action="store_true", help="Report selected backend on stderr")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--anydoc-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if not args.source:
        parser.error("source is required")
    if args.anydoc_worker:
        return run_anydoc_worker(args.source)

    runtime = parser_python()
    if not runtime.is_file():
        print(
            f"Document parser runtime is missing: {runtime}. "
            "Run tools/document-parser/install.sh to install the pinned environment.",
            file=sys.stderr,
        )
        return 2
    if not is_url(args.source):
        source_path = Path(args.source).expanduser()
        if not source_path.is_file():
            print(f"Source file not found: {source_path}", file=sys.stderr)
            return 2
        source = str(source_path.resolve())
    else:
        source = args.source

    failures: list[str] = []
    for backend in backend_order(source, args.backend):
        try:
            result = run_backend(backend, source, args.timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            failures.append(f"{backend}: {type(exc).__name__}: {exc}")
            continue
        if result.returncode == 0 and result.stdout.strip():
            if args.backend_marker:
                print(f"document-parser-backend={backend}", file=sys.stderr)
            sys.stdout.write(result.stdout)
            return 0
        detail = result.stderr.strip() or "no meaningful text"
        failures.append(f"{backend}: {detail}")

    print("Document extraction failed: " + " | ".join(failures), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
