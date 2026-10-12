"""#4634 — az XMP-arccímkék kiírása hatókör-választó párbeszéddel indul."""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtTest import QTest


def _var(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _elem(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(window, qt_app, elem) -> None:
    assert _var(qt_app, lambda: elem.width() > 0 and elem.height() > 0), (
        f"{elem.objectName()}: a vezérlő még nem épült fel"
    )
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )
    qt_app.processEvents()


def test_a_menu_parbeszedet_nyit_es_a_megse_nem_ir(qml_app, qt_app):
    window, controller, _engine = qml_app
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    qt_app.processEvents()

    menu_item = _elem(window, "menuToolsWriteXmpFaces")
    alapmagassag = window.height()
    for eltolas in (-5, 5):
        elvart_magassag = alapmagassag + eltolas
        window.resize(window.width(), elvart_magassag)
        assert _var(
            qt_app,
            lambda magassag=elvart_magassag: window.height() == magassag,
        )

        QMetaObject.invokeMethod(
            menu_item, "triggered", Qt.ConnectionType.DirectConnection
        )
        assert _var(
            qt_app,
            lambda: (dialog := window.findChild(QObject, "xmpFacesWriteDialog"))
            is not None
            and dialog.property("visible") is True,
        ), "a menüpontnak előbb a hatókör-választót kell megnyitnia"

        dialog = _elem(window, "xmpFacesWriteDialog")
        assert dialog.property("title") == "Write Face Tags"
        assert _elem(window, "xmpFacesWriteWarning").property("text").startswith(
            "Write faces or write all may take a long time."
        )
        assert _elem(window, "xmpFacesWriteSelected").property("text") == "Write Selected"
        kijelolt = _elem(window, "xmpFacesWriteSelected")
        assert kijelolt.property("enabled") is False
        assert float(kijelolt.property("opacity")) == 0.25
        assert _elem(window, "xmpFacesWriteFaces").property("text") == "Write Faces"
        assert _elem(window, "xmpFacesWriteAll").property("text") == "Write All"

        _kattints(window, qt_app, _elem(window, "xmpFacesWriteCancel"))
        assert _var(
            qt_app,
            lambda aktualis=dialog: aktualis.property("visible") is False,
        )
        assert controller.xmpFacesTotal == 0, "Mégse után nem indulhat el írás"
