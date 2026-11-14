"""#6571: a kurzor követi a vetítés lejátszás/szünet állapotát."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, Qt
from PySide6.QtGui import QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre


def _objektum(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _szam(ertek) -> int:
    return int(getattr(ertek, "value", ertek))


def _egerterulet(show):
    """A vetítőt fedő, lebegésre reagáló MouseArea."""
    talalatok = []
    for elem in show.findChildren(QObject):
        meta = elem.metaObject()
        accepted_buttons = elem.property("acceptedButtons")
        if (meta.indexOfProperty("cursorShape") >= 0
                and meta.indexOfProperty("hoverEnabled") >= 0
                and meta.indexOfProperty("acceptedButtons") >= 0
                and elem.property("hoverEnabled")
                and _szam(accepted_buttons) == 0):
            talalatok.append(elem)
    assert len(talalatok) == 1, (
        "a vetítőt fedő, gomb nélküli MouseArea nem egyértelmű: "
        f"{len(talalatok)} találat"
    )
    return talalatok[0]


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_space_elrejti_es_megjeleniti_a_kurzort(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    window.show()
    window.requestActivate()
    celmagassag = window.height() + magassag_eltolas

    QMetaObject.invokeMethod(
        window,
        "startSlideshow",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", -1),
        Q_ARG("QVariant", False),
    )
    show = _objektum(window, "slideshowView")
    try:
        # A teljes képernyős belépés után visszaváltunk ablakos módra, hogy
        # ugyanazt a viselkedést három, ténylegesen eltérő magasságon mérjük.
        window.setVisibility(QWindow.Visibility.Windowed)
        window.resize(window.width(), celmagassag)
        assert varj_feltetelre(
            qt_app, lambda: window.height() == celmagassag, 2.0
        ), f"az ablak nem vette fel a kért magasságot: {window.height()}"
        assert varj_feltetelre(
            qt_app,
            lambda: show.property("visible") is True
            and show.property("playing") is True,
        ), "a diavetítés nem indult el"
        egerterulet = _egerterulet(show)
        assert _szam(egerterulet.property("cursorShape")) == (
            Qt.CursorShape.BlankCursor.value
        ), (
            "lejátszás közben az egérmutató látható maradt"
        )

        QTest.keyClick(window, Qt.Key.Key_Space)
        assert varj_feltetelre(
            qt_app, lambda: show.property("playing") is False
        ), "a valódi Space leütés nem szüneteltette a vetítést"
        assert _szam(egerterulet.property("cursorShape")) == (
            Qt.CursorShape.ArrowCursor.value
        ), (
            "szünetben nem jelent meg az egérmutató"
        )

        QTest.keyClick(window, Qt.Key.Key_Space)
        assert varj_feltetelre(
            qt_app, lambda: show.property("playing") is True
        ), "a valódi Space leütés nem folytatta a vetítést"
        assert _szam(egerterulet.property("cursorShape")) == (
            Qt.CursorShape.BlankCursor.value
        ), (
            "folytatáskor látható maradt az egérmutató"
        )

        # A vetítőt fedő MouseArea a mutató mozgatására továbbra is előhozza
        # a sávot; a gombok fölött a nyíl marad látható.
        QTest.mouseMove(window, QPoint(window.width() // 2, window.height() // 2))
        controls = _objektum(window, "slideshowControls")
        assert varj_feltetelre(
            qt_app, lambda: controls.property("opacity") >= 0.99, 3.0
        ), "az egérmozgatás nem hozta elő a vezérlősávot"
        sav = window.findChild(QQuickItem, "slideshowControls")
        assert sav is not None
        sav_kozep = sav.mapToScene(sav.boundingRect().center())
        QTest.mouseMove(window, QPoint(round(sav_kozep.x()), round(sav_kozep.y())))
        lebeges = _objektum(window, "slideshowControlsHover")
        assert varj_feltetelre(qt_app, lambda: lebeges.property("hovered")), (
            "a mutató nem lépett a vezérlősáv fölé"
        )
        assert _szam(egerterulet.property("cursorShape")) == (
            Qt.CursorShape.ArrowCursor.value
        ), (
            "a vezérlősáv fölött is rejtve maradt az egérmutató"
        )

        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert varj_feltetelre(
            qt_app, lambda: show.property("visible") is False
        ), "az Escape nem lépett ki a vetítésből"
        assert window.cursor().shape() == Qt.CursorShape.ArrowCursor, (
            "kilépés után a főablak nem állította vissza a nyíl-kurzort"
        )
    finally:
        if show.property("visible"):
            QMetaObject.invokeMethod(show, "stop", Qt.ConnectionType.DirectConnection)
