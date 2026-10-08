"""#4696 — Ctrl+9 a szerkesztőnézet bal fiókját kapcsolja."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 3.0) -> None:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    qt_app.processEvents()
    assert feltetel(), uzenet


def _elem(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a főablakban nincs {nev}"
    return elem


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_ctrl9_toggles_editor_drawer_and_is_inactive_in_library(
    qml_app, qt_app, magassag_elteres
):
    window, controller, _engine = qml_app
    celmagassag = window.height() + magassag_elteres
    window.setHeight(celmagassag)
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    assert window.height() == celmagassag, (
        f"a főablak nem vette fel a kért {celmagassag} px magasságot: "
        f"{window.height()} px"
    )

    window.setProperty("selectedIndex", 0)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("viewerOpen", True)
    viewer = _elem(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    controller.setEditorControlsVisible(True)
    _varj(qt_app, viewer.isVisible, "a szerkesztőnézet nem nyílt meg")

    menupipa = _elem(window, "menuViewEditControls")
    assert controller.editorControlsVisible is True
    assert menupipa.property("checked") is True

    QTest.keyClick(window, Qt.Key.Key_9, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    _varj(
        qt_app,
        lambda: controller.editorControlsVisible is False,
        "a Ctrl+9 nem rejtette el a szerkesztő bal fiókját",
    )
    _varj(
        qt_app,
        lambda: menupipa.property("checked") is False,
        "a Nézet-menü pipája nem követte a bezárt fiókot",
    )

    QTest.keyClick(window, Qt.Key.Key_9, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    _varj(
        qt_app,
        lambda: controller.editorControlsVisible is True,
        "a második Ctrl+9 nem nyitotta vissza a szerkesztő bal fiókját",
    )
    _varj(
        qt_app,
        lambda: menupipa.property("checked") is True,
        "a Nézet-menü pipája nem követte a kinyitott fiókot",
    )

    window.setProperty("viewerOpen", False)
    _varj(qt_app, lambda: not viewer.isVisible(), "a szerkesztőnézet nem zárult be")
    keresomezo = _elem(window, "searchField")
    keresomezo.forceActiveFocus()
    _varj(
        qt_app,
        lambda: keresomezo.property("activeFocus") is True,
        "a könyvtárnézeti keresőmező nem kapott fókuszt",
    )
    elotte = str(keresomezo.property("text") or "")

    QTest.keyClick(window, Qt.Key.Key_9, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()

    assert controller.editorControlsVisible is True, (
        "a könyvtárnézeti Ctrl+9 megváltoztatta a szerkesztőfiók állapotát"
    )
    assert menupipa.property("checked") is True
    assert keresomezo.property("activeFocus") is True, (
        "a könyvtárnézeti Ctrl+9 elvette a fókuszt a keresőmezőtől"
    )
    assert str(keresomezo.property("text") or "") == elotte
