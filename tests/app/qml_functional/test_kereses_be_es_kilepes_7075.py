"""#7075: keresésbe és keresésből a Picasa billentyűútjaival.

Minden próbában a billentyűt vagy a törlőgombot valódi QML-eseménnyel
aktiváljuk. A Picasa előtti kijelölés/görgetés/mappa visszaállítása külön
Colab-mérést igényel, ezért ezek a próbák az eddigi állapotot hagyják érvényben.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _elem(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kijeloles(window) -> list[int]:
    value = window.property("selectedIndexes")
    return value.toVariant() if hasattr(value, "toVariant") else list(value)


def _keresest_indit(window, controller, qt_app) -> None:
    mezo = _elem(window, "searchField")
    mezo.forceActiveFocus()
    qt_app.processEvents()
    QTest.keyClick(window, Qt.Key.Key_Z)
    QTest.keyClick(window, Qt.Key.Key_Z)
    assert _varj(qt_app, lambda: controller.searchQuery == "zz"), (
        "a valódi billentyűleütések nem indították el a keresést"
    )
    timer = _elem(window, "suggestionsTimer")
    assert _varj(qt_app, lambda: timer.property("running") is False), (
        "a javaslatfrissítő időzítő nem futott le"
    )
    assert not _elem(window, "searchSuggestions").property("visible"), (
        "a 'zz' próbakifejezéshez nem várt javaslatpopup nyílt"
    )


def _racs_fokusz(window, qt_app, nev="photoGrid"):
    racs = _elem(window, nev)
    racs.forceActiveFocus()
    qt_app.processEvents()
    assert racs.property("activeFocus") is True, "a rács nem kapott fókuszt"
    return racs


def test_escape_a_racson_torli_a_keresest_es_a_szuroket(qml_app, qt_app):
    window, controller, _engine = qml_app
    _keresest_indit(window, controller, qt_app)
    assert controller.searchActive is True

    _racs_fokusz(window, qt_app, "groupedSearchResults")
    QTest.keyClick(window, Qt.Key.Key_Escape)

    assert _varj(qt_app, lambda: controller.searchActive is False), (
        "az Esc nem lépett ki a keresésből a rácson"
    )
    assert controller.filterActive is False
    assert _elem(window, "searchField").property("text") == ""

    controller.showStarred()
    assert controller.filterActive is True
    _racs_fokusz(window, qt_app)
    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert _varj(qt_app, lambda: controller.filterActive is False), (
        "az Esc nem törölte az aktív szűrőt a rácson"
    )


def test_masodik_ctrl_f_torli_a_keresest(qml_app, qt_app):
    window, controller, _engine = qml_app
    _keresest_indit(window, controller, qt_app)

    QTest.keyClick(
        window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier
    )

    assert _varj(qt_app, lambda: controller.searchActive is False), (
        "a második Ctrl+F nem kapcsolta ki a keresést"
    )
    assert controller.filterActive is False
    assert _elem(window, "searchField").property("text") == ""


@pytest.mark.parametrize("height_offset", (-5, 0, 5))
def test_x_nem_allitja_vissza_a_kijelolest_es_masodik_ctrl_f_kilep(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    window.setHeight(window.height() + height_offset)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    _keresest_indit(window, controller, qt_app)
    assert _kijeloles(window) == [], (
        "kereséskor a kijelölésnek a jelenlegi viselkedés szerint ki kell ürülnie"
    )

    gomb = _elem(window, "searchClear")
    assert gomb.isVisible() and gomb.width() > 0 and gomb.height() > 0
    pont = gomb.mapToScene(QPointF(gomb.width() / 2, gomb.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )

    assert _varj(qt_app, lambda: controller.searchActive is False)
    assert _elem(window, "searchField").property("text") == ""
    assert _kijeloles(window) == [], (
        "az X nem állíthatja vissza a keresés előtti kijelölést"
    )

    _keresest_indit(window, controller, qt_app)
    QTest.keyClick(
        window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier
    )

    assert _varj(qt_app, lambda: controller.searchActive is False), (
        "a második Ctrl+F nem kapcsolta ki a keresést"
    )
    assert controller.filterActive is False
    assert _elem(window, "searchField").property("text") == ""


def test_racson_gepelt_ascii_betu_a_keresobe_kerul(qml_app, qt_app):
    window, controller, _engine = qml_app
    _racs_fokusz(window, qt_app)

    QTest.keyClick(window, Qt.Key.Key_A)

    mezo = _elem(window, "searchField")
    assert mezo.property("activeFocus") is True, (
        "a rácson gépelés nem adta át a fókuszt a keresőmezőnek"
    )
    assert _varj(qt_app, lambda: mezo.property("text") == "a"), (
        "a rácson gépelt 'a' nem került a keresőmezőbe"
    )
    assert mezo.property("activeFocus") is True, (
        "a rácson gépelés után a keresőmezőnek kell fókuszt kapnia"
    )
    # #7081: a keresés a gépelési szünet (150 ms) után indul
    assert _varj(qt_app, lambda: controller.searchQuery == "a"), (
        "a rácson gépelt 'a' nem indított keresést"
    )
