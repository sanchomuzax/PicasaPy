"""Forrásból futó Windows-csomagmérő adaptere a QML-cache segédhez."""

from __future__ import annotations

import sys
from pathlib import Path

_FORRAS = Path(__file__).resolve().parents[2] / "src"
if str(_FORRAS) not in sys.path:
    sys.path.insert(0, str(_FORRAS))

from picasapy.app import qml_cache_warmup as _qml_cache_warmup  # noqa: E402


def __getattr__(nev: str):
    """A termékkód segédjét lazán adja tovább, tesztben is cserélhetően."""
    return getattr(_qml_cache_warmup, nev)
