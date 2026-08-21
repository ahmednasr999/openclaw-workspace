#!/usr/bin/env python3
"""Measure OpenClaw prompt overhead without reading conversation bodies."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


BOOTSTRAP_FILES = (
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "IDENTITY.md",
    "USER.md",
    "MEMORY.md",
)

RULE_TOPICS = {
    "approval": re.compile(r"\b(?:approv|pre-approved|ask first|ask before)\w*\b", re.I),
    "model": re.compile(r"\b(?:model|GPT-5\.6|reasoning effort)\b", re.I),
    "verification": re.compile(r"\b(?:verify|verification|evidence|proof)\w*\b", re.I),
    "writing": re.compile(r"\b(?:writing standard|voice|style|user-facing)\b", re.I),
    "memory": re.compile(r"\b(?:memory|remember|learning)\w*\b", re.I),
    "linkedin": re.compile(r"\bLinkedIn\b", re.I),
    "job_search": re.compile(r"\b(?:JobZoom|ATS|CV|job search|application)\b", re.I),
}


@dataclass(frozen=True)
class SessionSample:
    lane: str
    updated_at: int
    total_tokens: int
    input_tokens: int
    output_tokens: int
    compactions: int


def token_estimate(chars: int) -> int:
    return math.ceil(chars / 4)


def percentile(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = math.ceil(fraction * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def summarize(values: Iterable[int]) -> dict[str, int | float]:
    items = list(values)
    if not items:
        return {"count": 0, "mean": 0, "median": 0, "p90": 0, "max": 0}
    return {
        "count": len(items),
        "mean": round(statistics.fmean(items), 1),
        "median": round(statistics.median(items), 1),
        "p90": percentile(items, 0.9),
        "max": max(items),
    }


def lane_from_key(key: str) -> str:
    parts = key.split(":")
    agent = parts[1] if len(parts) > 1 else "unknown"
    kind = parts[2] if len(parts) > 2 else "unknown"
    subtype = parts[3] if kind in {"telegram", "slack", "discord"} and len(parts) > 3 else ""
    return "/".join(part for part in (agent, kind, subtype) if part)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def find_sessions(openclaw_root: Path, sample_size: int) -> list[SessionSample]:
    samples: list[SessionSample] = []
    for registry in sorted((openclaw_root / "agents").glob("*/sessions/sessions.json")):
        try:
            payload = load_json(registry)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if not isinstance(value, dict) or ":cron:" in key or ":subagent:" in key:
                continue
            total_tokens = int(value.get("totalTokens") or 0)
            input_tokens = int(value.get("inputTokens") or 0)
            if total_tokens <= 0 and input_tokens <= 0:
                continue
            samples.append(
                SessionSample(
                    lane=lane_from_key(key),
                    updated_at=int(value.get("updatedAt") or 0),
                    total_tokens=total_tokens,
                    input_tokens=input_tokens,
                    output_tokens=int(value.get("outputTokens") or 0),
                    compactions=int(value.get("compactionCount") or 0),
                )
            )
    return sorted(samples, key=lambda item: item.updated_at, reverse=True)[:sample_size]


def newest_prompt_report(openclaw_root: Path) -> dict[str, Any]:
    preferred: list[tuple[int, dict[str, Any]]] = []
    fallback: list[tuple[int, dict[str, Any]]] = []
    for registry in sorted((openclaw_root / "agents").glob("*/sessions/sessions.json")):
        try:
            payload = load_json(registry)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if not isinstance(value, dict):
                continue
            report = value.get("systemPromptReport")
            if isinstance(report, dict):
                candidate = (int(report.get("generatedAt") or 0), report)
                fallback.append(candidate)
                if key.startswith("agent:main:telegram:direct:"):
                    preferred.append(candidate)
    candidates = preferred or fallback
    return max(candidates, default=(0, {}), key=lambda item: item[0])[1]


def bootstrap_metrics(workspace: Path) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    rows: list[dict[str, Any]] = []
    topic_files = {topic: [] for topic in RULE_TOPICS}
    for name in BOOTSTRAP_FILES:
        path = workspace / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        rows.append(
            {
                "name": name,
                "chars": len(text),
                "lines": len(text.splitlines()),
                "estimated_tokens": token_estimate(len(text)),
            }
        )
        for topic, pattern in RULE_TOPICS.items():
            if pattern.search(text):
                topic_files[topic].append(name)
    return rows, topic_files


def lossless_config(openclaw_root: Path) -> dict[str, Any]:
    config_path = openclaw_root / "openclaw.json"
    try:
        config = load_json(config_path)
    except (OSError, json.JSONDecodeError):
        return {}
    entries = (((config.get("plugins") or {}).get("entries") or {}))
    lossless = entries.get("lossless-claw") or {}
    plugin_config = lossless.get("config") or {}
    return {
        key: plugin_config.get(key)
        for key in (
            "freshTailCount",
            "freshTailMaxTokens",
            "summaryPrefixTargetTokens",
            "contextThreshold",
        )
        if key in plugin_config
    }


def build_report(workspace: Path, openclaw_root: Path, sample_size: int) -> dict[str, Any]:
    bootstrap, topic_files = bootstrap_metrics(workspace)
    sessions = find_sessions(openclaw_root, sample_size)
    prompt = newest_prompt_report(openclaw_root)
    skills = prompt.get("skills") or {}
    injected = prompt.get("injectedWorkspaceFiles") or []
    system_prompt = prompt.get("systemPrompt") or {}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "workspace": str(workspace),
            "session_sample_size": len(sessions),
            "message_bodies_read": False,
        },
        "bootstrap": {
            "files": bootstrap,
            "total_chars": sum(row["chars"] for row in bootstrap),
            "estimated_tokens": sum(row["estimated_tokens"] for row in bootstrap),
            "topic_ownership_candidates": topic_files,
        },
        "latest_prompt": {
            "generated_at": prompt.get("generatedAt"),
            "system_prompt_chars": int(system_prompt.get("chars") or 0),
            "workspace_injected_chars": sum(int(row.get("injectedChars") or 0) for row in injected),
            "skill_count": len(skills.get("entries") or []),
            "skill_prompt_chars": int(skills.get("promptChars") or 0),
            "tool_schema_chars": int(((prompt.get("tools") or {}).get("schemaChars") or 0)),
        },
        "sessions": {
            "total_tokens": summarize(sample.total_tokens for sample in sessions),
            "input_tokens": summarize(sample.input_tokens for sample in sessions),
            "output_tokens": summarize(sample.output_tokens for sample in sessions),
            "compactions": summarize(sample.compactions for sample in sessions),
            "lane_counts": {
                lane: sum(1 for sample in sessions if sample.lane == lane)
                for lane in sorted({sample.lane for sample in sessions})
            },
        },
        "lossless_claw": lossless_config(openclaw_root),
    }


def markdown(report: dict[str, Any]) -> str:
    prompt = report["latest_prompt"]
    sessions = report["sessions"]
    bootstrap = report["bootstrap"]
    lines = [
        "# Prompt Context Audit",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Baseline",
        "",
        f"- Session sample: {report['scope']['session_sample_size']} recent non-cron sessions; message bodies were not read.",
        f"- Latest system prompt: {prompt['system_prompt_chars']:,} characters.",
        f"- Injected workspace files: {prompt['workspace_injected_chars']:,} characters.",
        f"- Skill catalog: {prompt['skill_count']} skills, {prompt['skill_prompt_chars']:,} characters.",
        f"- Direct tool schemas: {prompt['tool_schema_chars']:,} characters.",
        f"- Bootstrap source total: {bootstrap['total_chars']:,} characters (~{bootstrap['estimated_tokens']:,} tokens).",
        "",
        "## Recent Session Distribution",
        "",
        "| Metric | Mean | Median | P90 | Max |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, key in (
        ("Active context tokens", "total_tokens"),
        ("Input tokens", "input_tokens"),
        ("Output tokens", "output_tokens"),
        ("Compactions", "compactions"),
    ):
        row = sessions[key]
        lines.append(f"| {label} | {row['mean']:,.1f} | {row['median']:,.1f} | {row['p90']:,} | {row['max']:,} |")
    lines.extend(["", "## Lane Mix", ""])
    for lane, count in sessions["lane_counts"].items():
        lines.append(f"- `{lane}`: {count}")
    lines.extend(["", "## Rule-Ownership Candidates", ""])
    for topic, files in bootstrap["topic_ownership_candidates"].items():
        if len(files) > 1:
            lines.append(f"- `{topic}` appears in {', '.join(files)}.")
    lines.extend(
        [
            "",
            "## Lossless-Claw Context Budget",
            "",
            "```json",
            json.dumps(report["lossless_claw"], indent=2, sort_keys=True),
            "```",
            "",
            "## Interpretation",
            "",
            "- Core-file cleanup improves consistency but cannot deliver the target reduction alone.",
            "- Skill catalog size and lossless-history budgets are the largest controllable prompt surfaces.",
            "- Any reduction to skill visibility or retained history needs representative regression tests before live rollout.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--openclaw-root", type=Path, default=Path("/root/.openclaw"))
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.sample_size <= 100:
        raise SystemExit("--sample-size must be between 1 and 100")
    report = build_report(args.workspace.resolve(), args.openclaw_root.resolve(), args.sample_size)
    json_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    markdown_text = markdown(report)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json_text, encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown_text, encoding="utf-8")
    if not args.json_output and not args.markdown_output:
        print(json_text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
