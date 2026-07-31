"""#337: Kitöltő fény csúszka a Gyakori javítások fülön is.

Az eredeti Picasa Alapvető javítások fülén az ikonrács alatt ott a Kitöltő
fény csúszka — ez az egyetlen csúszka azon a fülön, és a napi használat
egyik legfontosabb eszköze. Nálunk csak a Finomhangolás fülön volt.

A két csúszka NEM két külön beállítás: ugyanazt az értéket mutatja és
állítja, bármelyiket húzva a másik követi.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject


@pytest.fixture
def panel(qml_app):
    window, _controller, _engine = qml_app
    editor = window.findChild(QObject, "viewerEditorPanel")
    assert editor is not None, "editorPanel nem található"
    return editor


def _slider(panel_item, name):
    found = panel_item.findChild(QObject, name)
    assert found is not None, f"{name} nem található"
    return found


class TestFillLightOnBothTabs:
    def test_fixes_tab_has_a_fill_light_slider(self, panel):
        assert panel.findChild(QObject, "fixesFillSlider") is not None

    def test_finetune_tab_keeps_its_slider(self, panel):
        assert panel.findChild(QObject, "finetuneFillSlider") is not None

    def test_the_two_sliders_share_the_range(self, panel):
        fixes = _slider(panel, "fixesFillSlider")
        finetune = _slider(panel, "finetuneFillSlider")
        assert fixes.property("from") == finetune.property("from")
        assert fixes.property("to") == finetune.property("to")

    def test_moving_the_fixes_slider_moves_the_finetune_one(self, panel, qt_app):
        fixes = _slider(panel, "fixesFillSlider")
        finetune = _slider(panel, "finetuneFillSlider")
        fixes.setProperty("value", 0.4)
        qt_app.processEvents()
        assert finetune.property("value") == pytest.approx(0.4, abs=1e-6)

    def test_moving_the_finetune_slider_moves_the_fixes_one(self, panel, qt_app):
        fixes = _slider(panel, "fixesFillSlider")
        finetune = _slider(panel, "finetuneFillSlider")
        finetune.setProperty("value", 0.7)
        qt_app.processEvents()
        assert fixes.property("value") == pytest.approx(0.7, abs=1e-6)

    def test_panel_state_syncs_both(self, panel, qt_app):
        """A mentett érték betöltése (kép nyitása/lapozás) mindkettőt állítja."""
        panel.setProperty("fillLight", 0.25)
        qt_app.processEvents()
        assert _slider(panel, "fixesFillSlider").property("value") == pytest.approx(
            0.25, abs=1e-6
        )
        assert _slider(panel, "finetuneFillSlider").property(
            "value"
        ) == pytest.approx(0.25, abs=1e-6)

    def test_each_slider_lives_on_its_own_tab(self, panel):
        """A csúszkák a saját fülük oszlopában élnek — a fül váltása így
        magától mutatja/rejti őket.

        A `visible` tulajdonságot NEM mérjük: az a teljes láthatósági láncot
        tükrözi, és a szerkesztő-panel a teszt-környezetben eleve rejtett
        (a néző nincs megnyitva). A szülő-kapcsolat a lényeg.
        """
        tools_column = panel.findChild(QObject, "toolsColumn")
        finetune_column = panel.findChild(QObject, "finetuneColumn")
        assert tools_column is not None and finetune_column is not None

        assert tools_column.findChild(QObject, "fixesFillSlider") is not None
        assert tools_column.findChild(QObject, "finetuneFillSlider") is None
        assert finetune_column.findChild(QObject, "finetuneFillSlider") is not None
        assert finetune_column.findChild(QObject, "fixesFillSlider") is None
