"""„Ellenőrzés" gomb a kis felbontású képekhez (#1953).

## Mit adott eddig

**Az üzenetet igen, a gombot nem.** A `PrintDialog` kiírta az eredeti
mondatait („Smallest picture: … / … small pictures found. / Please review
before printing."), de a felhasználó megtudta, hogy *van* kis felbontású
kép, azt viszont nem, hogy **melyik**.

## Az eredeti

`printpanel/reviewnowbutton` és `…button2` — felirat **„Review" /
„Ellenőrzés"**, súgó „Make sure your photos are ready to print" /
„Győződjön meg arról, hogy a fotók nyomtatásra készek"
(`referencia/ui-leltar.csv:1434–1437`, `i18n-hu/tooltips.xml:108–119`).
Mindkettőt ugyanaz a függvény kezeli, mint a figyelmeztető mondatot
(`0x00745980`).

⚠️ **Hogy MIÉRT kettő, az NINCS mérve** (a jegy blokkolt kérdése). Egy
gomb elég; a második az eredeti kétállapotú elrendezésének maradéka lehet.

## Ez a réteg

A vezérlő adja meg, **melyik** képek esnek a küszöb alá — név és effektív
DPI —, ugyanazzal a számítással, amivel az összegzés készül. Enélkül a
gomb csak egy újabb néma vezérlő lenne.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.print_controller import PrintController
from picasapy.printing.dpi import KICSI_KUSZOB_DPI

from support.jpeg_factory import make_jpeg


class _FakePhoto:
    """A rekord annyit tud, amennyit a nyomtatás-vezérlő kér tőle: hol
    van, hogy hívják, és mekkora."""

    def __init__(
        self, folder_path: str, name: str, width: int, height: int
    ) -> None:
        self.folder_path = folder_path
        self.name = name
        self.width = width
        self.height = height


@pytest.fixture
def vegyes(tmp_path):
    """Egy NAGY és két KICSI kép 4×6-os nyomathoz (küszöb 150 DPI).

    4×6 hüvelyken: 1600×1100 → 266 DPI (nagy); 450×300 → 75 DPI (kicsi);
    300×200 → 50 DPI (a legkisebb). Ugyanez 8×10-en: a „nagy" is 137
    DPI-re esik — ezért alkalmas a nyomatméret-függés mérésére.
    """
    meretek = {"nagy.jpg": (1600, 1100), "kicsi.jpg": (450, 300),
               "legkisebb.jpg": (300, 200)}
    for nev, meret in meretek.items():
        make_jpeg(tmp_path / nev, size=meret)
    photos = [
        _FakePhoto(str(tmp_path), nev, sz, m)
        for nev, (sz, m) in meretek.items()
    ]
    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    return PrintController(photo_source=lambda: photos, settings=beallitasok)


class TestAKifogasoltKepekListaja:
    def test_CSAK_a_kuszob_alattiakat_adja(self, vegyes):
        tetelek = vegyes.smallPictures([0, 1, 2], "M4X6")
        nevek = sorted(t["name"] for t in tetelek)
        assert nevek == ["kicsi.jpg", "legkisebb.jpg"], (
            "a nagy felbontású kép is bekerült a kifogásoltak közé"
        )

    def test_a_DPI_is_benne_van(self, vegyes):
        szerint = {t["name"]: t["dpi"] for t in vegyes.smallPictures(
            [0, 1, 2], "M4X6")}
        assert szerint["kicsi.jpg"] == 75
        assert szerint["legkisebb.jpg"] == 50

    def test_a_legrosszabb_all_elol(self, vegyes):
        """A felhasználót a legrosszabb érdekli először."""
        tetelek = vegyes.smallPictures([0, 1, 2], "M4X6")
        assert [t["dpi"] for t in tetelek] == sorted(t["dpi"] for t in tetelek)

    def test_egyezik_az_OSSZEGZESSEL(self, vegyes):
        """A foga: ha a két út külön számol, előbb-utóbb ellentmondanak —
        a mondat N kis képet ír, a lista M-et mutat."""
        osszegzes = vegyes.printQuality([0, 1, 2], "M4X6")
        assert len(vegyes.smallPictures([0, 1, 2], "M4X6")) == osszegzes["small"]
        assert osszegzes["threshold"] == KICSI_KUSZOB_DPI

    def test_csak_NAGY_kepekre_URES(self, vegyes):
        assert vegyes.smallPictures([0], "M4X6") == []

    def test_URES_kijelolesre_URES(self, vegyes):
        assert vegyes.smallPictures([], "M4X6") == []

    def test_a_NYOMATMERET_szamit(self, vegyes):
        """NAGYOBB nyomaton több kép esik a küszöb alá: a 1600×1100 a
        4×6-on még 266 DPI, a 8×10-en már csak 137."""
        negyszer_hat = vegyes.smallPictures([0, 1, 2], "M4X6")
        nyolcszor_tiz = vegyes.smallPictures([0, 1, 2], "M8X10")
        assert len(negyszer_hat) == 2
        assert len(nyolcszor_tiz) == 3, (
            "a nagyobb nyomaton a »nagy« képnek is kicsivé kell válnia"
        )


class TestAGombAQMLben:
    @staticmethod
    def _dialogus() -> str:
        import picasapy.app

        return (
            Path(picasapy.app.__file__).parent
            / "qml" / "PicasaPy" / "PrintDialog.qml"
        ).read_text(encoding="utf-8")

    def test_van_ellenorzes_gomb(self):
        assert 'objectName: "printReviewButton"' in self._dialogus()

    def test_az_EREDETI_feliratot_es_sugot_hasznalja(self):
        forras = self._dialogus()
        kezdet = forras.index('objectName: "printReviewButton"')
        blokk = forras[kezdet : kezdet + 900]
        assert 'qsTr("Review")' in blokk
        assert "Make sure your photos are ready to print" in blokk

    def test_CSAK_akkor_latszik_ha_van_kis_kep(self):
        """Az eredetiben a „You are ready to print." ágon nincs mit
        ellenőrizni."""
        forras = self._dialogus()
        kezdet = forras.index('objectName: "printReviewButton"')
        blokk = forras[kezdet : kezdet + 900]
        assert "quality.small > 0" in blokk

    def test_a_gomb_NEM_nema(self):
        """A #1798 osztálya: a gomb ne csak létezzen — hívja is a listát."""
        forras = self._dialogus()
        kezdet = forras.index('objectName: "printReviewButton"')
        blokk = forras[kezdet : kezdet + 900]
        assert "smallPictures" in blokk
