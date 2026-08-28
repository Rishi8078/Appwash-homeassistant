"""Test bootstrap.

``custom_components/appwash`` is registered here as the ``appwash``
package.  Its ``__init__.py`` is not executed, which keeps the pure-Python
modules (``api``, ``models``, ``const``) importable without a Home Assistant
installation.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "appwash"

if "appwash" not in sys.modules:
    package = types.ModuleType("appwash")
    package.__path__ = [str(COMPONENT)]
    sys.modules["appwash"] = package
