"""Locate immutable resources in source checkouts and frozen bundles."""

from __future__ import annotations

import sys
from pathlib import Path


def bundle_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parents[2]


def obsidian_plugin_source() -> Path:
    return bundle_root() / "integrations" / "obsidian-plugin"
