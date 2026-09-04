"""#2157 — az értesítő cellái CSÚSZNAK, nem halványodnak.

## A mérés

Az eredeti értesítő cellája két kulcskockás sávot tart; a rajzoló minden
képkockán kiértékeli őket (`0x00655950` → `0x009e5e70`):

| sáv | mit szoroz | élő cellán | elbocsátáskor |
|---|---|---|---|
| A | cellaszélesség = **247** (`[popup+0x1bc]`) | **−1,0** | 0,0 |
| B | cellamagasság = **45** (`[popup+0x1c0]`) | a cella **sorszáma** | – |

Időtartam **0,6 s** megjelenéskor (`0x00c7e304`), **0,3 s** elbocsátáskor
(`0x00c7dcc8`) — az aszimmetria az eredetié. A görbe exponenciális
(`0x0072df60`, `u = 8·t`).

⚠️ A pontos Qt-görbe-egyezés **nincs mérve**: a jegy a JELLEGET írja elő
(gyorsuló-lassuló, exponenciális), nem képkockára pontos egyezést. A
próbák ezért a görbe **típusát** és az időtartamokat mérik, nem a köztes
képkockákat.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app.application as app_module

#: `notifier/docbounds` — a cella mért mérete.
CELLA_SZELESSEG = 247
CELLA_MAGASSAG = 45
#: `0x00c7e304` / `0x00c7dcc8`
BE_MS = 600
VISSZA_MS = 300

_CELLA = (
    Path(app_module._APP_DIR) / "qml" / "PicasaPy" / "NotifierCell.qml"
).read_text(encoding="utf-8")
_SAV = (
    Path(app_module._APP_DIR) / "qml" / "PicasaPy" / "PicasaNotifier.qml"
).read_text(encoding="utf-8")


class TestAVizszintesCsuszas:
    def test_a_cella_x_e_ANIMALT(self):
        assert "Behavior on x" in _CELLA, (
            "a cellának nincs vízszintes animációja — ma csak az "
            "átlátszóság animált, az eredetiben viszont CSÚSZIK"
        )

    def test_a_ket_IDOTARTAM_a_mert_ertek(self):
        for ms in (BE_MS, VISSZA_MS):
            assert str(ms) in _CELLA, (
                f"a mért {ms} ms nem szerepel a cellában"
            )

    def test_az_ASZIMMETRIA_megvan(self):
        """A visszacsúszás FELEANNYI ideig tart — ez az eredeti
        aszimmetriája, nem elírás."""
        assert VISSZA_MS * 2 == BE_MS

    def test_a_gorbe_EXPONENCIALIS(self):
        assert "Easing.OutExpo" in _CELLA, (
            "a görbe nem exponenciális jellegű — az eredeti a saját "
            "`u = 8·t` skáláján az"
        )

    def test_a_gorbe_valasztasa_INDOKOLVA_van(self):
        """A jegy kifejezetten kéri: a Qt-görbe választását a kódban kell
        megindokolni, mert a pontos egyezés NINCS mérve."""
        kezd = _CELLA.index("Easing.OutExpo")
        kornyek = _CELLA[max(0, kezd - 1200):kezd]
        assert "nincs mérve" in kornyek or "NINCS mérve" in kornyek, (
            "az `OutExpo` mellett nincs ott, hogy a pontos egyezés nem "
            "mért — a következő olvasó mérésnek hinné"
        )


class TestAFuggolegesAtrendezodes:
    def test_a_cellak_ODACSUSZNAK(self):
        """Ha egy fölöttes cella eltűnik, a többi nem ugrik."""
        assert ("move: Transition" in _SAV or "move:Transition" in _SAV), (
            "a sávnak nincs `move` átmenete — a cellák ugranak"
        )

    def test_a_fuggoleges_animacio_is_a_MERT_idozitest_hasznalja(self):
        kezd = _SAV.index("move:")
        blokk = _SAV[kezd:kezd + 600]
        assert str(BE_MS) in blokk
        assert "Easing.OutExpo" in blokk


class TestAHalvanyitasSorsaKIMONDVA:
    """A jegy külön kéri: a `notifierFadeAnim` sorsa legyen kimondva, mert
    az eredetiben NINCS átlátszóság-animáció."""

    def test_a_dontes_le_van_irva(self):
        assert "notifierFadeAnim" in _SAV
        kezd = _SAV.index("notifierFadeAnim")
        kornyek = _SAV[max(0, kezd - 1500):kezd + 400]
        assert "#2157" in kornyek, (
            "a halványítás mellett nincs ott a #2157 döntése — az "
            "eredetiben nincs ilyen animáció, tehát indokolni kell, "
            "miért marad (vagy el kell venni)"
        )


# ----------------------------------------------------------------------
# Funkcionális próbák — a jegy kifejezetten kéri, hogy a cella `x`-ét és
# az animáció időtartamát ÉLŐ objektumon mérjük, ne csak forrásból.
# A betöltő a #1129 tesztfájl `sav` fixture-jével azonos; azt importáljuk,
# hogy ne legyen két, egymástól elcsúszható másolat.
# ----------------------------------------------------------------------

import time  # noqa: E402

from PySide6.QtCore import QObject  # noqa: E402

from app.test_qml_ertesitosav_1129 import (  # noqa: E402
    _cellak,
    sav,  # noqa: F401  (fixture, a pytest oldja fel)
)


def _var(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.01)
    return False


class TestAzELOCella:
    def test_a_cella_a_helyere_CSUSZIK(self, sav):  # noqa: F811
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        qt_app.processEvents()
        cellak = _cellak(objektum)
        assert cellak, "nem született cella"

        # a becsúszás VÉGÉN a cella a bal szélen ül
        assert _var(qt_app, lambda: abs(cellak[0].x()) < 0.5), (
            f"a cella nem csúszott a helyére (x = {cellak[0].x()})"
        )

    def test_a_KICSUSZOTT_helye_egy_teljes_cellaszelesseg(
        self, sav  # noqa: F811
    ):
        """Az „A" sáv élő cellán −1,0 × 247, elbocsátáskor 0,0 — nálunk
        ez a `[0 … width]` pár. A kicsúszott cella tehát pontosan egy
        cellaszélességgel áll odébb, és így hagyja el a sáv ablakát."""
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        qt_app.processEvents()
        cellak = _cellak(objektum)
        assert cellak
        assert _var(qt_app, lambda: abs(cellak[0].x()) < 0.5)

        cellak[0].setProperty("bent", False)
        assert _var(
            qt_app, lambda: abs(cellak[0].x() - CELLA_SZELESSEG) < 0.5
        ), (
            f"a kicsúszott cella x-e {cellak[0].x()}, a mért érték "
            f"{CELLA_SZELESSEG}"
        )

    def test_az_IDOTARTAMOK_az_elo_animacion(self, sav):  # noqa: F811
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        qt_app.processEvents()
        cellak = _cellak(objektum)
        assert cellak

        animacio = cellak[0].findChild(QObject, "notifierSlideAnim0")
        assert animacio is not None, "nincs vízszintes csúszás-animáció"
        assert animacio.property("duration") == BE_MS

        # elbocsátáskor a másik időtartam lép be
        cellak[0].setProperty("bent", False)
        qt_app.processEvents()
        assert animacio.property("duration") == VISSZA_MS

    def test_a_cella_MERETE_a_mert_ertek(self, sav):  # noqa: F811
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        qt_app.processEvents()
        cellak = _cellak(objektum)
        assert cellak
        assert cellak[0].property("width") == CELLA_SZELESSEG
        assert cellak[0].property("height") == CELLA_MAGASSAG


class TestATOBBcellaEgymasAlatt:
    def test_a_masodik_cella_egy_CELLAMAGASSAGGAL_lejjebb_all(
        self, sav  # noqa: F811
    ):
        """A „B" sáv sorszám × 45 — a `Column` ezt adja, a `move`
        átmenet pedig animálja."""
        objektum, controller, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        controller.collageDesktopBackgroundReady.emit("/kepek/k.jpg")
        qt_app.processEvents()
        cellak = _cellak(objektum)
        assert len(cellak) == 2

        assert _var(
            qt_app,
            lambda: abs(cellak[1].y() - cellak[0].y() - CELLA_MAGASSAG) < 0.5,
        ), (
            f"a két cella távolsága {cellak[1].y() - cellak[0].y()}, "
            f"a mért érték {CELLA_MAGASSAG}"
        )
