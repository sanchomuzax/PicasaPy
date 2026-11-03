"""#3263/#6443: a régi csempék és a Glimmer-effektek közös rácsot használnak."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem


def _item(window, name: str) -> QQuickItem:
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nincs a jelenetben"
    return item


def _visible_row_count(window) -> float:
    viewport = _item(window, "effectsGrid4Viewport")
    top = _item(window, "effectMatte")
    second_row = _item(window, "effectRoundedEdges")
    pitch = second_row.y() - top.y()
    assert pitch > 0
    return viewport.height() / pitch


def _open_combined_tab(window, panel, qt_app) -> None:
    window.setProperty("viewerOpen", True)
    panel.setProperty("activeTab", 5)
    effects = _item(window, "effectsColumn4")
    hatarido = time.monotonic() + 3
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if effects.property("visible"):
            return
        time.sleep(0.05)
    assert effects.property("visible") is True, "az összevont effektfül nem jelent meg"


class TestOsszevontRacs:
    def test_nincs_regi_bevezeto_es_egy_kozos_racs_van(self, qml_app, qt_app):
        window = qml_app[0]
        panel = _item(window, "viewerEditorPanel")
        _open_combined_tab(window, panel, qt_app)

        assert window.findChild(QObject, "legacyEffectsIntro") is None
        assert window.findChild(QObject, "editTabLegacy") is None
        effects = _item(window, "effectsColumn4")
        assert effects.property("visible") is True, (
            f"activeTab={panel.property('activeTab')}, "
            f"modeToolActive={panel.property('modeToolActive')}, "
            f"paramPanelActive={panel.property('paramPanelActive')}"
        )
        assert _item(window, "effectsGrid4").property("columns") == 3

    def test_nagyobb_feliratnal_is_4_5_sor_latszik(self, qml_app, qt_app):
        window = qml_app[0]
        panel = _item(window, "viewerEditorPanel")
        _open_combined_tab(window, panel, qt_app)

        label = _item(window, "effectMatteLabel")
        font = label.property("font")
        font.setPixelSize(22)
        label.setProperty("font", font)
        qt_app.processEvents()

        assert _visible_row_count(window) == pytest.approx(4.5, abs=0.03)
        assert panel.property("tabContentTruncated") is False
