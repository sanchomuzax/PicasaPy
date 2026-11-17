"""#7135: az üres szövegű Enter a címkepanelen a „nincs beírt szöveg” súgót mutatja.

Az eredetiben az Enter (`editselected`, `0x0063acd0`) a `0x0063bb30`-ra jut;
üres vagy csak szóközt tartalmazó szövegnél a `TagPanel::notify_notext`
modális üzenet jelenik meg (`0x0063bb85-0x0063bbd9`), és semmi nem íródik.

Valódi billentyűtesztek a kirajzolt főablakon (`Return`), a nézőterület
±5 képpontos mozgatásával; a `submit()` függvényt egyik sem hívja közvetlenül.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre, varj_kattinthatora

_NINCS_BEIRT_SZOVEG_SUGO = (
    "Type in a tag (word or phrase) in the text box to the left "
    "of the button you just pressed.\n\n"
    "Then press the button again to add the tag to the selected "
    "items.\n\n"
    "(TIP: Press <ENTER> after you type in your tag to "
    "automatically add the tag without pressing the button)"
)


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    found = window.findChild(QObject, name)
    assert found is not None, f"A kirajzolt felületen nincs ilyen elem: {name}"
    return found


def _click(window, item, qt_app):
    varj_kattinthatora(window, item)
    center = item.mapToScene(
        QPointF(item.width() / 2, item.height() / 2)
    ).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=center)
    qt_app.processEvents()


def _cimkek(controller, fajl: str):
    from picasapy.metadata import read_file_metadata

    return read_file_metadata(Path(controller._roots[0]) / fajl).keywords


def _felkeszit(window, qt_app, magassag_eltolas: int):
    """Kijelöli az első (írható) képet, megnyitja a Címkék-panelt, és
    fókuszba hozza a beviteli mezőt valódi egérkattintással."""
    window.requestActivate()
    assert varj_feltetelre(qt_app, lambda: window.isActive(), 5.0)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    window.setProperty("activeDrawerTab", "tags")
    assert varj_feltetelre(
        qt_app, lambda: window.findChild(QObject, "tagInput") is not None, 5.0
    )
    window.setHeight(int(window.height()) + magassag_eltolas)
    qt_app.processEvents()
    mezo = _item(window, "tagInput")
    assert varj_feltetelre(qt_app, lambda: mezo.isVisible(), 5.0)
    assert mezo.property("enabled") is True
    _click(window, mezo, qt_app)
    assert varj_feltetelre(
        qt_app, lambda: mezo.property("activeFocus") is True, 3.0
    ), "a címkemező nem kapott fókuszt"
    assert mezo.property("text") == ""
    return mezo


def _lenyomja(window, qt_app, szoveg: str) -> None:
    for karakter in szoveg:
        if karakter == " ":
            kulcs = Qt.Key.Key_Space
        else:
            kulcs = Qt.Key(ord(karakter.upper()))
        QTest.keyClick(window, kulcs)
    QTest.keyClick(window, Qt.Key.Key_Return)
    qt_app.processEvents()


def _sugo_bezar(window, qt_app, sugo) -> None:
    sugo.close()
    assert varj_feltetelre(qt_app, lambda: not sugo.property("visible"), 3.0)


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
class TestUresEnterSugo7135:
    def test_az_ures_mezo_entere_a_nincs_beirt_szoveg_sugot_mutatja(
        self, qml_app, qt_app, magassag_eltolas
    ):
        window, controller, _engine = qml_app
        _felkeszit(window, qt_app, magassag_eltolas)
        sugo = _item(window, "tagNoTextDialog")
        assert sugo.property("visible") is False
        elotte = _cimkek(controller, "a.jpg")

        QTest.keyClick(window, Qt.Key.Key_Return)
        qt_app.processEvents()

        assert varj_feltetelre(
            qt_app, lambda: bool(sugo.property("visible")), 3.0
        ), "az üres Enter nem nyitotta meg a „nincs beírt szöveg” ablakot"
        assert _item(window, "tagNoTextMessage").property("text") == (
            _NINCS_BEIRT_SZOVEG_SUGO
        )
        assert sugo.property("modal") is True
        assert _cimkek(controller, "a.jpg") == elotte
        _sugo_bezar(window, qt_app, sugo)

    def test_a_csak_szokozos_mezo_entere_is_a_sugot_mutatja_es_nem_ir(
        self, qml_app, qt_app, magassag_eltolas
    ):
        window, controller, _engine = qml_app
        mezo = _felkeszit(window, qt_app, magassag_eltolas)
        sugo = _item(window, "tagNoTextDialog")
        elotte = _cimkek(controller, "a.jpg")

        _lenyomja(window, qt_app, "   ")

        assert varj_feltetelre(
            qt_app, lambda: bool(sugo.property("visible")), 3.0
        ), "a szóközös Enter nem nyitotta meg a „nincs beírt szöveg” ablakot"
        assert _item(window, "tagNoTextMessage").property("text") == (
            _NINCS_BEIRT_SZOVEG_SUGO
        )
        assert _cimkek(controller, "a.jpg") == elotte
        # a mai viselkedés a mezőre: a szóközök nem törlődnek, semmi nem íródik
        assert mezo.property("text").strip() == ""
        _sugo_bezar(window, qt_app, sugo)

    def test_a_nem_ures_szoveg_entere_hozzaad_es_nem_nyit_ablakot(
        self, qml_app, qt_app, magassag_eltolas
    ):
        window, controller, _engine = qml_app
        mezo = _felkeszit(window, qt_app, magassag_eltolas)
        sugo = _item(window, "tagNoTextDialog")
        assert _cimkek(controller, "a.jpg") == ()

        _lenyomja(window, qt_app, "vitorlas")

        assert varj_feltetelre(
            qt_app, lambda: _cimkek(controller, "a.jpg") == ("vitorlas",), 10.0
        ), "a nem üres szövegű Enter a mai módon hozzáadja a címkét"
        assert sugo.property("visible") is False
        assert mezo.property("text") == ""

    def test_a_plusz_gomb_ures_szovegnel_tiltott_marad(
        self, qml_app, qt_app, magassag_eltolas
    ):
        """Az eredeti `+` gombjának állapota nem mért (B3), ezért a mai
        tiltás nem változhat."""
        window, _controller, _engine = qml_app
        _felkeszit(window, qt_app, magassag_eltolas)
        gomb = _item(window, "tagAddButton")
        assert gomb.property("enabled") is False
        sugo = _item(window, "tagNoTextDialog")
        assert sugo.property("visible") is False
