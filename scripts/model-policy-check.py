#!/usr/bin/env python3
"""Fail if active runtime paths drift away from Ahmed's GPT-5.5 model policy."""

from pathlib import Path
import json
import re
import sys

APPROVED_MODEL = "openai-codex/gpt-5.5"
APPROVED_RUNTIME_MODELS = {"openai/gpt-5.5", APPROVED_MODEL}

ROOTS = [
    Path("/root/.openclaw/workspace/scripts"),
    Path("/root/.openclaw/workspace-jobzoom/scripts"),
]

CRITICAL_FILES = {
    Path("/root/.openclaw/openclaw.json"),
    Path("/root/.openclaw/workspace/config/model-router.json"),
    Path("/root/.openclaw/workspace-hr/config/model-router.json"),
    Path("/root/.openclaw/workspace-cto/config/model-router.json"),
    Path("/root/.openclaw/workspace-cmo/config/model-router.json"),
    Path("/root/.openclaw/workspace/scripts/auto-cv-builder.py"),
    Path("/root/.openclaw/workspace/scripts/hr-agent.py"),
    Path("/root/.openclaw/workspace/scripts/jobs-review.py"),
    Path("/root/.openclaw/workspace/scripts/jobs-coverletter-autogen.py"),
    Path("/root/.openclaw/workspace/scripts/jobs-interview-prep.py"),
    Path("/root/.openclaw/workspace/scripts/jobs-sonnet-verify.py"),
    Path("/root/.openclaw/workspace/scripts/pipeline-healer.py"),
    Path("/root/.openclaw/workspace/scripts/comment-radar-agent.py"),
    Path("/root/.openclaw/workspace/scripts/youtube-intel.py"),
    Path("/root/.openclaw/workspace/scripts/outreach-agent.py"),
    Path("/root/.openclaw/workspace/scripts/email-agent.py"),
    Path("/root/.openclaw/workspace-jobzoom/scripts/daily_run.py"),
    Path("/root/.openclaw/workspace-jobzoom/scripts/cv_template_engine.py"),
}

FORBIDDEN = re.compile(
    r"openai-codex/gpt-5\.4|anthropic/claude|claude-(?:opus|sonnet)|"
    r"minimax-portal|MiniMax-M|moonshot/kimi|Kimi K",
    re.IGNORECASE,
)

CONFIG_RULES = {
    Path("/root/.openclaw/openclaw.json"): [
        ('"summaryModel": "openai-codex/gpt-5.5"', "lossless-claw summaryModel must use GPT-5.5"),
        ('"minimax": {\n        "enabled": false', "MiniMax plugin must stay disabled unless Ahmed explicitly re-enables it"),
    ],
}

FORBIDDEN_SCAN_EXEMPT = {
    Path("/root/.openclaw/openclaw.json"),
}


def check_openclaw_config(path: Path, text: str, problems: list[str]) -> None:
    if path != Path("/root/.openclaw/openclaw.json"):
        return

    try:
        config = json.loads(text)
    except json.JSONDecodeError as exc:
        problems.append(f"{path}: invalid JSON: {exc}")
        return

    lossless = config.get("plugins", {}).get("entries", {}).get("lossless-claw", {})
    summary_model = lossless.get("config", {}).get("summaryModel")
    if summary_model != APPROVED_MODEL:
        problems.append(f"{path}: lossless-claw summaryModel is {summary_model!r}, expected {APPROVED_MODEL}")

    minimax = config.get("plugins", {}).get("entries", {}).get("minimax", {})
    if minimax.get("enabled") is not False:
        problems.append(f"{path}: MiniMax plugin is enabled; expected disabled unless Ahmed explicitly re-enables it")

    model_by_channel = config.get("channels", {}).get("modelByChannel", {})
    for surface, mapping in model_by_channel.items():
        if not isinstance(mapping, dict):
            problems.append(f"{path}: channels.modelByChannel.{surface} must be an object")
            continue
        for channel, model in mapping.items():
            if model not in APPROVED_RUNTIME_MODELS:
                problems.append(
                    f"{path}: channels.modelByChannel.{surface}.{channel} uses {model!r}, expected GPT-5.5"
                )


def main() -> int:
    problems = []
    for path in sorted(CRITICAL_FILES):
        if not path.exists():
            problems.append(f"missing critical file: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if APPROVED_MODEL not in text:
            problems.append(f"{path}: approved model literal missing")
        for expected, description in CONFIG_RULES.get(path, []):
            if expected not in text:
                problems.append(f"{path}: {description}")
        check_openclaw_config(path, text, problems)
        if path in FORBIDDEN_SCAN_EXEMPT:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if FORBIDDEN.search(line):
                problems.append(f"{path}:{line_no}: forbidden model reference: {line.strip()[:160]}")

    if problems:
        print("MODEL POLICY CHECK FAILED")
        for item in problems:
            print(f"- {item}")
        return 1

    print(f"MODEL POLICY CHECK OK: all critical scripts use {APPROVED_MODEL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
