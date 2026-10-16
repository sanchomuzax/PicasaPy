"""#4500: Enter kilép a nézőből, ha az egykattintásos kilépés ki van kapcsolva."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRectF, Qt
from PySide6.QtTest import QTest
from tests.support.varakozas import var_feltetelre


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def test_enter_kilepesi_beallitas_es_vago_enter_utja(qml_app, qt_app):
    window, controller, _engine = qml_app
    window.show()
    window.requestActivate()
    window.setProperty("viewerOpen", True)

    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    assert _varj(qt_app, lambda: viewer.isVisible() and viewer.property("activeFocus"))

    # QTest a valódi ablak-billentyűeseményt küldi; a PhotoViewer az aktív
    # fókusz-eleme, így ugyanazt a Keys útvonalat kapja, mint használatkor.
    controller.setSingleClickExitEnabled(False)
    QTest.keyClick(window, Qt.Key.Key_Return)
    kikapcsolva_kilepett = _varj(
        qt_app, lambda: window.property("viewerOpen") is False
    )

    # Az engedélyezett beállítás mellett az Enter eddigi nézőbeli jelentése
    # (következő kép) maradjon meg.
    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", 0)
    assert _varj(qt_app, lambda: viewer.isVisible() and viewer.property("activeFocus"))
    controller.setSingleClickExitEnabled(True)
    QTest.keyClick(window, Qt.Key.Key_Return)
    bekapcsolva_tovabblepett = _varj(
        qt_app,
        lambda: window.property("viewerOpen") is True
        and viewer.property("currentIndex") == 1,
    )

    # A Vágás saját Enter-kezelője sorozat-vágás: alkalmazza a kijelölést,
    # a következő képre lép, és a vágó-módot megtartja.
    viewer.setProperty("currentIndex", 0)
    panel = window.findChild(QObject, "viewerEditorPanel")
    overlay = window.findChild(QObject, "cropOverlay")
    assert panel is not None and overlay is not None
    panel.setProperty("cropActive", True)
    assert _varj(qt_app, lambda: overlay.isVisible() and overlay.property("activeFocus"))
    overlay.setProperty("cropRect", QRectF(0.1, 0.1, 0.5, 0.5))
    overlay.setProperty("hasSelection", True)
    controller.setSingleClickExitEnabled(False)
    QTest.keyClick(window, Qt.Key.Key_Return)
    vagas_enter_megmaradt = _varj(
        qt_app,
        lambda: window.property("viewerOpen") is True
        and viewer.property("currentIndex") == 1
        and panel.property("cropActive") is True,
    )

    assert kikapcsolva_kilepett, (
        "kikapcsolt SingleClickExit mellett az Enter nem tért vissza a könyvtárba"
    )
    assert bekapcsolva_tovabblepett, (
        "bekapcsolt SingleClickExit mellett az Enter nem őrizte meg a következő-kép útját"
    )
    assert vagas_enter_megmaradt, (
        "a vágó eszköz Enter-kezelése nem alkalmazta a vágást és nem tartotta meg a módot"
    )
