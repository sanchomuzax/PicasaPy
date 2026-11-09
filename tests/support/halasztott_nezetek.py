"""#6700: a halasztott főablak-nézetek előre felépítése a közös QML-fixture-ökben.

A néző, az Időrend és a vetítés a programban csak első megnyitáskor épül fel.
A meglévő próbák a belső elemeiket megnyitás előtt is keresik, ezért a közös
fixture-ök rejtetten előre felépítik őket, ahogy #6700 előtt volt. A halasztást
magát a `halasztott_nezetek` jelölésű próba méri.
"""

from __future__ import annotations

from PySide6.QtCore import QObject

ELORE_EPULO_NEZETEK = ("photoViewerLoader", "timelineViewLoader", "slideshowLoader")


def nezetek_elore(window) -> None:
    """A három halasztott nézet betöltőjét bekapcsolja (a nézetek rejtve maradnak)."""
    for nev in ELORE_EPULO_NEZETEK:
        loader = window.findChild(QObject, nev)
        assert loader is not None, f"hiányzik a(z) {nev} betöltő"
        loader.setProperty("betoltve", True)
