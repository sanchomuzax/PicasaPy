"""#1782 — a nyomtatási párbeszéd minőség-ellenőrzése a felületen.

A `printing/dpi.py` a számolást méri; ez a fájl azt, hogy a felhasználó
**látja** is. A jegy nyitómondata:

> A felhasználó ma úgy nyomtathat ki egy 640×480-as képet 8×10-re, hogy a
> program egy szót sem szól.

Két külön dolog kell hozzá, és a teszt mindkettőt méri: legyen
**nyomatméret-választó** (enélkül a DPI-nek nincs mihez képest értelme),
és a mondat **kövesse** a választást.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

_QML = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/PrintDialog.qml"
)


def _forras() -> str:
    return _QML.read_text(encoding="utf-8")


class TestAFeluletenMegvan:
    def test_van_nyomatmeret_valaszto(self):
        assert 'objectName: "printSizeBox"' in _forras(), (
            "nincs nyomatméret-választó — a DPI-nek nincs mihez képest "
            "értelme (#1782)"
        )

    def test_van_minoseg_sor(self):
        assert 'objectName: "printQualityText"' in _forras()

    def test_a_valasztas_ELTEVODIK(self):
        """`PrintLastSize` — a méret túléli az újraindítást."""
        assert "setPrintSize(" in _forras(), (
            "a nyomatméret nem tevődik el — minden indításnál alapértékre "
            "esne vissza"
        )

    def test_a_valasztas_UJRAMER(self):
        """Méretváltáskor a mondatnak követnie kell."""
        forras = _forras()
        assert forras.count("frissitsdAMinoseget()") >= 2, (
            "a méretváltás nem méri újra a minőséget — a mondat a régi "
            "mérethez tartozó számot mutatná"
        )

    def test_mind_a_harom_mondat_szerepel(self):
        forras = _forras()
        for mondat in (
            "Smallest picture: %1 pixels/inch.",
            "Please review before printing.",
            "You are ready to print.",
        ):
            assert mondat in forras, f"hiányzik: {mondat!r}"

    def test_az_egyes_es_a_tobbes_szam_KULON_van(self):
        """Az eredetiben is két külön erőforrás (`::picture`/`::pictures`)."""
        forras = _forras()
        assert "%1 small picture found." in forras
        assert "%1 small pictures found." in forras


class TestAzEloFaban:
    def test_a_parbeszed_felepul_a_valasztoval(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        from support.halasztott_parbeszed import nyisd_meg

        nyisd_meg(window, "printDialog")
        qt_app.processEvents()
        assert window.findChild(QObject, "printSizeBox") is not None
        assert window.findChild(QObject, "printQualityText") is not None
