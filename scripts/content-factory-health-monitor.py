#!/usr/bin/env python3
"""Compatibility wrapper for the current content health monitor.

Old system crontab entries used this filename. Keep it as a thin wrapper so
the CMO/content health lane does not silently fail when the legacy cron runs.
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("content-health-monitor.py")), run_name="__main__")
