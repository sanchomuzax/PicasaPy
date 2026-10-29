"""#6039: a főablak arcszámláló-kötései a bomló vezérlő undefined értékére is
egész számot adnak.

A program bezárásakor a FaceScanController QObject-je még él, de a
tulajdonságai már undefined-ot adnak; a tartalék nélküli kötés ekkor
„Unable to assign [undefined] to int” QML-hibát ír, amit a fixture-őr
(#1260) bukásként jelez (main CI, futás 40486249765). A futásidejű
versenyhelyzet helyben nem idézhető elő megbízhatóan, ezért ez az őr a
forrásban rögzíti a tartalékot.
"""

from __future__ import annotations

from pathlib import Path

import pytest

QML_MAPPA = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "qml"
#: #6136: a főablak fiókja és könyvtárnézete önálló komponensbe került; a kötések
#: a főablak és a kiemelt komponensei közül bárhol lehetnek.
FOABLAK_CSALAD = (
    QML_MAPPA / "Main.qml",
    QML_MAPPA / "PicasaPy" / "MainRightDrawer.qml",
    QML_MAPPA / "PicasaPy" / "MainLibraryCanvas.qml",
)


@pytest.mark.parametrize(
    "kotes",
    [
        "faceScanController.unnamedCount ?? 0",
        "faceScanController.scanPercent ?? -1",
        "faceScanController.ignoredCount ?? 0",
        "_faceScanController.sortingPercent ?? -1",
    ],
)
def test_az_arcszamlalo_kotesnek_van_tartaleka(kotes: str) -> None:
    """# rontás-kontroll: a `?? x` nélkül a kötés undefined-ot írna int-be."""
    assert any(kotes in f.read_text(encoding="utf-8") for f in FOABLAK_CSALAD)
