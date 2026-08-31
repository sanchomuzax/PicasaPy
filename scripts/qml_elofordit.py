#!/usr/bin/env python3
"""#1719 — a QML-fa előrefordítása a REPÓ forrásfáján (fejlesztői kényelem).

A tényleges megvalósítás a csomagban él
(`src/picasapy/perf/qml_elofordit.py`), mert a telepítéskor futó lépésnek
(`packaging/debian/postinst`, `packaging/windows/install.bat.template`) a
telepített csomagból kell elérnie. Ez a szkript csak a `src/`-t teszi az
importútra, hogy a repóból is egyetlen paranccsal futtatható legyen::

    python3 scripts/qml_elofordit.py               # fordítás
    python3 scripts/qml_elofordit.py --ellenoriz   # csak ellenőrzés
    python3 scripts/qml_elofordit.py --takarit     # vissza fejlesztői állapotba

⚠️ A forrásfán KÉZZEL futtatva a `.qmlc` **elnyomja** a később szerkesztett
`.qml`-t (a fordított egység szándékosan időbélyeg-független). Fejlesztés
közben ezért a `--takarit` a normális befejező lépés.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from picasapy.perf.qml_elofordit import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
