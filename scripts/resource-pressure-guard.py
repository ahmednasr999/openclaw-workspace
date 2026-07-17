#!/usr/bin/env python3
"""Deterministic VPS resource-pressure monitor and heavy-job circuit breaker."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import time
from typing import Any


WORKSPACE = Path("/root/.openclaw/workspace")
DEFAULT_CONFIG = WORKSPACE / "config/resource-pressure-guard.json"
DEFAULT_STATE = WORKSPACE / ".watchdog/resource-pressure-guard.json"
DEFAULT_LOCK = WORKSPACE / ".watchdog/resource-pressure-guard.lock"


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default.copy()
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default.copy()


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def parse_meminfo(path: Path = Path("/proc/meminfo")) -> dict[str, int]:
    values: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, _, raw = line.partition(":")
        fields = raw.strip().split()
        if fields:
            values[key] = int(fields[0]) * 1024
    return values


def parse_psi(path: Path = Path("/proc/pressure/memory")) -> dict[str, float]:
    values: dict[str, float] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for line in lines:
        fields = line.split()
        if not fields:
            continue
        prefix = fields[0]
        for field in fields[1:]:
            key, _, raw = field.partition("=")
            if key.startswith("avg"):
                values[f"{prefix}_{key}"] = float(raw)
    return values


def collect_metrics() -> dict[str, float]:
    mem = parse_meminfo()
    total = max(mem.get("MemTotal", 0), 1)
    available = mem.get("MemAvailable", 0)
    swap_total = mem.get("SwapTotal", 0)
    swap_free = mem.get("SwapFree", 0)
    disk = shutil.disk_usage("/")
    psi = parse_psi()
    return {
        "mem_available_pct": round(available * 100.0 / total, 2),
        "swap_used_pct": round((swap_total - swap_free) * 100.0 / swap_total, 2)
        if swap_total
        else 0.0,
        "root_disk_used_pct": round(disk.used * 100.0 / disk.total, 2),
        "memory_psi_some_avg60": round(psi.get("some_avg60", 0.0), 2),
        "memory_psi_full_avg60": round(psi.get("full_avg60", 0.0), 2),
    }


def evaluate_thresholds(metrics: dict[str, float], limits: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    pairs = (
        ("mem_available_pct_below", "mem_available_pct", "RAM available"),
        ("swap_used_pct_above", "swap_used_pct", "swap used"),
        ("root_disk_used_pct_above", "root_disk_used_pct", "root disk used"),
        ("memory_psi_some_avg60_above", "memory_psi_some_avg60", "memory PSI some avg60"),
        ("memory_psi_full_avg60_above", "memory_psi_full_avg60", "memory PSI full avg60"),
    )
    for limit_key, metric_key, label in pairs:
        if limit_key not in limits:
            continue
        threshold = float(limits[limit_key])
        value = float(metrics[metric_key])
        breached = value < threshold if limit_key.endswith("_below") else value > threshold
        if breached:
            operator = "<" if limit_key.endswith("_below") else ">"
            reasons.append(f"{label} {value:.2f}% {operator} {threshold:.2f}%")
    return reasons


def recovered(metrics: dict[str, float], limits: dict[str, Any]) -> bool:
    checks = (
        metrics["mem_available_pct"] > float(limits["mem_available_pct_above"]),
        metrics["swap_used_pct"] < float(limits["swap_used_pct_below"]),
        metrics["root_disk_used_pct"] < float(limits["root_disk_used_pct_below"]),
        metrics["memory_psi_some_avg60"] < float(limits["memory_psi_some_avg60_below"]),
        metrics["memory_psi_full_avg60"] < float(limits["memory_psi_full_avg60_below"]),
    )
    return all(checks)


def advance_state(
    previous: dict[str, Any], metrics: dict[str, float], config: dict[str, Any], now: int
) -> tuple[dict[str, Any], str | None]:
    warning_reasons = evaluate_thresholds(metrics, config["warning"])
    critical_reasons = evaluate_thresholds(metrics, config["critical"])
    immediate_reasons = evaluate_thresholds(metrics, config["immediate"])
    blocked = bool(previous.get("blocked", False))
    bad_samples = int(previous.get("critical_samples", 0))
    good_samples = int(previous.get("recovery_samples", 0))

    if critical_reasons:
        bad_samples += 1
        good_samples = 0
        if immediate_reasons or bad_samples >= int(config["critical_samples_to_block"]):
            blocked = True
    else:
        bad_samples = 0
        if blocked and recovered(metrics, config["recovery"]):
            good_samples += 1
            if good_samples >= int(config["recovery_samples_to_unblock"]):
                blocked = False
                good_samples = 0
        elif blocked:
            good_samples = 0

    level = "critical" if blocked else "warning" if warning_reasons or critical_reasons else "normal"
    old_level = str(previous.get("level", "normal"))
    alert: str | None = None
    if level != old_level:
        detail = "; ".join(critical_reasons or warning_reasons) or "thresholds recovered"
        if level == "critical":
            alert = f"🔴 VPS resource guard blocked heavy scheduled launches: {detail}"
        elif level == "warning":
            alert = f"🟡 VPS resource pressure warning: {detail}"
        else:
            alert = "🟢 VPS resource pressure recovered; heavy scheduled launches are enabled."

    state = {
        "updated_at_epoch": now,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "level": level,
        "blocked": blocked,
        "critical_samples": bad_samples,
        "recovery_samples": good_samples,
        "warning_reasons": warning_reasons,
        "critical_reasons": critical_reasons,
        "immediate_reasons": immediate_reasons,
        "metrics": metrics,
    }
    return state, alert


def proc_stat(pid: int) -> tuple[int, int] | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        _, _, tail = raw.rpartition(")")
        fields = tail.strip().split()
        return int(fields[1]), int(fields[19])
    except (OSError, ValueError, IndexError):
        return None


def proc_comm(pid: int) -> str:
    try:
        return Path(f"/proc/{pid}/comm").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def proc_cmd(pid: int) -> list[str]:
    try:
        return [part.decode("utf-8", "replace") for part in Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0") if part]
    except OSError:
        return []


def stale_helper_roots(min_age_seconds: int) -> list[int]:
    uptime = float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0])
    ticks = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
    roots: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if proc_comm(pid) != "openclaw":
            continue
        stat = proc_stat(pid)
        if not stat:
            continue
        ppid, start_ticks = stat
        age = uptime - start_ticks / ticks
        command = proc_cmd(pid)
        if (
            age >= min_age_seconds
            and proc_comm(ppid) == "systemd"
            and len(command) == 1
            and Path(command[0]).name == "openclaw"
        ):
            roots.append(pid)
    return roots


def descendants(roots: list[int]) -> list[int]:
    parent_map: dict[int, list[int]] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        stat = proc_stat(pid)
        if stat:
            parent_map.setdefault(stat[0], []).append(pid)
    found: set[int] = set()
    stack = list(roots)
    while stack:
        pid = stack.pop()
        if pid in found:
            continue
        found.add(pid)
        stack.extend(parent_map.get(pid, []))
    return sorted(found, reverse=True)


def reap_stale_helpers(min_age_seconds: int) -> list[int]:
    targets = descendants(stale_helper_roots(min_age_seconds))
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in targets:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
            except PermissionError:
                continue
        if sig == signal.SIGTERM and targets:
            time.sleep(1)
    return targets


def locked_update(config_path: Path, state_path: Path, lock_path: Path, reap: bool) -> dict[str, Any]:
    config = load_json(config_path, {})
    if not config:
        raise SystemExit(f"invalid or missing config: {config_path}")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        reaped = reap_stale_helpers(int(config["stale_helper_age_seconds"])) if reap else []
        metrics = collect_metrics()
        previous = load_json(state_path, {})
        state, alert = advance_state(previous, metrics, config, int(time.time()))
        state["reaped_helper_pids"] = reaped
        if reaped:
            reaped_alert = f"🟡 VPS resource guard reaped {len(reaped)} stale OpenClaw helper processes."
            alert = f"{reaped_alert} {alert}" if alert else reaped_alert
        if alert:
            state["alert"] = alert
        write_json_atomic(state_path, state)
        return state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("monitor", "check", "status"))
    parser.add_argument("--task")
    parser.add_argument("--reap", action="store_true")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    args = parser.parse_args()
    config = load_json(args.config, {})
    if not config:
        print(json.dumps({"error": f"invalid or missing config: {args.config}"}))
        return 2

    if args.mode == "status":
        print(json.dumps(load_json(args.state, {}), sort_keys=True))
        return 0

    state = locked_update(args.config, args.state, args.lock, args.reap)
    if args.mode == "monitor":
        print(json.dumps(state, sort_keys=True))
        return 0

    if not args.task:
        print(json.dumps({"error": "--task is required for check"}))
        return 2
    if args.task not in set(config.get("heavy_tasks", [])):
        print(json.dumps({"task": args.task, "decision": "allow", "heavy": False}))
        return 0
    decision = "block" if state.get("blocked") else "allow"
    print(
        json.dumps(
            {
                "task": args.task,
                "decision": decision,
                "heavy": True,
                "level": state.get("level"),
                "reasons": state.get("critical_reasons", []),
            },
            sort_keys=True,
        )
    )
    return 75 if decision == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
