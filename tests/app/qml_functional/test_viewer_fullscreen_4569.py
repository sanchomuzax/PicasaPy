"""#4569: az F11 a nyitott képnéző teljes képernyős módját kapcsolja."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from tests.support.varakozas import var_feltetelre


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_f11_a_nezoben_be_es_kikapcsolja_a_teljes_kepernyot(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + magassag_eltolas)
    window.setVisibility(window.Visibility.Windowed)
    window.show()
    window.requestActivate()

    # #6700: a néző csak az első megnyitáskor épül fel
    window.setProperty("viewerOpen", True)
    assert _varj(
        qt_app, lambda: window.findChild(QObject, "photoViewer") is not None
    ), "a néző nem jött létre a megnyitáskor"
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    assert _varj(qt_app, lambda: viewer.isVisible()), "a néző nem épült fel"

    # Valódi kattintással aktiváljuk a néző ablakát; a sarok nem vezérlő,
    # a kattintás a billentyű útját nem befolyásolja.
    kattintasi_pont = viewer.mapToScene(
        QPointF(viewer.width() - 3, viewer.height() - 3)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kattintasi_pont.x()), round(kattintasi_pont.y())),
    )

    QTest.keyClick(window, Qt.Key.Key_F11)
    assert _varj(
        qt_app,
        lambda: window.visibility() == window.Visibility.FullScreen,
    ), "az F11 nem kapcsolta teljes képernyőre a nyitott nézőt"
    assert viewer.isVisible(), "az F11 bezárta a nézőt"

    QTest.keyClick(window, Qt.Key.Key_F11)
    assert _varj(
        qt_app,
        lambda: window.visibility() == window.Visibility.Windowed,
    ), "a második F11 nem állította vissza az ablakos nézetet"
    assert viewer.isVisible(), "a visszaállítás bezárta a nézőt"


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_f11_a_konyvtarnezetben_be_es_kikapcsolja_a_teljes_kepernyot(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + magassag_eltolas)
    window.setVisibility(window.Visibility.Windowed)
    window.show()
    window.requestActivate()
    assert window.property("viewerOpen") is False
    menu_bar = window.property("menuBar")
    assert menu_bar is not None and menu_bar.isVisible()

    QTest.keyClick(window, Qt.Key.Key_F11)

    assert _varj(
        qt_app,
        lambda: window.visibility() == window.Visibility.FullScreen,
    ), "az F11 nem kapcsolta teljes képernyőre a könyvtárnézetet"
    assert _varj(qt_app, lambda: not menu_bar.isVisible()), (
        "a könyvtári teljes képernyőben látható maradt a menüsáv"
    )

    QTest.keyClick(window, Qt.Key.Key_F11)

    assert _varj(
        qt_app,
        lambda: window.visibility() == window.Visibility.Windowed,
    ), "a második F11 nem állította vissza a könyvtárnézet ablakát"
    assert _varj(qt_app, lambda: menu_bar.isVisible()), (
        "a visszaállított könyvtárnézetben nem jelent meg a menüsáv"
    )
