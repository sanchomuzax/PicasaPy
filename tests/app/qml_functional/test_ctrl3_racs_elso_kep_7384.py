"""A Ctrl+3 a rács szerinti első képet nyitja meg (#7384).

Az eredeti Picasa 3.9 `Ctrl+3`-ja (`thumbui/fullview`, `0x005e624f`) nem
vizsgálja a kijelölést a gombnyomás előtt:

- kijelölt kép nélkül (a mappa van kijelölve) az 1. képet nyitja (J1a 9.);
- több kijelölt képnél a RÁCS szerinti elsőt, a kijelölés sorrendjétől
  függetlenül (J1b 12. és 19.);
- egy kijelölt képnél azt a képet, és az Escape után a kijelölés megmarad
  (J1a 15. és 17.).

A billentyűket valódi `QTest.keyClick` viszi az ablakra: a teszt a
`nezdEsSzerkeszd()` függvényt közvetlenül nem hívja, a hatást a néző
állapotán és a főablak kijelölésén méri.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQml import QJSValue
from PySide6.QtTest import QTest

from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._menusor_maradek_5150_helpers import billentyu
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    kijelol,
    varj,
)

CTRL = Qt.KeyboardModifier.ControlModifier
#: a teszt mappájának három képe: a rács sorai 0, 1, 2
ELSO_SOR = 0
KOZEPSO_SOR = 1
UTOLSO_SOR = 2
#: az Alapvető javítások fül (az eredetiben az 1. fül) a szerkesztő panelen
ALAPVETO_FUL = 0


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _nezo(window) -> QObject:
    nezo = _objektum(window, "photoViewer")
    assert nezo is not None, "a photoViewer nem található"
    return nezo


def _kijeloles(window) -> list[int]:
    """A főablak `selectedIndexes` listája (a kattintás sorrendjében)."""
    ertek = window.property("selectedIndexes")
    if isinstance(ertek, QJSValue):
        ertek = ertek.toVariant()
    return [int(sor) for sor in ertek]


def _ctrl3(window, qt_app) -> None:
    billentyu(window, qt_app, "editViewShortcut", Qt.Key.Key_3, CTRL)


def _nem_nyilt_meg(window, qt_app) -> bool:
    """Ctrl+3 után rövid ideig várva sem nyílik néző (a negatív eset ellenőrzése)."""
    return not varj(qt_app, lambda: window.property("viewerOpen") is True, 1.0)


def _kijelolest_torol(window, qt_app) -> None:
    """A mappa van kijelölve, kép nincs: ez az eredeti J1a 9. előtti állapota."""
    kijelol(window, qt_app, [])
    assert _kijeloles(window) == [], (
        "a kijelölés nem ürült ki: a teszt nem bizonyít"
    )
    assert window.property("selectedIndex") == -1, (
        "a horgony nem ürült ki: a teszt nem bizonyít"
    )


class TestKijelolesNelkul:
    def test_a_ctrl_3_az_elso_kepet_nyitja_az_elso_fulon(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _kijelolest_torol(window, qt_app)
        assert window.property("viewerOpen") is False, "a néző már nyitva: nem bizonyít"

        _ctrl3(window, qt_app)

        assert varj(qt_app, lambda: window.property("viewerOpen") is True), (
            "a Ctrl+3 kijelölt kép nélkül nem nyitotta meg a nézőt"
        )
        nezo = _nezo(window)
        assert varj(qt_app, lambda: nezo.property("currentIndex") == ELSO_SOR), (
            "a Ctrl+3 kijelölés nélkül nem a rács 1. képét nyitotta"
        )
        panel = _objektum(window, "viewerEditorPanel")
        assert panel is not None, "a viewerEditorPanel nem található"
        assert panel.property("activeTab") == ALAPVETO_FUL, (
            "a néző nem az 1. fülön nyílt"
        )

    def test_ures_racsnal_a_ctrl_3_nem_nyit_nezot(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        controller.search("ilyen-szo-egyik-kepben-sincs")
        assert varj(qt_app, lambda: controller.photos.rowCount() == 0), (
            "a keresés nem ürítette ki a rácsot: a teszt nem bizonyít"
        )
        _kijelolest_torol(window, qt_app)

        _ctrl3(window, qt_app)

        assert _nem_nyilt_meg(window, qt_app), "üres rácson a Ctrl+3 nézőt nyitott"


class TestTobbesKijeloles:
    @pytest.mark.parametrize(
        "kijeloles_sorrendje",
        [
            [UTOLSO_SOR, KOZEPSO_SOR],
            [KOZEPSO_SOR, UTOLSO_SOR],
        ],
        ids=["utolso_aztan_kozepso", "kozepso_aztan_utolso"],
    )
    def test_a_ctrl_3_a_racs_szerinti_elsot_nyitja(
        self, kep_app, qt_app, kijeloles_sorrendje
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, kijeloles_sorrendje)
        assert _kijeloles(window) == (
            kijeloles_sorrendje
        ), "a kijelölés sorrendje nem a vártként rögzült: a teszt nem bizonyít"
        assert window.property("viewerOpen") is False, "a néző már nyitva: nem bizonyít"

        _ctrl3(window, qt_app)

        assert varj(qt_app, lambda: window.property("viewerOpen") is True), (
            "a Ctrl+3 nem nyitotta meg a nézőt többes kijelöléssel"
        )
        nezo = _nezo(window)
        assert varj(qt_app, lambda: nezo.property("currentIndex") == KOZEPSO_SOR), (
            "a Ctrl+3 nem a rács szerinti első kijelölt képet nyitotta "
            f"(kijelölés sorrendje: {kijeloles_sorrendje})"
        )


class TestEgyKijeloltKep:
    def test_a_ctrl_3_a_kijelolt_kepet_nyitja_es_az_escape_utan_a_kijeloles_marad(
        self, kep_app, qt_app
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, [KOZEPSO_SOR])
        assert window.property("viewerOpen") is False, "a néző már nyitva: nem bizonyít"

        _ctrl3(window, qt_app)

        assert varj(qt_app, lambda: window.property("viewerOpen") is True), (
            "a Ctrl+3 nem nyitotta meg a nézőt egy kijelölt képpel"
        )
        nezo = _nezo(window)
        assert varj(qt_app, lambda: nezo.property("currentIndex") == KOZEPSO_SOR), (
            "a Ctrl+3 nem a kijelölt képet nyitotta"
        )

        QTest.keyClick(window, Qt.Key.Key_Escape)

        assert varj(qt_app, lambda: window.property("viewerOpen") is False), (
            "az Escape nem zárta be a nézőt"
        )
        assert _kijeloles(window) == [KOZEPSO_SOR], (
            "az Escape után a kijelölés nem maradt meg"
        )
        assert window.property("selectedIndex") == KOZEPSO_SOR, (
            "az Escape után a horgony nem maradt a kijelölt képen"
        )
