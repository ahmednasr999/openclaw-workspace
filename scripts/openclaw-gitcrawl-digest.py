#!/usr/bin/env python3
"""Generate a read-only OpenClaw GitHub digest using gitcrawl."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any

DEFAULT_REPOS = [
    "openclaw/openclaw",
    "openclaw/docs",
    "openclaw/gitcrawl",
    "openclaw/telecrawl",
    "openclaw/openclaw.ai",
]
STATE_HOME = Path(os.environ.get("GITCRAWL_DIGEST_HOME", "/root/.local/share/openclaw-gitcrawl-digest"))
REPORT_DIR = Path(os.environ.get("GITCRAWL_DIGEST_REPORT_DIR", "/root/.openclaw/workspace/reports"))


def run(cmd: list[str], *, env: dict[str, str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, env=env, text=True, capture_output=True, check=check)


def extract_json(stdout: str) -> Any:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{.*\}|\[.*\])\s*$", text, flags=re.S)
    if not match:
        raise ValueError(f"No JSON object found in output: {text[-300:]}")
    return json.loads(match.group(1))


def github_token(base_env: dict[str, str]) -> str:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        token = base_env.get(name, "").strip()
        if token:
            return token
    proc = subprocess.run(["gh", "auth", "token"], text=True, capture_output=True)
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    return ""


def item_line(thread: dict[str, Any]) -> str:
    number = thread.get("number", "?")
    kind = thread.get("kind", "thread")
    state = thread.get("state", "unknown")
    title = str(thread.get("title") or "(untitled)").replace("\n", " ").strip()
    url = thread.get("html_url") or ""
    updated = thread.get("updated_at_gh") or thread.get("updated_at") or ""
    prefix = f"#{number} {kind} {state}"
    if url:
        return f"- [{prefix}]({url}) - {title} - updated {updated}"
    return f"- {prefix} - {title} - updated {updated}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only gitcrawl digest for OpenClaw repos.")
    parser.add_argument("--repos", default=",".join(DEFAULT_REPOS), help="Comma-separated owner/repo list")
    parser.add_argument("--limit", type=int, default=25, help="Per-repo sync/thread limit")
    parser.add_argument("--no-sync", action="store_true", help="Only read existing local cache")
    args = parser.parse_args()

    repos = [repo.strip() for repo in args.repos.split(",") if repo.strip()]
    if not repos:
        print("No repos provided", file=sys.stderr)
        return 2

    base_env = os.environ.copy()
    token = github_token(base_env)
    if not token:
        print("Missing GitHub token. Run gh auth login or set GITHUB_TOKEN.", file=sys.stderr)
        return 2

    STATE_HOME.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    env = base_env | {
        "HOME": str(STATE_HOME),
        "GITHUB_TOKEN": token,
        "GH_TOKEN": token,
        "GITCRAWL_NO_UPDATE_CHECK": "1",
        "CRAWLKIT_NO_UPDATE_CHECK": "1",
    }

    config = STATE_HOME / ".config/gitcrawl/config.toml"
    if not config.exists():
        run(["gitcrawl", "init", "--json"], env=env)

    results: list[dict[str, Any]] = []
    for repo in repos:
        sync_result: dict[str, Any] | None = None
        sync_error = ""
        if not args.no_sync:
            proc = run(["gitcrawl", "sync", repo, "--state", "open", "--limit", str(args.limit), "--json"], env=env, check=False)
            if proc.returncode == 0:
                sync_result = extract_json(proc.stdout)
            else:
                sync_error = (proc.stderr or proc.stdout).strip()[-1000:]
        proc = run(["gitcrawl", "threads", repo, "--limit", str(args.limit), "--json"], env=env, check=False)
        threads: list[dict[str, Any]] = []
        thread_error = ""
        if proc.returncode == 0:
            payload = extract_json(proc.stdout) or {}
            threads = payload.get("threads", []) if isinstance(payload, dict) else []
        else:
            thread_error = (proc.stderr or proc.stdout).strip()[-1000:]
        results.append({"repo": repo, "sync": sync_result, "sync_error": sync_error, "threads": threads, "thread_error": thread_error})

    status_proc = run(["gitcrawl", "status", "--json"], env=env, check=False)
    status = extract_json(status_proc.stdout) if status_proc.returncode == 0 else {}

    now = datetime.now(ZoneInfo("Africa/Cairo"))
    report_path = REPORT_DIR / f"openclaw-gitcrawl-digest-{now.strftime('%Y-%m-%d')}.md"
    lines = [
        "# OpenClaw Gitcrawl Digest",
        "",
        f"Generated: {now.isoformat(timespec='seconds')}",
        f"State home: `{STATE_HOME}`",
        "Mode: read-only sync/status/thread report",
        "",
        "## Archive Status",
        "",
        f"- Summary: {status.get('summary', 'unknown')}",
        f"- Database: `{status.get('database_path', '')}`",
        f"- Last sync: {status.get('last_sync_at', '')}",
        "",
        "## Repositories",
        "",
    ]

    for result in results:
        repo = result["repo"]
        sync = result.get("sync") or {}
        threads = result.get("threads") or []
        open_threads = [t for t in threads if t.get("state") == "open"]
        lines.extend([
            f"### {repo}",
            "",
            f"- Sync error: {result['sync_error'] or 'none'}",
            f"- Thread read error: {result['thread_error'] or 'none'}",
            f"- Threads synced this run: {sync.get('threads_synced', 'n/a')}",
            f"- Cached threads shown: {len(threads)}",
            f"- Open cached threads shown: {len(open_threads)}",
            "",
        ])
        shown = open_threads[:10] or threads[:10]
        if shown:
            lines.append("Top cached threads:")
            lines.append("")
            lines.extend(item_line(t) for t in shown)
            lines.append("")
        else:
            lines.append("No cached threads returned.\n")

    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
