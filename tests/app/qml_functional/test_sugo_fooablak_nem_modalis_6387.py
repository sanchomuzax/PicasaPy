"""#6387: a főablakból nyitott súgó NEM modális, külön ablakban nyílik.

A súgó eddig a főablak rétegében élő, `modal: true` párbeszéd volt: amíg
nyitva állt, a főablak nem kapott bemenetet. Most az F1, a Shift+F1 és a
Súgó menü egy NEM modális súgóablakot nyit (`HelpWindow.qml`). Ez a főablak
fölött áll, a főablak közben kattintható marad, és egyetlen példány van:
újranyitáskor a meglévő ablak kerül előre.

A modális párbeszédekből nyitott súgó (`WindowHelp.qml`) külön példány, és
továbbra is alkalmazás-modális; azt a `test_sugo_kulon_ablakbol_3544.py` fedi.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints
from tests.app.qml_functional.test_aa_kilepesi_utak_3014 import _KilepesFigyelo
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre

#: A főablakból nyitott súgóablak objectName-je; a modális párbeszédek
#: súgóablakától (`helpWindow`) elkülönül.
FOABLAK_SUGO = "mainHelpWindow"


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _aktival(qt_app, ablak) -> None:
    ablak.requestActivate()
    assert _var(qt_app, lambda: ablak.property("active") is True), (
        "az ablak nem aktiválódott"
    )


def _foablak_sugoja(window):
    sugo = window.findChild(QObject, FOABLAK_SUGO)
    return sugo if sugo is not None and sugo.property("visible") is True else None


def _f1_a_foablakbol(window, qt_app):
    _aktival(qt_app, window)
    QTest.keyClick(window, Qt.Key.Key_F1)
    assert _var(qt_app, lambda: _foablak_sugoja(window) is not None), (
        "az F1 nem nyitott súgóablakot a főablakból"
    )
    return _foablak_sugoja(window)


def test_f1_a_foablakbol_nem_modalis_sugoablak_nyilik(qml_app, qt_app):
    window, controller, _engine = qml_app
    sugo = _f1_a_foablakbol(window, qt_app)

    assert sugo.property("modality") == Qt.WindowModality.NonModal, (
        "a főablakból nyitott súgó még modális"
    )
    belso = sugo.findChild(QObject, "helpDialog")
    assert belso is not None and belso.property("visible") is True
    assert belso.property("topic") == controller.property("helpHomeTopic")


def test_a_sugo_nyitva_a_foablak_gombja_mukodik(qml_app, qt_app):
    window, _controller, _engine = qml_app
    sugo = _f1_a_foablakbol(window, qt_app)

    gomb = window.findChild(QObject, "toolbarTreeViewButton")
    assert gomb is not None, "nincs fanézet-gomb a főablakban"
    assert gomb.property("aktiv") is False, "a próba feltétele: a fanézet még nincs bekapcsolva"

    _aktival(qt_app, window)
    kattints(window, qt_app, gomb)

    assert _var(qt_app, lambda: gomb.property("aktiv") is True), (
        "a főablak gombjára kattintás nem futott le, miközben a súgó nyitva volt"
    )
    assert sugo.property("visible") is True, "a gombnyomás bezárta a súgót"


def test_masodik_f1_utan_is_egyetlen_sugoablak_van(qml_app, qt_app):
    window, _controller, _engine = qml_app
    elso = _f1_a_foablakbol(window, qt_app)

    _aktival(qt_app, window)
    QTest.keyClick(window, Qt.Key.Key_F1)
    qt_app.processEvents()

    assert _foablak_sugoja(window) is elso, "a második F1 új súgóablakot nyitott"
    assert len(window.findChildren(QObject, FOABLAK_SUGO)) == 1, (
        "a főablakban egynél több súgóablak van"
    )


def test_a_foablak_bezarasa_a_sugoablakot_is_zarja(qml_app, qt_app):
    window, _controller, engine = qml_app
    _KilepesFigyelo(engine)
    sugo = _f1_a_foablakbol(window, qt_app)

    window.close()
    qt_app.processEvents()

    assert not window.isVisible(), "a főablak bezárása nem sikerült a próbában"
    assert sugo.property("visible") is False, (
        "a főablak bezárása után a súgóablak nyitva maradt"
    )
