"""Test bootstrap.

The repository root is the Home Assistant component directory, so it is
registered here as the ``appwash`` package.  ``appwash/__init__.py`` is not
executed, which keeps the pure-Python modules (``api``, ``models``,
``const``) importable without a Home Assistant installation.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if "appwash" not in sys.modules:
    package = types.ModuleType("appwash")
    package.__path__ = [str(ROOT)]
    sys.modules["appwash"] = package
