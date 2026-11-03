"""#3247/#6443: a panel 4,5 csempesort valóban megjelenít az összevont fülön."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem


def _item(window, name: str) -> QQuickItem:
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nincs a jelenetben"
    return item


class TestOsszevontEffektfulMagassaga:
    def test_a_panel_megnovekszik_a_4_5_soros_racshoz(self, qml_app, qt_app):
        window = qml_app[0]
        panel = _item(window, "viewerEditorPanel")
        panel.setProperty("activeTab", 5)
        qt_app.processEvents()

        viewport = _item(window, "effectsGrid4Viewport")
        grid = _item(window, "effectsGrid4")
        first = _item(window, "effectMatte")
        next_row = _item(window, "effectRoundedEdges")
        row_pitch = next_row.y() - first.y()

        assert row_pitch > 0
        assert viewport.height() / row_pitch == pytest.approx(4.5, abs=0.03)
        assert grid.property("implicitHeight") > viewport.height()
        assert panel.property("tabContentTruncated") is False
        assert float(panel.property("mertTabPanelHeight")) >= viewport.height()
        assert float(panel.property("implicitHeight")) == pytest.approx(
            float(panel.property("chromeHeight"))
            + float(panel.property("mertTabPanelHeight"))
        )
