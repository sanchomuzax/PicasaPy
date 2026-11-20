"""#7285: a vetítés képfelületén az egérkattintás kapcsolja a szünetet."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre


def _objektum(window, nev: str) -> QQuickItem:
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(window, qt_app, elem: QQuickItem, x: float, y: float, button):
    pont = elem.mapToScene(QPointF(x, y))
    QTest.mouseClick(
        window,
        button,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_kepkattintas_szunet_es_folytat_es_a_savon_nem_valt(
    qml_app, qt_app, magassag_eltolas
):
    window, controller, _engine = qml_app
    controller.setSlideshowLoop(True)
    controller.setSlideshowSeconds(60)
    window.show()
    window.setVisibility(QWindow.Visibility.Windowed)
    celmagassag = window.height() + magassag_eltolas
    window.resize(window.width(), celmagassag)
    assert varj_feltetelre(
        qt_app, lambda: window.height() == celmagassag, 3.0
    ), f"az ablak nem vette fel a kért magasságot: {window.height()}"

    window.startSlideshow(0, False)
    show = _objektum(window, "slideshowView")
    assert varj_feltetelre(
        qt_app,
        lambda: show.property("visible") and show.property("playing"),
        3.0,
    ), "a normál vetítés nem indult el"

    _kattints(window, qt_app, show, show.width() / 2, show.height() / 2,
              Qt.MouseButton.LeftButton)
    assert show.property("playing") is False, (
        "a kép közepére kattintás nem szüneteltette a vetítést"
    )

    kattinthato = _objektum(window, "slideshowPlaybackToggleArea")
    auto2 = _objektum(window, "slideshowAuto2Area")
    assert auto2.height() == 14, "az eredeti felső 14 px-es terület megváltozott"
    assert kattinthato.width() == show.width()
    assert kattinthato.height() == pytest.approx(show.height() - 97), (
        "szünetben a kattintási terület alsó határa nem H-97"
    )

    # A felső 14 px az új terület része; egy valódi press+release egyetlen
    # folytatást és egyetlen azonnali dia-lépést eredményez.
    index_szu_net_elott = show.property("currentIndex")
    _kattints(window, qt_app, kattinthato, kattinthato.width() / 2, 7,
              Qt.MouseButton.LeftButton)
    assert show.property("playing") is True, (
        "a felső 14 px-es átfedés nem folytatta a vetítést"
    )
    assert show.property("currentIndex") == index_szu_net_elott + 1, (
        "a felső terület kattintása nem pontosan egy folytatást váltott ki"
    )

    _kattints(window, qt_app, show, show.width() / 2, show.height() / 2,
              Qt.MouseButton.LeftButton)
    assert show.property("playing") is False, "a második képkattintás nem szüneteltetett"

    sav = _objektum(window, "slideshowControls")
    # A próbapont a sáv gombmentes helyére esik (az eredeti képikon/csúszka
    # helye, #7281): a sáv közepe az átrendezés óta a ▶▶ gombra esne, ami
    # szándékosan lép, és a sávon belüli kattintás hatását elfedné.
    ures_hely = _objektum(window, "slideshowImageSliderSlot")
    sav_pont = show.mapFromScene(
        ures_hely.mapToScene(
            QPointF(ures_hely.width() / 2, ures_hely.height() / 2)
        )
    )
    assert sav.contains(sav.mapFromScene(show.mapToScene(sav_pont))), (
        "a próbapont nem esik a tényleges vezérlősávba"
    )
    assert not kattinthato.contains(kattinthato.mapFromScene(show.mapToScene(sav_pont))), (
        "a szünetelt kattintási terület ráfed a vezérlősávra"
    )
    index_sav_elott = show.property("currentIndex")
    _kattints(window, qt_app, show, sav_pont.x(), sav_pont.y(),
              Qt.MouseButton.LeftButton)
    assert show.property("playing") is False, (
        "a vezérlősávon levő kattintást a képfelület is kapcsolta"
    )
    assert show.property("currentIndex") == index_sav_elott

    _kattints(window, qt_app, show, show.width() / 2, show.height() / 2,
              Qt.MouseButton.RightButton)
    assert show.property("playing") is False, "a jobb kattintás megváltoztatta a vetítés állapotát"
