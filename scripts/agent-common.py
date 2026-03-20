#!/usr/bin/env python3
"""
agent-common.py — Shared foundation for all briefing agents.

Provides:
  - Standard JSON envelope (meta + data + kpi)
  - Retry with exponential backoff
  - KPI logging (append-only jsonl)
  - Run history logging
  - Dry-run support
  - Feedback recommendation tracking
"""

import json
import os
import sys
import time
import uuid
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from functools import wraps

# Base directories
WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
FEEDBACK_DIR = DATA_DIR / "feedback"
LEARNING_DIR = DATA_DIR / "learning"
JOBS_RAW_DIR = DATA_DIR / "jobs-raw"
KPI_LOG = DATA_DIR / "kpi-history.jsonl"
RUN_LOG = DATA_DIR / "run-history.jsonl"
FAILURES_LOG = DATA_DIR / "failures.json"

# Timezone
CAIRO_TZ = timezone(timedelta(hours=2))

def now_cairo():
    """Current time in Cairo timezone."""
    return datetime.now(CAIRO_TZ)

def now_iso():
    """Current time as ISO string with Cairo timezone."""
    return now_cairo().isoformat()

def generate_run_id():
    """Generate a unique run ID."""
    return str(uuid.uuid4())[:8]


class AgentResult:
    """Standard agent output envelope."""

    def __init__(self, agent_name, version="1.0.0", ttl_hours=6):
        self.agent_name = agent_name
        self.version = version
        self.ttl_hours = ttl_hours
        self.run_id = generate_run_id()
        self.start_time = time.time()
        self.data = {}
        self.kpi = {}
        self.recommendations = []
        self.status = "success"
        self.error = None
        self.retries_used = 0

    def set_data(self, data):
        self.data = data

    def set_kpi(self, kpi):
        self.kpi = kpi

    def add_recommendation(self, action, target, reason, urgency="medium", rec_id=None):
        """Add a tracked recommendation for the learning engine."""
        self.recommendations.append({
            "id": rec_id or f"rec-{self.run_id}-{len(self.recommendations)}",
            "action": action,
            "target": target,
            "reason": reason,
            "urgency": urgency,
            "timestamp": now_iso()
        })

    def set_error(self, error_msg, partial_data=None):
        self.status = "error"
        self.error = error_msg
        if partial_data:
            self.data = partial_data
            self.status = "partial"

    def to_dict(self):
        duration_ms = int((time.time() - self.start_time) * 1000)
        return {
            "meta": {
                "agent": self.agent_name,
                "version": self.version,
                "generated_at": now_iso(),
                "duration_ms": duration_ms,
                "ttl_hours": self.ttl_hours,
                "status": self.status,
                "error": self.error,
                "run_id": self.run_id,
                "retries_used": self.retries_used,
                "data_freshness": "fresh" if self.status == "success" else "stale"
            },
            "data": self.data,
            "kpi": self.kpi,
            "recommendations": self.recommendations
        }

    def write(self, output_path):
        """Write result to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        return output_path

    def log_kpi(self):
        """Append KPI entry to history."""
        entry = {
            "agent": self.agent_name,
            "run_id": self.run_id,
            "timestamp": now_iso(),
            "duration_ms": int((time.time() - self.start_time) * 1000),
            "status": self.status,
            "error": bool(self.error),
            **self.kpi
        }
        KPI_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(KPI_LOG, 'a') as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def log_run(self):
        """Append run entry to history."""
        entry = {
            "agent": self.agent_name,
            "run_id": self.run_id,
            "started": now_iso(),
            "duration_ms": int((time.time() - self.start_time) * 1000),
            "status": self.status,
            "records": len(self.data) if isinstance(self.data, (list, dict)) else 0,
            "error": self.error
        }
        RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(RUN_LOG, 'a') as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def log_feedback(self, feedback_type, entries):
        """Append recommendation entries to feedback log."""
        log_path = FEEDBACK_DIR / f"{feedback_type}.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a') as f:
            for entry in entries:
                entry["timestamp"] = now_iso()
                entry["run_id"] = self.run_id
                f.write(json.dumps(entry, default=str) + "\n")


def retry_with_backoff(func=None, max_retries=3, base_delay=2):
    """Decorator: retry with exponential backoff."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        print(f"  Retry {attempt+1}/{max_retries} after {delay}s: {e}")
                        time.sleep(delay)
            raise last_error
        return wrapper
    if func is not None:
        return decorator(func)
    return decorator


def load_cached(path, max_age_hours=24):
    """Load a JSON file if it exists and is fresh enough."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        # Check freshness
        if "meta" in data and "generated_at" in data["meta"]:
            gen_time = datetime.fromisoformat(data["meta"]["generated_at"])
            age_hours = (now_cairo() - gen_time).total_seconds() / 3600
            if age_hours <= max_age_hours:
                return data
            print(f"  Cached data is {age_hours:.1f}h old (max: {max_age_hours}h)")
        return data
    except Exception as e:
        print(f"  Error loading cached {path}: {e}")
        return None


def is_dry_run():
    """Check if --dry-run flag is set."""
    return "--dry-run" in sys.argv


def load_env(key, default=None):
    """Load from ~/.env file or environment."""
    val = os.environ.get(key)
    if val:
        return val
    env_file = Path.home() / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip('"').strip("'")
    return default


def load_json(path, default=None):
    """Safely load a JSON file."""
    path = Path(path)
    if not path.exists():
        return default if default is not None else {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def agent_main(agent_name, run_func, output_path, ttl_hours=6, version="1.0.0"):
    """Standard agent entry point. Handles dry-run, error capture, KPI logging."""
    print(f"[{agent_name}] Starting... (run_id: {generate_run_id()})")
    if is_dry_run():
        print(f"[{agent_name}] DRY RUN — will print but not write files")

    result = AgentResult(agent_name, version=version, ttl_hours=ttl_hours)

    try:
        run_func(result)
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[{agent_name}] ERROR: {e}\n{tb}")
        # Try to preserve last good data
        cached = load_cached(output_path, max_age_hours=ttl_hours * 4)
        result.set_error(str(e), partial_data=cached.get("data") if cached else None)

    if is_dry_run():
        print(f"\n[{agent_name}] DRY RUN output:")
        print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        result.write(output_path)
        result.log_kpi()
        result.log_run()
        print(f"[{agent_name}] Written to {output_path}")
        print(f"[{agent_name}] Status: {result.status} | Duration: {int((time.time() - result.start_time)*1000)}ms")

    return result
