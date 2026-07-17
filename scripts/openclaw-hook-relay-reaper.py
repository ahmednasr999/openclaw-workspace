#!/usr/bin/env python3
"""Reap expired OpenClaw native-hook relay subprocesses.

Codex native-hook commands have a 10-second parent timeout. Under host pressure,
an abandoned ``openclaw-hooks`` subprocess can outlive that budget and retain its
``openclaw`` launcher. This watchdog only targets relay workers older than the
configured ceiling and only when they belong to openclaw-gateway.service.
"""

from __future__ import annotations

import argparse
import fcntl
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


GATEWAY_CGROUP_MARKER = "/openclaw-gateway.service"


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    ppid: int
    comm: str
    start_ticks: int
    age_seconds: float
    cgroup: str


def read_process(pid: int) -> ProcessIdentity | None:
    proc_dir = Path("/proc") / str(pid)
    try:
        comm = (proc_dir / "comm").read_text(encoding="utf-8").strip()
        stat = (proc_dir / "stat").read_text(encoding="utf-8")
        cgroup = (proc_dir / "cgroup").read_text(encoding="utf-8")
        close_paren = stat.rfind(")")
        if close_paren < 0:
            return None
        fields = stat[close_paren + 2 :].split()
        ppid = int(fields[1])
        start_ticks = int(fields[19])
        uptime_seconds = float(Path("/proc/uptime").read_text().split()[0])
        clock_ticks = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        age_seconds = max(0.0, uptime_seconds - (start_ticks / clock_ticks))
        return ProcessIdentity(pid, ppid, comm, start_ticks, age_seconds, cgroup)
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError, IndexError):
        return None


def identity_is_current(identity: ProcessIdentity) -> bool:
    current = read_process(identity.pid)
    return current is not None and current.start_ticks == identity.start_ticks


def expired_relays(max_age_seconds: float) -> list[ProcessIdentity]:
    relays: list[ProcessIdentity] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        process = read_process(int(entry.name))
        if process is None:
            continue
        if process.comm != "openclaw-hooks":
            continue
        if GATEWAY_CGROUP_MARKER not in process.cgroup:
            continue
        if process.age_seconds <= max_age_seconds:
            continue
        relays.append(process)
    return sorted(relays, key=lambda process: process.age_seconds, reverse=True)


def parent_launcher(relay: ProcessIdentity) -> ProcessIdentity | None:
    parent = read_process(relay.ppid)
    if parent is None:
        return None
    if parent.comm != "openclaw":
        return None
    if GATEWAY_CGROUP_MARKER not in parent.cgroup:
        return None
    return parent


def send_if_current(identity: ProcessIdentity, sig: signal.Signals) -> bool:
    if not identity_is_current(identity):
        return False
    try:
        os.kill(identity.pid, sig)
        return True
    except (PermissionError, ProcessLookupError):
        return False


def reap_once(max_age_seconds: float, grace_seconds: float, dry_run: bool) -> int:
    targets: list[ProcessIdentity] = []
    seen: set[tuple[int, int]] = set()
    relays = expired_relays(max_age_seconds)
    for relay in relays:
        for process in (relay, parent_launcher(relay)):
            if process is None:
                continue
            key = (process.pid, process.start_ticks)
            if key not in seen:
                seen.add(key)
                targets.append(process)

    if not targets:
        return 0

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    description = ",".join(
        f"{process.pid}:{process.comm}:{process.age_seconds:.1f}s" for process in targets
    )
    if dry_run:
        print(f"{timestamp} dry-run expired hook relays: {description}", flush=True)
        return len(relays)

    for process in targets:
        send_if_current(process, signal.SIGTERM)

    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline and any(identity_is_current(p) for p in targets):
        time.sleep(0.1)

    killed = 0
    for process in targets:
        if send_if_current(process, signal.SIGKILL):
            killed += 1

    print(
        f"{timestamp} reaped {len(relays)} expired hook relay(s); "
        f"targets={description}; forced={killed}",
        flush=True,
    )
    return len(relays)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-age-seconds", type=float, default=15.0)
    parser.add_argument("--interval-seconds", type=float, default=5.0)
    parser.add_argument("--grace-seconds", type=float, default=1.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.max_age_seconds < 10:
        parser.error("--max-age-seconds must be at least 10")
    if args.interval_seconds <= 0 or args.grace_seconds < 0:
        parser.error("interval must be positive and grace must be non-negative")
    return args


def main() -> int:
    args = parse_args()
    runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    runtime_dir.mkdir(parents=True, exist_ok=True)
    lock_path = runtime_dir / "openclaw-hook-relay-reaper.lock"
    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("openclaw hook relay reaper is already running", file=sys.stderr)
            return 0

        while True:
            reap_once(args.max_age_seconds, args.grace_seconds, args.dry_run)
            if args.once:
                return 0
            time.sleep(args.interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
