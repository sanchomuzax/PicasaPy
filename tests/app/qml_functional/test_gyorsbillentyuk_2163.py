"""#2163 — a könyvtárnézet hiányzó gyorsbillentyűi.

Az eredeti kezelője (`0x005e60d0`, ugrótáblás switch) **34 billentyűt**
kezel; nálunk húsz hiányzott. Ez a kör a leképezhetőket köti be:

| billentyű | az eredetiben | nálunk |
|---|---|---|
| `Ctrl+0` | `thumbui/toggle_right_drawer` (`0x005e6206`) | a jobb fiók billentése |
| `Ctrl+F` | `searchcontainer/searchbutton` (`0x005e63bb`) | a keresőmezőre fókusz |
| `Ctrl+K` | ugyanaz az ág, mint a `Ctrl+T` (`0x005e650e`) | Címkék-panel |

⚠️ A `Ctrl+9` (`editpanel/toggle_left_drawer`) SZÁNDÉKOSAN kimarad: az
eredetiben a szerkesztő-panel bal fiókját billenti, nálunk a szerkesztő
külön nézet, fiók nélkül — nincs mit billenteni. A jegy soronkénti
indoklása ezt rögzíti.

A próbák a `Shortcut` elem `activated` JELÉT bocsátják ki — ezt adja a
valódi billentyűleütés is.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickItem


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


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


def _shortcut(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen gyorsbillentyű: {nev}"
    return obj


def _aktival(sc, qt_app):
    QMetaObject.invokeMethod(sc, "activated", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestAJobbFiokBillenteseCtrl0:
    def test_letezik_a_gyorsbillentyu(self, qml_app, qt_app):
        window, _c, _e = qml_app
        sc = _shortcut(window, "toggleRightDrawerShortcut")
        assert sc.property("sequence") == "Ctrl+0"

    def test_zart_fiokot_KINYIT(self, qml_app, qt_app):
        window, _c, _e = qml_app
        window.setProperty("activeDrawerTab", "")
        qt_app.processEvents()
        _aktival(_shortcut(window, "toggleRightDrawerShortcut"), qt_app)
        assert _var(qt_app, lambda: window.property("activeDrawerTab") != ""), (
            "a Ctrl+0 nem nyitotta ki a fiókot"
        )

    def test_nyitott_fiokot_BEZAR(self, qml_app, qt_app):
        window, _c, _e = qml_app
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        _aktival(_shortcut(window, "toggleRightDrawerShortcut"), qt_app)
        assert _var(qt_app, lambda: window.property("activeDrawerTab") == "")

    def test_a_MEGNYITOTT_lapot_jegyzi_meg(self, qml_app, qt_app):
        """Bezárás után újranyitva ugyanaz a lap jöjjön vissza."""
        window, _c, _e = qml_app
        window.setProperty("activeDrawerTab", "people")
        qt_app.processEvents()
        sc = _shortcut(window, "toggleRightDrawerShortcut")
        _aktival(sc, qt_app)
        assert _var(qt_app, lambda: window.property("activeDrawerTab") == "")
        _aktival(sc, qt_app)
        assert _var(qt_app, lambda: window.property("activeDrawerTab") == "people"), (
            "újranyitáskor nem a korábbi lap jött vissza"
        )


class TestAKeresesCtrlF:
    def test_letezik_a_gyorsbillentyu(self, qml_app, qt_app):
        window, _c, _e = qml_app
        sc = _shortcut(window, "searchShortcut")
        assert sc.property("sequence") == "Ctrl+F"

    def test_a_keresomezore_visz(self, qml_app, qt_app):
        window, _c, _e = qml_app
        mezo = window.findChild(QObject, "searchField")
        assert mezo is not None, "nincs keresőmező"
        mezo.setProperty("focus", False)
        qt_app.processEvents()
        _aktival(_shortcut(window, "searchShortcut"), qt_app)
        assert _var(qt_app, lambda: mezo.property("activeFocus") is True), (
            "a Ctrl+F nem vitte a fókuszt a keresőmezőre"
        )


class TestACtrlK_ugyanaz_mint_a_CtrlT:
    """Az eredetiben egy ág (`0x005e650e`) — nálunk is ugyanaz legyen."""

    def test_letezik_a_gyorsbillentyu(self, qml_app, qt_app):
        window, _c, _e = qml_app
        sc = _shortcut(window, "tagsPanelAltShortcut")
        assert sc.property("sequence") == "Ctrl+K"

    def test_a_cimkek_panelt_nyitja(self, qml_app, qt_app):
        window, _c, _e = qml_app
        window.setProperty("activeDrawerTab", "")
        qt_app.processEvents()
        _aktival(_shortcut(window, "tagsPanelAltShortcut"), qt_app)
        assert _var(qt_app, lambda: window.property("activeDrawerTab") == "tags")


class TestAmitNEM_kotottunk_be:
    """⚠️ Az eredeti kezelőjének VK-tartományán kívüli, illetve a kihagyó
    ágra mutató billentyűkre nem szabad kötni (a spec 10.3 táblája)."""

    TILTOTT = ["Ctrl+7", "Ctrl+J", "Ctrl+Q", "Ctrl+W", "Ctrl+Z"]

    def test_a_negativ_meresu_billentyuk_nincsenek_bekotve(self, qml_app, qt_app):
        window, _c, _e = qml_app
        gyoker = window.contentItem() if hasattr(window, "contentItem") else window
        talalt = []
        for elem in _walk(gyoker):
            seq = elem.property("sequence")
            if seq and str(seq) in self.TILTOTT:
                talalt.append(str(seq))
        assert not talalt, (
            f"olyan billentyű van bekötve, amire az eredetiben NINCS ág: {talalt}"
        )
