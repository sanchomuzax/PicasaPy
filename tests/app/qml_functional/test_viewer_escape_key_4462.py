"""#4462: a néző Esc billentyűje valódi Qt billentyűeseménnyel zár."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_escreal_a_nezobol_a_konyvtarba_ter_vissza(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + magassag_eltolas)
    window.show()
    window.requestActivate()
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    assert _varj(qt_app, lambda: viewer.isVisible()), "a néző nem épült fel"
    assert viewer.property("activeFocus"), "a látható néző nem kapott fókuszt"

    QTest.keyClick(window, Qt.Key.Key_Escape)

    assert _varj(qt_app, lambda: window.property("viewerOpen") is False), (
        "a valódi Esc billentyűesemény nem tért vissza a könyvtárnézetbe"
    )
