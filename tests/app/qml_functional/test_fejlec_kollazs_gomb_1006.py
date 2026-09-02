"""Kollázs-gomb a mappa-fejlécben (#1006).

## A lelet

Az eredeti Picasában NÉGY helyről indítható kollázs; nálunk kettő
működött. A két hiányzó egy-egy fejléc-gomb:

| forrás | geometria |
|---|---|
| `headerpanel/create_collage` | (44, 53), **29 × 27** |
| `faceheaderpanel/create_collage` | (115, 55), **29 × 27** |

*(`picasa-create-features.md` 1.10.5)*

## ⚠️ Nálunk EGY fejléc szolgálja mindkettőt

Az eredetiben külön panel tartozik a mappa- és az arc-nézethez. A mi
felületünkön a személy képei UGYANABBAN a rácsban, ugyanazzal a
`LightboxHeader`-rel jelennek meg — nincs külön arc-fejléc (mérve: a
`faceHeader`/`PersonHeader` nevekre nulla találat a QML-fában). Egy gomb
tehát mindkét belépési pontot lefedi; külön arc-fejlécet építeni olyan
felületet hozna létre, ami nálunk nem létezik.

⚠️ A jegy a `CollectionHeader.qml`-t nevezte meg arc-fejlécként — az
valójában a BAL HASÁB gyűjtemény-fejléce (Albumok, Emberek, …), nem a
képnézeté. Ezt a mérés derítette ki.

## A forrás

A gomb a FEJLÉCHEZ tartozó csoport képeit adja át — nem a kijelölést és
nem a tálcát. Az eredeti is a panelhez tartozó halmazzal dolgozik.
"""
from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app

_HEADER = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "LightboxHeader.qml"
).read_text(encoding="utf-8")
_FEED = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "LightboxFeed.qml"
).read_text(encoding="utf-8")


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elem(window, nev: str):
    for it in _walk(window.contentItem()):
        if it.objectName() == nev:
            return it
    return window.findChild(QObject, nev)


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _kattints(window, elem, qt_app):
    assert elem.width() > 0 and elem.height() > 0, "kattinthatatlan (0 méret)"
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


class TestAGombOttVan:
    def test_a_fejlecben_van_kollazs_gomb(self, qml_app, qt_app):
        window, _c, _e = qml_app
        gomb = _elem(window, "headerCollageButton")
        assert gomb is not None, "a mappa-fejlécből hiányzik a kollázs-gomb"

    def test_a_MERT_meret_29x27(self, qml_app, qt_app):
        """`headerpanel/create_collage` — 29 × 27 (spec 1.10.5)."""
        window, _c, _e = qml_app
        gomb = _elem(window, "headerCollageButton")
        assert (gomb.width(), gomb.height()) == (29.0, 27.0)

    def test_van_buboreksugoja(self):
        reszlet = _HEADER[_HEADER.find("headerCollageButton"):][:900]
        assert "ToolTip.text" in reszlet


class TestABekotes:
    """A gomb NE csak létezzen — nyissa is meg a lapot."""

    def test_a_jelzes_a_feedben_FOGADVA_van(self):
        assert "onCollageRequested" in _FEED, (
            "a fejléc kollázs-jelzését senki nem fogja el — néma gomb"
        )

    def test_a_CSOPORT_kepeit_adja_at_nem_a_kijelolest(self):
        """A fejléc a SAJÁT csoportjához tartozik; a kijelölés vagy a
        tálca más halmaz. Az eredeti is a panelhez tartozó képekkel
        dolgozik.
        """
        kezdet = _FEED.find("onCollageRequested")
        blokk = _FEED[kezdet:kezdet + 700]
        assert "modelData.start" in blokk and "modelData.count" in blokk, (
            "a gomb nem a csoport sorait adja át"
        )

    def test_kattintasra_megnyilik_a_kollazs_lap(self, qml_app, qt_app):
        window, _c, _e = qml_app
        gomb = _elem(window, "headerCollageButton")
        if gomb is None or not gomb.isEnabled():
            import pytest
            pytest.skip("a fejléc nincs kirajzolva ebben az összeállításban")
        _kattints(window, gomb, qt_app)
        sav = _elem(window, "documentTabStrip")
        assert _var(
            qt_app, lambda: sav.property("activeTabId") == "collage"
        ), "a fejléc kollázs-gombja nem nyitotta meg a lapot"


class TestAmitKIMONDUNK:
    def test_a_forras_kimondja_hogy_EGY_fejlec_van(self):
        """Hogy egy későbbi kör ne építsen külön arc-fejlécet, ami nálunk
        nem létezik."""
        reszlet = _HEADER[_HEADER.find("headerCollageButton") - 1400:]
        reszlet = reszlet[:2200]
        assert "arc" in reszlet.lower(), (
            "a forrás nem mondja ki, hogy ez a fejléc az arc-nézetet is "
            "kiszolgálja"
        )
