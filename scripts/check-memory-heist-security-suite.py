#!/usr/bin/env python3
"""Fail-closed verifier for the Memory Heist 19-test security baseline."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


WORKSPACE = Path("/root/.openclaw/workspace")
TEST_FILES = (
    WORKSPACE / "plugins/memory-heist-guard/test.mjs",
    WORKSPACE / "labs/gpt-red-pilot/pilot.test.mjs",
)
EXPECTED_TESTS = 19
EXPECTED_HOOKS = {"message_received", "before_tool_call", "after_tool_call", "agent_end"}


def tap_count(output: str, label: str) -> int | None:
    matches = re.findall(rf"^# {re.escape(label)} (\d+)\s*$", output, flags=re.MULTILINE)
    return int(matches[-1]) if matches else None


def parse_json_output(output: str) -> object:
    decoder = json.JSONDecoder()
    for index, character in enumerate(output):
        if character not in "{[":
            continue
        try:
            value, _end = decoder.raw_decode(output[index:])
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError("no JSON object or array found")


def runtime_contract(timeout: int) -> dict[str, object]:
    command = ["openclaw", "plugins", "inspect", "memory-heist-guard", "--runtime", "--json"]
    try:
        completed = subprocess.run(
            command,
            cwd=WORKSPACE,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "reason": f"runtime inspection timed out after {timeout}s"}

    output = completed.stdout + completed.stderr
    try:
        data = parse_json_output(output)
    except ValueError as exc:
        return {"ok": False, "reason": str(exc), "output": output[-4000:]}
    if not isinstance(data, dict):
        return {"ok": False, "reason": "runtime inspection did not return an object"}

    plugin = data.get("plugin") if isinstance(data.get("plugin"), dict) else {}
    hooks = {
        str(item.get("name"))
        for item in data.get("typedHooks") or []
        if isinstance(item, dict) and item.get("name")
    }
    diagnostics = data.get("diagnostics") if isinstance(data.get("diagnostics"), list) else []
    expected_source = (WORKSPACE / "plugins/memory-heist-guard/index.js").resolve()
    inspected_source_raw = plugin.get("source")
    inspected_source = (
        Path(inspected_source_raw).resolve()
        if isinstance(inspected_source_raw, str) and inspected_source_raw
        else None
    )
    source_version = json.loads((WORKSPACE / "plugins/memory-heist-guard/package.json").read_text()).get("version")
    ok = (
        completed.returncode == 0
        and plugin.get("status") == "loaded"
        and plugin.get("activated") is True
        and inspected_source == expected_source
        and plugin.get("version") == source_version
        and EXPECTED_HOOKS.issubset(hooks)
        and not diagnostics
    )
    return {
        "ok": ok,
        "reason": "four-hook runtime contract passed" if ok else "four-hook runtime contract failed",
        "sourceVersion": source_version,
        "runtimeVersion": plugin.get("version"),
        "expectedSource": str(expected_source),
        "inspectedSource": str(inspected_source) if inspected_source else None,
        "sourceMatches": inspected_source == expected_source,
        "hookCount": plugin.get("hookCount"),
        "hooks": sorted(hooks),
        "missingHooks": sorted(EXPECTED_HOOKS - hooks),
        "diagnostics": diagnostics,
    }


def run_suite(timeout: int, require_runtime_contract: bool = False) -> dict[str, object]:
    missing = [str(path) for path in TEST_FILES if not path.is_file()]
    if missing:
        return {
            "ok": False,
            "reason": "required test file missing",
            "missing": missing,
            "expectedTests": EXPECTED_TESTS,
        }

    command = ["node", "--test", *(str(path) for path in TEST_FILES)]
    try:
        completed = subprocess.run(
            command,
            cwd=WORKSPACE,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        output = "\n".join(part for part in [exc.stdout, exc.stderr] if isinstance(part, str))
        return {
            "ok": False,
            "reason": f"security suite timed out after {timeout}s",
            "command": command,
            "output": output[-4000:],
            "expectedTests": EXPECTED_TESTS,
        }

    output = completed.stdout + completed.stderr
    tests = tap_count(output, "tests")
    passed = tap_count(output, "pass")
    failed = tap_count(output, "fail")
    ok = (
        completed.returncode == 0
        and tests == EXPECTED_TESTS
        and passed == EXPECTED_TESTS
        and failed == 0
    )
    result = {
        "ok": ok,
        "reason": "19/19 security baseline passed" if ok else "security baseline did not pass exactly 19/19",
        "command": command,
        "returnCode": completed.returncode,
        "expectedTests": EXPECTED_TESTS,
        "tests": tests,
        "passed": passed,
        "failed": failed,
        "output": output[-4000:] if not ok else "",
    }
    if require_runtime_contract:
        contract = runtime_contract(timeout)
        result["runtimeContract"] = contract
        result["ok"] = bool(result["ok"] and contract["ok"])
        if not contract["ok"]:
            result["reason"] = "source tests passed but runtime hook contract failed"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable evidence")
    parser.add_argument(
        "--require-runtime-contract",
        action="store_true",
        help="also require all four hooks to activate without diagnostics",
    )
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    result = run_suite(max(1, args.timeout), require_runtime_contract=args.require_runtime_contract)
    if args.json:
        print(json.dumps(result, indent=2))
    elif result["ok"]:
        print("PASS: Memory Heist security suite 19/19")
    else:
        print(f"FAIL: {result['reason']}", file=sys.stderr)
        if result.get("output"):
            print(result["output"], file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
