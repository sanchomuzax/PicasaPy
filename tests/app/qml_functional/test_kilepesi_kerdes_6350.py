"""#6350: a kilépési kérdés az eredeti két gombját mutatja, „Ne kérdezze meg
újra” nélkül — a háttérmunka miatti kérdés nem nyomható el."""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def test_a_kilepesi_kerdesben_ket_gomb_van_es_nincs_jelolo(qml_app, qt_app):
    window, _controller, _engine = qml_app
    betolto = window.findChild(QObject, "exitConfirmDialogLoader")
    assert betolto is not None
    QMetaObject.invokeMethod(betolto, "askExit", Qt.ConnectionType.DirectConnection)
    for _ in range(5):
        qt_app.processEvents()

    def lathato(nev: str) -> bool:
        elem = window.findChild(QObject, nev)
        assert elem is not None, nev
        return bool(elem.property("visible"))

    try:
        assert lathato("exitYesButton")
        assert lathato("exitNoButton")
        assert not lathato("exitCancelButton")
        assert not lathato("exitRememberCheck")
    finally:
        kerdes = window.findChild(QObject, "exitConfirm")
        if kerdes is not None:
            QMetaObject.invokeMethod(kerdes, "close", Qt.ConnectionType.DirectConnection)
            qt_app.processEvents()
