"""A régi sync modul monkeypatch-felületének futásidejű feloldása."""

from __future__ import annotations

import sys
from typing import Any


def legacy(name: str) -> Any:
    """A picasapy.index.sync aktuális attribútuma, a teszt-foltokkal együtt."""
    module = sys.modules.get("picasapy.index.sync")
    if module is None:
        raise RuntimeError("A kompatibilitási sync modul még nincs betöltve")
    return getattr(module, name)
