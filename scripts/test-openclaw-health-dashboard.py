#!/usr/bin/env python3
"""Regression checks for Health Guard timeout and LCM pressure classification."""
from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("openclaw-health-dashboard.py")
spec = importlib.util.spec_from_file_location("openclaw_health_dashboard", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def classify(tokens, pending=None, maintenance_tokens=None):
    return module.classify_lcm_pressure(tokens, pending, maintenance_tokens, context_window=1_000_000)


state, ratio, issues = classify(143_033)
assert state == "OK", (state, ratio, issues)
assert round(ratio, 3) == 0.143

state, _, issues = classify(760_000)
assert state == "WARN" and "context_pressure_high" in issues

state, _, issues = classify(910_000)
assert state == "CRITICAL" and "context_pressure_critical" in issues

state, _, issues = classify(200_000, pending=1, maintenance_tokens=75_000)
assert state == "WARN" and "maintenance_pending" in issues

state, _, issues = classify(200_000, pending=1, maintenance_tokens=10_000)
assert state == "OK" and "maintenance_pending_transient" in issues

print("health dashboard classification tests passed")
