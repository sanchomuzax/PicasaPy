"""#6888: a Print Layout a főablakban váltja le a könyvtárnézetet."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit


def _elem(window, object_name: str):
    elem = _objektum(window, object_name)
    assert elem is not None, f"{object_name} nem található"
    return elem


def _kijelol(window, qt_app) -> list[int]:
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    return [0, 1]


def _kijelolt_sorok(window) -> list[int]:
    ertek = window.property("selectedIndexes")
    nyers = ertek.toVariant() if hasattr(ertek, "toVariant") else ertek
    return [int(sor) for sor in nyers]


def _nyomtatasi_nezet(window, qt_app):
    assert varj_feltetelre(
        qt_app, lambda: _objektum(window, "printDialog") is not None
    ), "a nyomtatási nézet nem épült fel"
    return _elem(window, "printDialog")


def _ellenoriz_beagyazott_nezet(window, qt_app, kijeloles: list[int]):
    nezet = _nyomtatasi_nezet(window, qt_app)
    assert isinstance(nezet, QQuickItem), (
        "a nyomtatási nézet gyökere külön ablak, nem a főablak tartalma"
    )
    assert nezet.window() == window, "a nyomtatási nézet külön ablakban él"
    assert nezet.property("visible") is True
    assert _elem(window, "mainSplit").property("visible") is False, (
        "a könyvtárnézet vagy a bal hasáb látszik a nyomtatási nézet alatt"
    )
    assert _elem(window, "trayBar").property("visible") is False, (
        "az infósáv/tálca látszik nyomtatási nézetben"
    )
    assert _elem(window, "printPrinterBox") is not None, (
        "a nyomtatási nézetből hiányzik a nyomtatóválasztó"
    )
    assert _kijelolt_sorok(window) == kijeloles
    return nezet


def _talcaval_nyit(window, qt_app):
    gomb = _elem(window, "trayPrintButton")
    assert gomb.property("enabled") is True
    _kattints(qt_app, gomb)


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_talca_print_a_fomablakba_valt_es_cancellel_visszater(
    qml_app, qt_app, height_delta
):
    window, _controller, _engine = qml_app
    kijeloles = _kijelol(window, qt_app)
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    _talcaval_nyit(window, qt_app)
    _ellenoriz_beagyazott_nezet(window, qt_app, kijeloles)

    cancel = _elem(window, "printCloseButton")
    _kattints(qt_app, cancel)

    assert varj_feltetelre(
        qt_app, lambda: _elem(window, "printDialog").property("visible") is False
    ), "a Cancel nem zárta be a nyomtatási nézetet"
    assert _elem(window, "mainSplit").property("visible") is True
    assert _kijelolt_sorok(window) == kijeloles


def test_file_print_valodi_kattintassal_a_fomablakba_valt(qml_app, qt_app):
    window, _controller, _engine = qml_app
    kijeloles = _kijelol(window, qt_app)
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, "&File")
    _kattints(qt_app, _elem(window, "menuFilePrint"))

    _ellenoriz_beagyazott_nezet(window, qt_app, kijeloles)


def test_escape_visszavisz_a_konyvtarnezetbe(qml_app, qt_app):
    window, _controller, _engine = qml_app
    kijeloles = _kijelol(window, qt_app)
    _talcaval_nyit(window, qt_app)
    _ellenoriz_beagyazott_nezet(window, qt_app, kijeloles)

    QTest.keyClick(window, Qt.Key.Key_Escape)

    assert varj_feltetelre(
        qt_app, lambda: _elem(window, "printDialog").property("visible") is False
    ), "az Escape nem zárta be a nyomtatási nézetet"
    assert _elem(window, "mainSplit").property("visible") is True
    assert _kijelolt_sorok(window) == kijeloles


def test_sikeres_nyomtatas_utan_visszater_a_konyvtarnezetbe(qml_app, qt_app):
    window, _controller, _engine = qml_app
    kijeloles = _kijelol(window, qt_app)
    _talcaval_nyit(window, qt_app)
    nezet = _ellenoriz_beagyazott_nezet(window, qt_app, kijeloles)
    nyomtato_vezerlo = nezet.property("printCtl")

    nyomtato_vezerlo.printFinished.emit("file:///print/6888.pdf")
    qt_app.processEvents()

    assert nezet.property("visible") is False, (
        "a sikeres nyomtatás után a Print Layout nyitva maradt"
    )
    assert _elem(window, "mainSplit").property("visible") is True
    assert _kijelolt_sorok(window) == kijeloles
