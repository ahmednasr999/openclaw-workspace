#!/usr/bin/env python3
"""
_imports.py — Helper to import hyphenated module names.

Usage:
    from _imports import agent_common, jobs_source_common
"""

import importlib.util
from pathlib import Path

_scripts_dir = Path(__file__).parent

def _load_module(name: str, filename: str):
    """Load a module from a hyphenated filename."""
    spec = importlib.util.spec_from_file_location(name, _scripts_dir / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load modules
agent_common = _load_module("agent_common", "agent-common.py")
jobs_source_common = _load_module("jobs_source_common", "jobs-source-common.py")
