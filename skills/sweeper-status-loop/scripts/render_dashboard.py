#!/usr/bin/env python3
"""Render a simple sweeper README/STATUS dashboard from markdown item records."""
from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FIELD_RE = re.compile(r"^- (?P<key>[^:]+):\s*(?P<value>.*)$")


def parse_record(path: Path) -> dict:
    data = {
        "path": path,
        "title": path.stem,
        "status": "unknown",
        "proposed_action": "unknown",
        "confidence": "unknown",
        "source_id": path.stem,
    }
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        if line.startswith("# ") and data["title"] == path.stem:
            data["title"] = line[2:].strip()
        m = FIELD_RE.match(line.strip())
        if not m:
            continue
        key = m.group("key").lower().strip().replace(" ", "_")
        value = m.group("value").strip()
        if key in {"source_id", "status", "proposed_action", "confidence"}:
            data[key] = value
    return data


def render(items: list[dict], title: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_counts = Counter(item["status"] for item in items)
    action_counts = Counter(item["proposed_action"] for item in items)
    needs_human = sum(1 for item in items if item["status"] in {"blocked", "needs_human"} or item["confidence"] == "low")
    proposed = sum(1 for item in items if item["status"] == "proposed_action")
    safe_apply = sum(1 for item in items if item["status"] == "proposed_action" and item["confidence"] == "high")
    state = "review_ready" if proposed else "scan_only"
    if needs_human:
        state = "blocked" if needs_human == len(items) and items else "review_ready"

    lines = [
        f"# {title}",
        "",
        f"Last updated: {now}",
        f"State: {state}",
        "",
        "## Decision card",
        f"- Items scanned: {len(items)}",
        f"- Proposed actions: {proposed}",
        f"- Safe to apply now: {safe_apply}",
        f"- Needs human review: {needs_human}",
        f"- Blockers: {status_counts.get('blocked', 0)}",
        "",
        "## Recommended next action",
        recommended_next_action(items, proposed, safe_apply, needs_human),
        "",
        "## Metrics",
        "| Metric | Count |",
        "|---|---:|",
        f"| Open/source items | {len(items)} |",
        f"| Reviewed items | {len(items)} |",
        f"| Proposed apply | {proposed} |",
        f"| Safe high-confidence apply | {safe_apply} |",
        f"| Blocked/ambiguous | {needs_human} |",
        "",
        "## Status breakdown",
        "| Status | Count |",
        "|---|---:|",
    ]
    for key, count in sorted(status_counts.items()):
        lines.append(f"| {key} | {count} |")
    if not status_counts:
        lines.append("| none | 0 |")

    lines.extend([
        "",
        "## Proposed action breakdown",
        "| Action | Count |",
        "|---|---:|",
    ])
    for key, count in sorted(action_counts.items()):
        lines.append(f"| {key} | {count} |")
    if not action_counts:
        lines.append("| none | 0 |")

    lines.extend([
        "",
        "## Recent items",
        "| Item | Outcome | Confidence | Record |",
        "|---|---|---|---|",
    ])
    for item in items[:25]:
        record = item["path"].as_posix()
        title_text = item["title"].replace("|", "\\|")
        lines.append(f"| {title_text} | {item['proposed_action']} | {item['confidence']} | [{item['path'].name}]({record}) |")
    if not items:
        lines.append("| none | none | none | n/a |")
    lines.append("")
    return "\n".join(lines)


def recommended_next_action(items: list[dict], proposed: int, safe_apply: int, needs_human: int) -> str:
    if not items:
        return "Run a scan and generate item records."
    if needs_human:
        return "Review blocked or low-confidence items before applying changes."
    if safe_apply:
        return "Review the high-confidence proposed actions and approve a small apply batch."
    if proposed:
        return "Review proposed actions; none are marked high-confidence safe-apply yet."
    return "No apply action needed; keep monitoring."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True, help="Directory containing item markdown records")
    parser.add_argument("--output", required=True, help="Dashboard markdown output path")
    parser.add_argument("--title", default="Sweeper Status", help="Dashboard title")
    args = parser.parse_args()

    item_dir = Path(args.items)
    if not item_dir.exists():
        raise SystemExit(f"items directory does not exist: {item_dir}")
    items = [parse_record(p) for p in sorted(item_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(items, args.title), encoding="utf-8")
    print(f"Wrote {output} from {len(items)} item record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
