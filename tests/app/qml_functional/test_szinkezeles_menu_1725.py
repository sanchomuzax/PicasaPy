"""A `Nézet ▸ Színkezelés használata` menütétel valódi kattintásra (#1725).

A tétel korábban `placeholder` volt: látszott, de nem csinált semmit. A
teszt a VALÓDI kattintást utánozza (`toggle` + `triggered`), mert épp a
`toggle` az, ami a `checked` kötését eldobja (#2377/#1471) — enélkül a
hibás QML mellett is zöld lenne.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _kattints(item, qt_app) -> None:
    QMetaObject.invokeMethod(item, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def test_a_tetel_kapcsol_es_a_pipa_koveti(qml_app, qt_app):
    window, controller, _engine = qml_app
    tetel = _gyerek(window, "menuViewColorManagement")

    assert tetel.property("checkable") is True
    assert tetel.property("enabled") is True, "a tétel nem lehet szürke (placeholder)"
    assert controller.colorManagement is False, "az alapállapot KI (mérve)"
    assert tetel.property("checked") is False

    _kattints(tetel, qt_app)
    assert controller.colorManagement is True, "a kattintás nem kapcsolt"
    assert tetel.property("checked") is True

    _kattints(tetel, qt_app)
    assert controller.colorManagement is False
    assert tetel.property("checked") is False, (
        "a pipa nem követte a kikapcsolást — a checked kötését a toggle eldobta"
    )
