"""Az „aa" mód fókuszváltása VALÓDI kattintással is megőrzi a festést
(#3649 — a PR #3679 átnézésének 4. lelete).

A `swapAaFocus` unit-tesztje (`test_aa_memoria_lanc_3014.py::TestASwapAaFocus`)
a Python-vezérlőt hívja közvetlenül; ez a teszt a TELJES utat méri: a
`viewerSwapFocus` szegmensre VALÓDI egérkattintással (`QTest.mouseClick`,
a jelenet-koordinátákon) — nem a `kattints()` kezelő közvetlen hívásával,
mert az akkor is zöld volna, ha a gomb takart vagy tiltott (ugyanaz a minta,
mint a `test_aa_utkozes_3014.py` és a `test_aa_kilepesi_utak_3014.py`
párbeszéd-gombjainál). A `swap_2up_focus`-on NINCS `mousedown` (#885): a
`TapHandler` felengedésre sül el, tehát a `QTest.mouseClick` (nyom+enged)
a valódi felhasználói gesztust adja.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

_VAMPIRSZEM_LANC = "ReanimatedEyeColor=1,6.000000,20.000000;"


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _nezot_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    nezo = _gyerek(window, "photoViewer")
    QMetaObject.invokeMethod(
        nezo, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    qt_app.processEvents()
    return nezo


def _szegmens(window, qt_app, nev):
    QMetaObject.invokeMethod(
        _gyerek(window, nev), "kattints", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _kattints(window, qt_app, nev):
    """Valódi egérkattintás a vezérlő közepére."""
    elem = _gyerek(window, nev)
    kozep = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _aa(window, qt_app):
    nezo = _nezot_nyit(window, qt_app)
    _szegmens(window, qt_app, "viewerLayoutAa")
    return nezo


class TestAFokuszvaltasKattintassal:
    """[code review lelet #4, PR #3679]: a `viewerSwapFocus` VALÓDI
    kattintása is a saját felén tartja a festést, oda-vissza váltva is."""

    def test_a_festes_a_sajat_felen_marad_oda_vissza_kattintva(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        nezo = _aa(window, qt_app)

        edit_ctl = nezo.property("editCtl")
        masik_hid = nezo.property("masodikEditCtl")

        edit_ctl.setChainValue(_VAMPIRSZEM_LANC)
        qt_app.processEvents()
        edit_ctl.paintStroke(0.5, 0.5)
        qt_app.processEvents()

        assert edit_ctl._paint_strokes()
        assert not masik_hid.controller._paint_strokes()

        _kattints(window, qt_app, "viewerSwapFocus")

        # a fókusz átment: a fő vezérlő MOST a párja (érintetlen, festetlen)
        # felét mutatja, a festés a memóriás oldalra került — NEM ürült ki.
        assert not edit_ctl._paint_strokes()
        assert masik_hid.controller._paint_strokes()

        _kattints(window, qt_app, "viewerSwapFocus")

        # oda-vissza kattintva a festés visszatér a saját (eredeti) oldalra.
        assert edit_ctl._paint_strokes()
        assert not masik_hid.controller._paint_strokes()

    def test_azonos_lancnal_is_cserel_kattintasra_ha_csak_a_festes_ter_el(
        self, qml_app, qt_app
    ):
        """[code review lelet #3]: a festés NEM része a `chainValue`-nak —
        azonos lánc mellett is cserélnie kell VALÓDI kattintásra, ha csak
        az egyik fél festett."""
        window, _controller, _engine = qml_app
        nezo = _aa(window, qt_app)

        edit_ctl = nezo.property("editCtl")
        masik_hid = nezo.property("masodikEditCtl")

        edit_ctl.setChainValue(_VAMPIRSZEM_LANC)
        qt_app.processEvents()
        masik_hid.controller.setChainValue(_VAMPIRSZEM_LANC)
        qt_app.processEvents()
        assert edit_ctl.property("chainValue") == masik_hid.property("chainValue")

        edit_ctl.paintStroke(0.5, 0.5)
        qt_app.processEvents()
        assert edit_ctl._paint_strokes()
        assert not masik_hid.controller._paint_strokes()

        _kattints(window, qt_app, "viewerSwapFocus")

        assert not edit_ctl._paint_strokes()
        assert masik_hid.controller._paint_strokes()
