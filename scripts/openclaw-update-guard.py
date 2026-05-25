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

EXPECTED_MODEL = "openai-codex/gpt-5.5"
SANDBOX_IMAGE = "openclaw-sandbox:bookworm-slim"
OPENCLAW_CONFIG = Path("/root/.openclaw/openclaw.json")
WORKSPACE = Path("/root/.openclaw/workspace")
MODEL_ROUTER = WORKSPACE / "config/model-router.json"
REPORT_DIR = WORKSPACE / "reports"
REQUIRED_PLUGINS = [
    "lossless-claw",
    "telegram",
    "openai",
    "file-transfer",
    "memory-core",
    "memory-wiki",
]
LOSSLESS_TOOLS = {"lcm_grep", "lcm_describe", "lcm_expand", "lcm_expand_query"}


@dataclass
class Check:
    name: str
    status: str
    detail: str
    evidence: str = ""


class Guard:
    def __init__(self, timeout: int = 20, deep: bool = False):
        self.timeout = timeout
        self.deep = deep
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
        cp = self.run_cmd(
            "systemd gateway",
            ["systemctl", "--user", "show", "openclaw-gateway", "-p", "ExecStart", "-p", "MainPID", "-p", "ExecMainStartTimestamp"],
        )
        if not cp:
            return
        text = cp.stdout + cp.stderr
        pid = re.search(r"MainPID=(\d+)", text)
        exec_ok = "dist/index.js gateway" in text and "/usr/bin/node" in text
        ts_line = next((l for l in text.splitlines() if l.startswith("ExecMainStartTimestamp=")), "")
        start_ok = bool(ts_line and ts_line.strip() != "ExecMainStartTimestamp=" and "n/a" not in ts_line.lower())
        if cp.returncode != 0:
            self.add("systemd gateway", "FAIL", f"exit {cp.returncode}", text)
        elif pid and pid.group(1) != "0" and exec_ok and start_ok:
            self.add("systemd gateway", "PASS", f"MainPID={pid.group(1)}, ExecStart/start timestamp present", text.strip())
        else:
            self.add("systemd gateway", "FAIL", "missing valid MainPID, ExecStart, or start timestamp", text.strip())

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
            bad = sorted(set(s for s in strings if s == "openai/gpt-5.5" or s.startswith("openai/gpt-5.5")))
            expected_hits = sum(1 for s in strings if s == EXPECTED_MODEL or s.startswith(EXPECTED_MODEL))
            if bad:
                problems.append(f"{path}: contains {bad}")
            evidence.append(f"{path}: expected_hits={expected_hits}, bad_openai_refs={len(bad)}")
        if problems:
            self.add("model refs", "FAIL", "provider drift detected, expected openai-codex refs", "\n".join(problems + evidence))
        else:
            self.add("model refs", "PASS", f"no openai/gpt-5.5 drift found, expected {EXPECTED_MODEL}", "\n".join(evidence))

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

        for pid in ["lossless-claw", "file-transfer"]:
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
        self.check_systemd()
        self.check_config_validate()
        self.check_sandbox_image()
        self.check_visible_reply_config()
        self.check_gateway_status()
        self.check_gateway_probe()
        self.check_model_refs()
        self.check_codex_usage()
        self.check_plugins()
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
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--json", action="store_true", help="emit JSON result")
    ap.add_argument("--write-report", action="store_true", help="write report under workspace/reports")
    args = ap.parse_args()

    g = Guard(timeout=args.timeout, deep=args.deep)
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
