"""A QML-figyelmeztetés-őr osztályozója (a #305-ös őr, a #309-es szűkítéssel).

Külön modul, nem a `conftest.py`-ban: a conftest nem importálható a
tesztekből (nem csomag), a `tests/support/` viszont a `pythonpath` révén
igen — így az osztályozó önmagában is tesztelhető.

## Mire hasal el az őr, és mire nem

KIZÁRÓLAG a QML-SZKRIPTHIBÁKRA. Ezek a minták mindig a MI kódunk hibái
(kötés hivatkozik nem létező tagra, rossz típust rendel értékül), és
platformfüggetlenek — ilyet sose írjunk ki.

A korábbi, MINDEN Qt-figyelmeztetésre elhasaló változat (#305) a
windows-latest CI-lábat buktatta olyan környezeti üzenetekre, amiknek semmi
közük a kódhoz: hiányzó fontkönyvtár a runneren, `OpenThemeData() failed`
offscreen módban, illetve a natív Windows-stílus „nem támogatja a
testreszabást" figyelmeztetése. Ezek platformfüggő zajok; ha az őr rájuk is
elhasal, minden jövőbeli Qt-/runner-változás hamis pirosat okoz — épp az
ellenkezőjét annak, amit a #305 el akart érni (a VALÓDI hibák láthatósága).

Ezért NE tágítsd vissza „minden figyelmeztetésre" gondolkodás nélkül: a
szűk, mintaalapú szűrés a szándékolt viselkedés.
"""

from __future__ import annotations

QML_SCRIPT_ERROR_PATTERNS = (
    "TypeError",
    "ReferenceError",
    "SyntaxError",
    "Unable to assign",
    "is not a function",
)


def is_qml_script_error(message: str) -> bool:
    """QML-szkripthiba-e az üzenet (a mi kötéseink hibája), vagy környezeti zaj."""
    return any(pattern in message for pattern in QML_SCRIPT_ERROR_PATTERNS)
