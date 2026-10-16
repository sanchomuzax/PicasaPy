"""#4329: felső menüpontok — gyorsbillentyuk."""

from pathlib import Path

import pytest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _kijeloles,
    _magassag,
    _objektum,
    _varj,
)


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_ctrl_e_billentyu_a_meglevo_kuldesi_utvonalat_hivja(
    qml_app_email, qt_app, height_offset
):
    window, _controller, _engine = qml_app_email
    _magassag(window, height_offset)
    shortcut = _objektum(window, "emailShortcut")
    assert shortcut is not None
    assert shortcut.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: shortcut.property("enabled") is True)

    QTest.keyClick(window, Qt.Key.Key_E, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()

    assert _varj(
        qt_app,
        lambda: (
            _objektum(window, "emailChoiceDialog") is not None
            and _objektum(window, "emailChoiceDialog").property("visible")
        ),
    ), "a Ctrl+E nem jutott el a meglévő e-mail választóig"


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_ctrl_h_billentyu_a_talka_megtartasi_muveletet_hivja(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    shortcut = _objektum(window, "trayKeepSelectionShortcut")
    assert shortcut is not None
    assert shortcut.property("enabled") is False
    QTest.keyClick(window, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    assert controller.heldCount == 0

    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: shortcut.property("enabled") is True)
    QTest.keyClick(window, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier)

    assert _varj(qt_app, lambda: controller.heldCount == 1), (
        "a Ctrl+H nem rögzítette a kijelölt képet a képtálcán"
    )
    assert [Path(path) for path in controller.heldPaths] == [
        Path(controller.photos.filePathAt(0))
    ]
