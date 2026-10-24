"""#5684: a nyomtatási mód valódi kattintással váltható és újranyitható."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt, QTranslator
from PySide6.QtTest import QTest


def _child(root, name):
    child = root.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


@pytest.fixture
def magyar_forditas(qt_app):
    from picasapy.app import application

    translator = QTranslator(qt_app)
    qm = Path(application.__file__).parent / "i18n" / "picasapy_hu.qm"
    assert translator.load(str(qm)), f"a magyar fordítás nem tölthető be: {qm}"
    assert qt_app.installTranslator(translator)
    yield
    qt_app.removeTranslator(translator)


@pytest.fixture
def qml_app_magyar(magyar_forditas, qml_app):
    """A QML-fa a magyar fordító telepítése után épüljön fel."""
    return qml_app


def _hataridon_belul(feltetel, qt_app, *, masodperc=3.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(feltetel())


def _kattints(elem, qt_app):
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nincs kattintható mérete"
    )
    pont = elem.mapToScene(
        QPointF(elem.width() / 2, elem.height() / 2)
    ).toPoint()
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )
    qt_app.processEvents()


def _megnyit(window, qt_app):
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    QMetaObject.invokeMethod(
        _child(window, "menuFilePrint"),
        "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    dialog = _child(window, "printDialog")
    assert _hataridon_belul(
        lambda: dialog.property("visible") is True, qt_app
    ), "a Nyomtatás párbeszéd nem nyílt meg"
    return dialog


def test_valodi_kattintas_es_parbeszed_ujranyitas_visszaolvassa_a_modot(
    qml_app_magyar, qt_app
):
    window, _controller, _engine = qml_app_magyar
    dialog = _megnyit(window, qt_app)
    normal = _child(dialog, "printModeNormalRadio")
    optimalizalt = _child(dialog, "printModeOptimizedRadio")
    bezar = _child(dialog, "printCloseButton")

    assert normal.property("text") == "Normál"
    assert optimalizalt.property("text") == "Optimalizált"
    assert normal.property("checked") is True
    assert optimalizalt.property("checked") is False

    alapmagassag = int(dialog.height())
    for elteres in (-5, 0, 5):
        dialog.setHeight(alapmagassag + elteres)
        qt_app.processEvents()
        _kattints(optimalizalt, qt_app)
        assert _hataridon_belul(
            lambda radio=optimalizalt: radio.property("checked") is True,
            qt_app,
        ), "az Optimalizált mód nem kapcsolt be a valódi kattintásra"

        _kattints(bezar, qt_app)
        assert _hataridon_belul(
            lambda current_dialog=dialog: current_dialog.property("visible")
            is False,
            qt_app,
        ), "a Nyomtatás párbeszéd nem záródott be"
        dialog = _megnyit(window, qt_app)
        normal = _child(dialog, "printModeNormalRadio")
        optimalizalt = _child(dialog, "printModeOptimizedRadio")
        assert normal.property("checked") is False
        assert optimalizalt.property("checked") is True

        _kattints(normal, qt_app)
        assert _hataridon_belul(
            lambda radio=normal: radio.property("checked") is True, qt_app
        ), "a Normál mód nem kapcsolt be a valódi kattintásra"

    # A következő megnyitás már a Normál `2/0` párt olvassa vissza.
    _kattints(bezar, qt_app)
    assert _hataridon_belul(
        lambda: dialog.property("visible") is False, qt_app
    )
    dialog = _megnyit(window, qt_app)
    assert _child(dialog, "printModeNormalRadio").property("checked") is True
    assert _child(dialog, "printModeOptimizedRadio").property("checked") is False
