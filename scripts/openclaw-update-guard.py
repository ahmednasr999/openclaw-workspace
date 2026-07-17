#!/usr/bin/env python3
"""OpenClaw update guard.

Read-only guardrail for OpenClaw update/restart/config-change windows.
It does not update, restart, or edit config. It prints PASS/FAIL/WARN checks
with evidence so a human/agent can stop before repeating known failure modes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_MODEL = "openai/gpt-5.6-sol"
LEGACY_MODEL = "openai/gpt-5.5"
SANDBOX_IMAGE = "openclaw-sandbox:bookworm-slim"
OPENCLAW_CONFIG = Path("/root/.openclaw/openclaw.json")
WORKSPACE = Path("/root/.openclaw/workspace")
MODEL_ROUTER = WORKSPACE / "config/model-router.json"
REPORT_DIR = WORKSPACE / "reports"
OPENCLAW_INSTALL = Path("/usr/lib/node_modules/openclaw")
MEMORY_HEIST_CHECKER = WORKSPACE / "scripts/check-memory-heist-security-suite.py"
INSTALL_SIZE_WARN_MB = 850
DEPENDENCY_COUNT_WARN = 450
NATIVE_OPTIONAL_WARN = 18
TURN_COLD_WARN_SECONDS = 30.0
TURN_WARM_WARN_SECONDS = 20.0
REQUIRED_PLUGINS = [
    "lossless-claw",
    "telegram",
    "openai",
    "file-transfer",
    "memory-core",
    "memory-wiki",
    "memory-heist-guard",
]
LOSSLESS_TOOLS = {"lcm_grep", "lcm_describe", "lcm_expand", "lcm_expand_query"}


@dataclass
class Check:
    name: str
    status: str
    detail: str
    evidence: str = ""


class Guard:
    def __init__(self, timeout: int = 20, deep: bool = False, measure_turn_latency: bool = False):
        self.timeout = timeout
        self.deep = deep
        self.measure_turn_latency = measure_turn_latency
        self.checks: list[Check] = []
        self.raw: dict[str, Any] = {}

    def add(self, name: str, status: str, detail: str, evidence: str = "") -> None:
        self.checks.append(Check(name, status, detail, evidence.strip()))

    def run_cmd(self, name: str, args: list[str], timeout: int | None = None) -> subprocess.CompletedProcess[str] | None:
        t = timeout or self.timeout
        try:
            cp = subprocess.run(args, text=True, capture_output=True, timeout=t)
            self.raw[name] = {
                "args": args,
                "returncode": cp.returncode,
                "stdout": cp.stdout,
                "stderr": cp.stderr,
            }
            return cp
        except subprocess.TimeoutExpired as e:
            out = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode(errors="replace") if e.stdout else "")
            err = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode(errors="replace") if e.stderr else "")
            self.raw[name] = {"args": args, "timeout": t, "stdout": out, "stderr": err}
            status = "WARN" if name in {"status usage json", "openclaw status deep"} else "FAIL"
            self.add(name, status, f"timed out after {t}s", (out + "\n" + err)[-1000:])
            return None
        except Exception as e:
            self.raw[name] = {"args": args, "error": str(e)}
            self.add(name, "FAIL", f"command failed to start: {e}")
            return None

    @staticmethod
    def mixed_json(text: str) -> Any:
        starts = [(i, ch) for i, ch in enumerate(text) if ch in "{["]
        for start, ch in starts:
            close = "}" if ch == "{" else "]"
            depth = 0
            in_str = False
            esc = False
            for pos in range(start, len(text)):
                c = text[pos]
                if in_str:
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == "\"":
                        in_str = False
                    continue
                if c == "\"":
                    in_str = True
                elif c == ch:
                    depth += 1
                elif c == close:
                    depth -= 1
                    if depth == 0:
                        candidate = text[start:pos + 1]
                        try:
                            return json.loads(candidate)
                        except Exception:
                            break
        raise ValueError("no parseable JSON object/array found")

    def check_disk(self) -> None:
        usage = shutil.disk_usage("/tmp")
        free_gb = usage.free / (1024**3)
        if free_gb >= 2:
            self.add("tmp disk", "PASS", f"/tmp has {free_gb:.1f} GB free")
        else:
            self.add("tmp disk", "FAIL", f"/tmp has only {free_gb:.1f} GB free, need >=2 GB")

    def check_version(self) -> None:
        cp = self.run_cmd("openclaw version", ["openclaw", "--version"])
        if not cp:
            return
        text = (cp.stdout + cp.stderr).strip()
        if cp.returncode == 0 and "OpenClaw" in text:
            self.add("openclaw version", "PASS", text)
        else:
            self.add("openclaw version", "FAIL", f"exit {cp.returncode}", text)

    def count_node_modules_packages(self, node_modules: Path) -> int | None:
        if not node_modules.exists():
            return None
        count = 0
        for child in node_modules.iterdir():
            if child.name.startswith("."):
                continue
            if child.name.startswith("@") and child.is_dir():
                count += sum(1 for pkg in child.iterdir() if (pkg / "package.json").exists())
            elif (child / "package.json").exists():
                count += 1
        return count

    def count_native_optional_packages(self, node_modules: Path) -> tuple[int, list[str]]:
        scoped_patterns = {
            "@rollup": ("rollup-",),
            "@tailwindcss": ("oxide-",),
            "@esbuild": ("",),
            "@img": ("sharp-",),
            "@swc": ("core-",),
        }
        matches: list[str] = []
        for scope, prefixes in scoped_patterns.items():
            scope_dir = node_modules / scope
            if not scope_dir.exists():
                continue
            for pkg in scope_dir.iterdir():
                if not pkg.is_dir():
                    continue
                if any(pkg.name.startswith(prefix) for prefix in prefixes):
                    matches.append(f"{scope}/{pkg.name}")
        return len(matches), sorted(matches)

    def check_release_footprint(self) -> None:
        if not OPENCLAW_INSTALL.exists():
            self.add("release footprint", "FAIL", f"OpenClaw install path missing: {OPENCLAW_INSTALL}")
            return

        size_mb: int | None = None
        cp = self.run_cmd("openclaw install size", ["du", "-sm", str(OPENCLAW_INSTALL)])
        if cp and cp.returncode == 0:
            try:
                size_mb = int((cp.stdout.strip().split() or ["0"])[0])
            except Exception:
                size_mb = None

        node_modules = OPENCLAW_INSTALL / "node_modules"
        dep_count = self.count_node_modules_packages(node_modules)
        native_count, native_matches = self.count_native_optional_packages(node_modules)
        nested_duplicate = OPENCLAW_INSTALL / "node_modules" / "openclaw" / "node_modules"
        nested_exists = nested_duplicate.exists()

        evidence = json.dumps(
            {
                "installPath": str(OPENCLAW_INSTALL),
                "sizeMb": size_mb,
                "dependencyCountDirect": dep_count,
                "nativeOptionalCount": native_count,
                "nativeOptionalSample": native_matches[:20],
                "nestedDuplicateTree": str(nested_duplicate),
                "nestedDuplicateTreeExists": nested_exists,
                "thresholds": {
                    "sizeWarnMb": INSTALL_SIZE_WARN_MB,
                    "dependencyCountWarn": DEPENDENCY_COUNT_WARN,
                    "nativeOptionalWarn": NATIVE_OPTIONAL_WARN,
                },
            },
            ensure_ascii=False,
        )

        if nested_exists:
            self.add("release footprint", "FAIL", "duplicate nested OpenClaw dependency tree detected", evidence)
            return

        warnings = []
        if size_mb is not None and size_mb > INSTALL_SIZE_WARN_MB:
            warnings.append(f"install size {size_mb} MB exceeds {INSTALL_SIZE_WARN_MB} MB")
        if dep_count is not None and dep_count > DEPENDENCY_COUNT_WARN:
            warnings.append(f"direct dependency count {dep_count} exceeds {DEPENDENCY_COUNT_WARN}")
        if native_count > NATIVE_OPTIONAL_WARN:
            warnings.append(f"native optional package count {native_count} exceeds {NATIVE_OPTIONAL_WARN}")

        if warnings:
            self.add("release footprint", "WARN", "; ".join(warnings), evidence)
        else:
            self.add("release footprint", "PASS", "install footprint and dependency shape are within guard thresholds", evidence)

    def check_runtime_llm_complete(self) -> None:
        cp = self.run_cmd("runtime llm complete", ["openclaw", "plugins", "inspect", "lossless-claw", "--runtime", "--json"], timeout=max(self.timeout, 30))
        if not cp:
            return
        text = cp.stdout + cp.stderr
        if cp.returncode != 0:
            self.add("runtime.llm.complete", "WARN", f"could not inspect lossless-claw runtime, exit {cp.returncode}", text[-1500:])
            return
        if "runtime.llm.complete is unavailable" in text:
            self.add("runtime.llm.complete", "WARN", "Plugin SDK runtime LLM support is unavailable in this build", "LCM cannot use plugin-side runtime LLM completion until OpenClaw includes that support.")
        elif "runtime.llm.complete" in text and "unavailable" not in text.lower():
            self.add("runtime.llm.complete", "PASS", "runtime LLM completion appears available to plugin runtime", text[-1000:])
        else:
            self.add("runtime.llm.complete", "WARN", "runtime inspection did not provide explicit runtime.llm.complete evidence", text[-1000:])

    def check_gateway_status(self) -> None:
        cp = self.run_cmd("gateway status", ["openclaw", "gateway", "status", "--deep"], timeout=max(self.timeout, 30))
        if not cp:
            return
        text = cp.stdout + cp.stderr
        bad_needles = ["ERR_MODULE_NOT_FOUND", "Missing API key", "Cannot find module"]
        if cp.returncode != 0:
            self.add("gateway status", "FAIL", f"exit {cp.returncode}", text[-1500:])
        elif any(n in text for n in bad_needles):
            self.add("gateway status", "FAIL", "fatal module/auth error surfaced", "\n".join(l for l in text.splitlines() if any(n in l for n in bad_needles)))
        elif "Connectivity probe: ok" in text or "Gateway:" in text:
            warns = [l for l in text.splitlines() if "warning" in l.lower() or "out of date" in l.lower() or "newer OpenClaw" in l]
            status = "WARN" if warns else "PASS"
            self.add("gateway status", status, "gateway status returned usable output", "\n".join(warns[:8]))
        else:
            self.add("gateway status", "WARN", "status returned but expected gateway markers were not found", text[-1200:])

    def check_gateway_probe(self) -> None:
        cp = self.run_cmd("gateway probe", ["openclaw", "gateway", "probe", "--json"])
        if not cp:
            return
        text = cp.stdout + cp.stderr
        if cp.returncode != 0:
            self.add("gateway probe", "FAIL", f"exit {cp.returncode}", text[-1000:])
            return
        ok = "ok" in text.lower() or "reachable" in text.lower() or "127.0.0.1" in text
        self.add("gateway probe", "PASS" if ok else "WARN", "probe completed" if ok else "probe output unclear", text[-1000:])

    def check_config_validate(self) -> None:
        cp = self.run_cmd("config validate", ["openclaw", "config", "validate"])
        if not cp:
            return
        text = cp.stdout + cp.stderr
        if cp.returncode == 0 and "Config valid" in text:
            self.add("config validate", "PASS", "config validates", text.strip())
        else:
            self.add("config validate", "FAIL", f"exit {cp.returncode}", text[-1200:])

    def check_memory_heist_security_suite(self) -> None:
        cp = self.run_cmd(
            "memory heist security suite",
            [
                sys.executable,
                str(MEMORY_HEIST_CHECKER),
                "--require-runtime-contract",
                "--json",
                "--timeout",
                "60",
            ],
            timeout=max(self.timeout, 70),
        )
        if not cp:
            return
        text = cp.stdout + cp.stderr
        try:
            result = self.mixed_json(text)
        except Exception as exc:
            self.add("memory heist security suite", "FAIL", f"invalid checker output: {exc}", text[-1500:])
            return
        ok = cp.returncode == 0 and result.get("ok") is True
        counts = f"tests={result.get('tests')} pass={result.get('passed')} fail={result.get('failed')}"
        self.add(
            "memory heist security suite",
            "PASS" if ok else "FAIL",
            "mandatory 19/19 security baseline passed" if ok else f"mandatory security baseline failed ({counts})",
            json.dumps(result, ensure_ascii=False)[:1500],
        )

    def check_sandbox_image(self) -> None:
        cp = self.run_cmd("sandbox image", ["docker", "image", "inspect", SANDBOX_IMAGE])
        if not cp:
            return
        text = cp.stdout + cp.stderr
        if cp.returncode == 0 and SANDBOX_IMAGE in text:
            self.add("sandbox image", "PASS", f"Docker image present: {SANDBOX_IMAGE}")
        else:
            self.add(
                "sandbox image",
                "FAIL",
                f"missing Docker image: {SANDBOX_IMAGE}",
                "Rebuild from /usr/lib/node_modules/openclaw/docs/gateway/sandboxing.md, then rerun guard.",
            )

    def check_visible_reply_config(self) -> None:
        data = self.load_json_file(OPENCLAW_CONFIG)
        if data is None:
            return
        messages = data.get("messages") if isinstance(data, dict) else None
        if not isinstance(messages, dict):
            self.add("telegram visible replies", "FAIL", "messages config block missing", str(OPENCLAW_CONFIG))
            return
        direct = messages.get("visibleReplies")
        group = messages.get("groupChat") if isinstance(messages.get("groupChat"), dict) else {}
        group_visible = group.get("visibleReplies")
        evidence = json.dumps(
            {
                "messages.visibleReplies": direct,
                "messages.groupChat.visibleReplies": group_visible,
            },
            ensure_ascii=False,
        )
        if direct == "automatic" and group_visible == "automatic":
            self.add("telegram visible replies", "PASS", "direct DM and group/topic reply modes are visible", evidence)
        else:
            self.add(
                "telegram visible replies",
                "FAIL",
                "expected messages.visibleReplies=automatic and messages.groupChat.visibleReplies=automatic",
                evidence,
            )

    def check_systemd(self) -> None:
        commands = [
            (
                "user",
                [
                    "systemctl",
                    "--user",
                    "show",
                    "openclaw-gateway",
                    "-p",
                    "ExecStart",
                    "-p",
                    "MainPID",
                    "-p",
                    "ExecMainStartTimestamp",
                ],
            ),
            (
                "system",
                [
                    "systemctl",
                    "show",
                    "openclaw-gateway.service",
                    "-p",
                    "ExecStart",
                    "-p",
                    "MainPID",
                    "-p",
                    "ExecMainStartTimestamp",
                    "-p",
                    "ActiveState",
                    "-p",
                    "SubState",
                ],
            ),
        ]
        failures = []
        for scope, cmd in commands:
            cp = self.run_cmd(f"systemd gateway ({scope})", cmd)
            if not cp:
                continue
            text = cp.stdout + cp.stderr
            if cp.returncode != 0:
                failures.append(f"[{scope}] exit {cp.returncode}\n{text.strip()}")
                continue
            pid = re.search(r"MainPID=(\d+)", text)
            exec_ok = "gateway --port 18789" in text and ("/usr/bin/openclaw" in text or "dist/index.js gateway" in text)
            ts_line = next((l for l in text.splitlines() if l.startswith("ExecMainStartTimestamp=")), "")
            start_ok = bool(ts_line and ts_line.strip() != "ExecMainStartTimestamp=" and "n/a" not in ts_line.lower())
            active_ok = "ActiveState=active" in text or scope == "user"
            if pid and pid.group(1) != "0" and exec_ok and start_ok and active_ok:
                self.add("systemd gateway", "PASS", f"{scope} MainPID={pid.group(1)}, ExecStart/start timestamp present", text.strip())
                return
            failures.append(f"[{scope}] missing valid MainPID, ExecStart, active state, or start timestamp\n{text.strip()}")
        self.add("systemd gateway", "FAIL", "no valid user or system gateway service found", "\n\n".join(failures))

    def load_json_file(self, path: Path) -> Any | None:
        try:
            return json.loads(path.read_text())
        except Exception as e:
            self.add(f"read {path.name}", "FAIL", str(e))
            return None

    def iter_strings(self, obj: Any):
        if isinstance(obj, str):
            yield obj
        elif isinstance(obj, dict):
            for v in obj.values():
                yield from self.iter_strings(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from self.iter_strings(v)

    def check_model_refs(self) -> None:
        problems = []
        evidence = []
        for path in [OPENCLAW_CONFIG, MODEL_ROUTER]:
            if not path.exists():
                continue
            data = self.load_json_file(path)
            if data is None:
                continue
            strings = list(self.iter_strings(data))
            bad = sorted(set(s for s in strings if s == LEGACY_MODEL or s.startswith(LEGACY_MODEL)))
            expected_hits = sum(1 for s in strings if s == EXPECTED_MODEL or s.startswith(EXPECTED_MODEL))
            if bad:
                problems.append(f"{path}: contains {bad}")
            evidence.append(f"{path}: expected_hits={expected_hits}, legacy_refs={len(bad)}")
        if problems:
            self.add("model refs", "FAIL", f"legacy provider drift detected, expected {EXPECTED_MODEL}", "\n".join(problems + evidence))
        else:
            self.add("model refs", "PASS", f"no legacy model drift found, expected {EXPECTED_MODEL}", "\n".join(evidence))

    def check_codex_usage(self) -> None:
        cp = self.run_cmd("status usage json", ["openclaw", "status", "--usage", "--json"], timeout=max(self.timeout, 30))
        if not cp:
            return
        text = cp.stdout + cp.stderr
        if cp.returncode != 0:
            # Some versions print warnings/empty usage with 0/odd code; keep as warn unless auth text is fatal.
            status = "FAIL" if "Missing API key" in text or "auth" in text.lower() else "WARN"
            self.add("codex usage", status, f"status usage exit {cp.returncode}", text[-1500:])
            return
        try:
            data = self.mixed_json(text)
            providers = ((data.get("usage") or {}).get("providers") or []) if isinstance(data, dict) else []
            codex = next((p for p in providers if p.get("provider") == "openai-codex"), None)
            if codex and not codex.get("error"):
                self.add("codex usage", "PASS", "openai-codex provider visible without reported error", json.dumps(codex, ensure_ascii=False)[:1500])
            elif codex:
                self.add("codex usage", "FAIL", f"openai-codex error: {codex.get('error')}", json.dumps(codex, ensure_ascii=False)[:1500])
            else:
                self.add("codex usage", "WARN", "openai-codex provider not visible in usage output", text[-1500:])
        except Exception as e:
            # Human output for --usage on 2026.5.5 can be sparse. Missing API key is the real hard fail here.
            if "Missing API key" in text:
                self.add("codex usage", "FAIL", "missing API key surfaced", text[-1500:])
            else:
                self.add("codex usage", "WARN", f"could not parse usage JSON: {e}", text[-1500:])

    def check_plugins(self) -> None:
        cp = self.run_cmd("plugins list", ["openclaw", "plugins", "list", "--verbose", "--json"], timeout=max(self.timeout, 30))
        plugins_seen: set[str] = set()
        if cp and cp.returncode == 0:
            try:
                data = self.mixed_json(cp.stdout + cp.stderr)
                items = data if isinstance(data, list) else data.get("plugins") or data.get("entries") or []
                for item in items:
                    pid = str(item.get("id") or item.get("name") or item.get("plugin") or "")
                    if not pid:
                        continue
                    if pid in REQUIRED_PLUGINS:
                        plugins_seen.add(pid)
                        loaded = (item.get("status") == "loaded") or bool(item.get("activated"))
                        self.add(f"plugin {pid}", "PASS" if loaded else "FAIL", f"enabled={item.get('enabled')} activated={item.get('activated')} status={item.get('status')}")
            except Exception as e:
                self.add("plugins list", "WARN", f"could not parse plugin list JSON: {e}", (cp.stdout + cp.stderr)[-1500:])
        elif cp:
            self.add("plugins list", "FAIL", f"exit {cp.returncode}", (cp.stdout + cp.stderr)[-1500:])
        for missing in sorted(set(REQUIRED_PLUGINS) - plugins_seen):
            self.add(f"plugin {missing}", "WARN", "not found in parsed plugin list, checking inspect may still prove runtime")

        for pid in ["lossless-claw", "file-transfer", "memory-heist-guard"]:
            cp2 = self.run_cmd(f"inspect {pid}", ["openclaw", "plugins", "inspect", pid, "--runtime", "--json"], timeout=max(self.timeout, 30))
            if not cp2:
                continue
            text = cp2.stdout + cp2.stderr
            if cp2.returncode != 0:
                self.add(f"runtime {pid}", "FAIL", f"inspect exit {cp2.returncode}", text[-1500:])
                continue
            if pid == "lossless-claw":
                missing = sorted(t for t in LOSSLESS_TOOLS if t not in text)
                self.add("runtime lossless-claw", "PASS" if not missing else "FAIL", "lossless tool contracts present" if not missing else f"missing {missing}", "tools=" + ",".join(sorted(LOSSLESS_TOOLS - set(missing))))
            if pid == "file-transfer":
                ok = all(t in text for t in ["file_fetch", "file_write", "dir_list", "dir_fetch"])
                self.add("runtime file-transfer", "PASS" if ok else "FAIL", "file-transfer tool contracts present" if ok else "missing one or more file-transfer tools")
            if pid == "memory-heist-guard":
                expected_hooks = {
                    "message_received",
                    "before_tool_call",
                    "after_tool_call",
                    "agent_end",
                }
                try:
                    data = self.mixed_json(text)
                    plugin = data.get("plugin") or {}
                    hooks = {
                        str(item.get("name"))
                        for item in data.get("typedHooks") or []
                        if isinstance(item, dict) and item.get("name")
                    }
                    hook_count = plugin.get("hookCount")
                    ok = (
                        plugin.get("status") == "loaded"
                        and plugin.get("activated") is True
                        and isinstance(hook_count, int)
                        and hook_count >= len(expected_hooks)
                        and expected_hooks.issubset(hooks)
                    )
                    self.add(
                        "runtime memory-heist-guard",
                        "PASS" if ok else "FAIL",
                        f"runtime hookCount={hook_count}; hooks={','.join(sorted(hooks))}",
                        "runtime inspection is authoritative; cold plugin-list snapshots may report hookCount=0",
                    )
                except Exception as exc:
                    self.add("runtime memory-heist-guard", "FAIL", f"could not parse runtime hook evidence: {exc}", text[-1500:])

    def check_turn_latency_optional(self) -> None:
        if not self.measure_turn_latency:
            return
        session_key = "agent:main:update-guard-latency"
        timings: list[dict[str, Any]] = []
        for label in ["cold", "warm"]:
            started = time.monotonic()
            cp = self.run_cmd(
                f"agent turn latency {label}",
                [
                    "openclaw",
                    "agent",
                    "--agent",
                    "main",
                    "--session-key",
                    session_key,
                    "--message",
                    f"Update guard {label} latency probe. Reply with exactly pong.",
                    "--thinking",
                    "minimal",
                    "--timeout",
                    str(max(self.timeout, 90)),
                    "--json",
                ],
                timeout=max(self.timeout, 120),
            )
            elapsed = time.monotonic() - started
            ok = bool(cp and cp.returncode == 0)
            text = (cp.stdout + cp.stderr) if cp else ""
            timings.append({"label": label, "ok": ok, "seconds": round(elapsed, 2), "returncode": cp.returncode if cp else None})
            if not ok:
                self.add(f"agent turn latency {label}", "WARN", f"agent turn probe failed after {elapsed:.1f}s", text[-1500:])
                continue
            threshold = TURN_COLD_WARN_SECONDS if label == "cold" else TURN_WARM_WARN_SECONDS
            status = "PASS" if elapsed <= threshold else "WARN"
            self.add(f"agent turn latency {label}", status, f"{elapsed:.1f}s gateway agent turn, threshold {threshold:.1f}s", text[-1000:])
        self.raw["agent turn latency summary"] = timings

    def check_deep_status_optional(self) -> None:
        if not self.deep:
            return
        cp = self.run_cmd("openclaw status deep", ["openclaw", "status", "--deep"], timeout=max(self.timeout, 45))
        if cp and cp.returncode == 0:
            self.add("openclaw status --deep", "PASS", "deep status completed", (cp.stdout + cp.stderr)[-1000:])
        elif cp:
            self.add("openclaw status --deep", "WARN", f"deep status exit {cp.returncode}", (cp.stdout + cp.stderr)[-1000:])

    def run_all(self) -> None:
        self.check_disk()
        self.check_version()
        self.check_release_footprint()
        self.check_runtime_llm_complete()
        self.check_systemd()
        self.check_config_validate()
        self.check_memory_heist_security_suite()
        self.check_sandbox_image()
        self.check_visible_reply_config()
        self.check_gateway_status()
        self.check_gateway_probe()
        self.check_model_refs()
        self.check_codex_usage()
        self.check_plugins()
        self.check_turn_latency_optional()
        self.check_deep_status_optional()

    def verdict(self) -> str:
        if any(c.status == "FAIL" for c in self.checks):
            return "FAIL"
        if any(c.status == "WARN" for c in self.checks):
            return "WARN"
        return "PASS"

    def render(self) -> str:
        out = []
        out.append(f"OpenClaw Update Guard - {datetime.now(timezone.utc).isoformat()}")
        out.append(f"Verdict: {self.verdict()}")
        out.append("")
        for c in self.checks:
            out.append(f"[{c.status}] {c.name}: {c.detail}")
            if c.evidence:
                ev = c.evidence.strip()
                if len(ev) > 900:
                    ev = ev[:900] + " ...[truncated]"
                out.append("  " + ev.replace("\n", "\n  "))
        out.append("")
        out.append("Stop rules:")
        out.append("- FAIL means do not update/restart until repaired.")
        out.append("- WARN means inspect before proceeding; common known warnings include config written by newer version and non-standard PATH.")
        out.append("- This script is read-only and does not prove delivery unless paired with a real channel response test.")
        return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only OpenClaw update/restart guard")
    ap.add_argument("--deep", action="store_true", help="also run openclaw status --deep, may be slow")
    ap.add_argument("--measure-turn-latency", action="store_true", help="run two non-delivered gateway agent turns and record cold/warm latency")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--json", action="store_true", help="emit JSON result")
    ap.add_argument("--write-report", action="store_true", help="write report under workspace/reports")
    args = ap.parse_args()

    g = Guard(timeout=args.timeout, deep=args.deep, measure_turn_latency=args.measure_turn_latency)
    g.run_all()
    verdict = g.verdict()
    rendered = g.render()

    report_path = None
    if args.write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_path = REPORT_DIR / f"openclaw-update-guard-{ts}.txt"
        report_path.write_text(rendered + "\n")

    if args.json:
        print(json.dumps({
            "verdict": verdict,
            "reportPath": str(report_path) if report_path else None,
            "checks": [c.__dict__ for c in g.checks],
        }, indent=2))
    else:
        print(rendered)
        if report_path:
            print(f"\nReport: {report_path}")

    return 0 if verdict == "PASS" else (1 if verdict == "FAIL" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
