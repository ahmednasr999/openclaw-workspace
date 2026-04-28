#!/usr/bin/env python3
"""Check known OpenClaw runtime patches that can be overwritten by updates.

This is intended for post-update verification. It does not modify files.
"""
from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

CHECKS = [
    {
        "name": "session-resume fallback prefix suppressed",
        "mode": "absent",
        "needle": "Automatic session resume failed, so sending the status directly.",
        "paths": [
            Path("/usr/lib/node_modules/openclaw/dist"),
            Path("/root/openclaw/dist"),
        ],
        "alert": (
            "OpenClaw runtime contains the session-resume fallback prefix again. "
            "Reapply the known patch or use the upstream/source fix."
        ),
    },
    {
        "name": "active-memory direct FTS live-reply patch present",
        "mode": "present",
        "needle": "directFts=1",
        "paths": [
            Path("/usr/lib/node_modules/openclaw/dist/extensions/active-memory/index.js"),
        ],
        "alert": (
            "Active-memory direct FTS patch is missing. Do not enable semantic/vector "
            "active-memory in live Telegram replies until isolated tests prove it is fast."
        ),
    },
]


def iter_files(path: Path):
    if path.is_file():
        yield path
    elif path.is_dir():
        yield from path.rglob("*.js")


def check_runtime_context_plain_header_smoke(failures: list[str]) -> None:
    dist = Path("/usr/lib/node_modules/openclaw/dist")
    internal_candidates = sorted(dist.glob("internal-runtime-context-*.js"))
    sanitizer_candidates = sorted(dist.glob("sanitize-user-facing-text-*.js"))
    runtime_prompt_candidates = sorted(dist.glob("runtime-context-prompt-*.js"))
    if not runtime_prompt_candidates:
        failures.append("FAIL: runtime-context custom-message queue disabled\nruntime-context-prompt dist file missing")
    else:
        runtime_prompt_text = runtime_prompt_candidates[0].read_text(errors="ignore")
        if "Do not queue runtime-context as a custom message" not in runtime_prompt_text:
            failures.append("FAIL: runtime-context custom-message queue disabled\nHidden runtime-context custom_message queue is enabled again.")
        else:
            print("OK: runtime-context custom-message queue disabled")

    if not internal_candidates:
        failures.append("FAIL: runtime-context plain-header leak stripper present\ninternal-runtime-context dist file missing")
        return
    internal_text = internal_candidates[0].read_text(errors="ignore")
    if "findNextPublicReplyStart" not in internal_text:
        failures.append("FAIL: runtime-context plain-header leak stripper present\nPlain-header leak stripper is missing; runtime context can leak before assistant replies.")
    else:
        print("OK: runtime-context plain-header leak stripper present")
    if not sanitizer_candidates:
        failures.append("FAIL: runtime-context plain-header sanitizer smoke\nsanitize-user-facing-text dist file missing")
        return
    sanitizer = sanitizer_candidates[0]
    node_script = f"""
import {{ u as sanitizeUserFacingText }} from {json.dumps(str(sanitizer))};
const leak = `OpenClaw runtime context for the immediately preceding user message.\nThis context is runtime-generated, not user-authored. Keep internal details private.\n\n<composio>secret</composio>\nNo. The update is done, but the leak is not fixed.`;
const clean = sanitizeUserFacingText(leak);
if (clean !== 'No. The update is done, but the leak is not fixed.') {{
  console.error(JSON.stringify({{clean}}));
  process.exit(1);
}}
"""
    smoke = subprocess.run(["node", "--input-type=module", "-e", node_script], text=True, capture_output=True)
    if smoke.returncode != 0:
        failures.append("FAIL: runtime-context plain-header sanitizer smoke\n" + (smoke.stderr or smoke.stdout).strip())
    else:
        print("OK: runtime-context plain-header sanitizer smoke passed")


def main() -> int:
    failures: list[str] = []
    for check in CHECKS:
        matches: list[str] = []
        needle = check["needle"]
        for root in check["paths"]:
            for file_path in iter_files(root):
                try:
                    text = file_path.read_text(errors="ignore")
                except OSError:
                    continue
                if needle in text:
                    for line_no, line in enumerate(text.splitlines(), 1):
                        if needle in line:
                            matches.append(f"{file_path}:{line_no}: {line.strip()}")
        mode = check.get("mode", "absent")
        if mode == "absent":
            if matches:
                failures.append(
                    f"FAIL: {check['name']}\n{check['alert']}\n" + "\n".join(matches)
                )
            else:
                print(f"OK: {check['name']}")
        elif mode == "present":
            if matches:
                print(f"OK: {check['name']}")
            else:
                failures.append(f"FAIL: {check['name']}\n{check['alert']}")
        else:
            failures.append(f"FAIL: {check['name']}\nUnknown check mode: {mode}")


    check_runtime_context_plain_header_smoke(failures)

    if failures:
        print("\n\n".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
