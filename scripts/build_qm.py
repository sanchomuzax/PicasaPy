#!/usr/bin/env python3
"""Az összes `picasapy_*.qm` lefordítása a `.ts`-ből (#4817).

A `.qm` nincs a repóban (bináris, a PR-ek összefésülését lehetetlenné
tette); csomagépítés és tesztfutás előtt ez készíti el. Hibánál 1-gyel
lép ki, és megnevezi a sikertelen fájlokat.
"""

from __future__ import annotations

import sys
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GYOKER / "src"))

from picasapy.app.i18n_build import forditsd_mind, lrelease_parancs  # noqa: E402


def main() -> int:
    if lrelease_parancs() is None:
        print("nincs pyside6-lrelease (a PySide6 része) — a .qm nem fordítható")
        return 1
    hibas = forditsd_mind(GYOKER / "src" / "picasapy" / "app" / "i18n")
    for ts in hibas:
        print(f"nem fordult le: {ts}")
    return 1 if hibas else 0


if __name__ == "__main__":
    raise SystemExit(main())
