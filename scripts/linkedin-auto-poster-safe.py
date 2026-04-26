#!/usr/bin/env python3
"""Compatibility wrapper for the current LinkedIn auto-poster.

Legacy crontab entries call linkedin-auto-poster-safe.py. The active
auto-poster already performs Notion preflight and safe staging checks, so this
wrapper preserves the cron target while delegating to the maintained script.
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("linkedin-auto-poster.py")), run_name="__main__")
