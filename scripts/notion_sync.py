#!/usr/bin/env python3
"""Compatibility wrapper for legacy cron skills that import notion_sync.

The maintained implementation currently lives under scripts/deprecated, but
several cron skills still import notion_sync from scripts/. Keep this shim thin
so those jobs do not fail on module lookup while the Notion workflow is being
modernized.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_LEGACY = Path(__file__).resolve().parent / "deprecated" / "notion_sync.py"
_spec = importlib.util.spec_from_file_location("_legacy_notion_sync", _LEGACY)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load legacy notion_sync at {_LEGACY}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

for _name in dir(_module):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_module, _name)
