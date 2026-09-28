"""#3826 — a Fókuszos FF (`radsat`) Sugár csúszkája [-1, 1], alapja 0.

A csúszka korábban [0, 1] tartományú volt 0,3 alapértékkel — a natív
regiszter (`render/registry_data.py`, radsat „Size") és a mért spec
(`docs/specs/filters-decoded.md`, radsat `+0x28`) szerint [-1, 1], mért
alapállása 0 (ld. a golden `radsat__alap` eset, `test_effects.py`). A
negatív ág (a 684-es „min" mérőkészlet-eset) így felületről elérhetetlen
volt.

A próba VALÓDI egérhúzással viszi a csúszkát a két szélső állásba (nem az
`updateParamValue` közvetlen hívásával, mint a többi #316 próba), és a
tényleges `.picasa.ini` `filters=` láncát ellenőrzi.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.test_editor_panel_rendered_651 import _child
from tests.app.qml_functional.test_effect_sliders import _click

#: radsat=1,x,y,sugár,élesség — a katalógusban a Sugár a 3. vezérlő (0-indexű: 2)
_SUGAR_INDEX = 2


def _open_radsat_panel(window, qt_app):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("activeTab", 2)
    qt_app.processEvents()
    _click(panel.findChild(QObject, "effectRadsat"))
    qt_app.processEvents()
    assert panel.property("paramPanelActive") is True
    return panel


def _drag_slider_to_edge(window, qt_app, slider, *, to_left: bool) -> None:
    """Valódi press+move+release. A húzás vége szándékosan a csúszka
    kattintható területén KÍVÜL landol (messze balra/jobbra): amíg a
    fogantyú lenyomva, azaz a csúszka fogva tartja az egeret, a
    Qt Quick a mozgás vetületét a [0, 1] tartományra vágja — ez adja a
    pontos szélsőértéket, ahol egy önálló, terület-határon kívüli
    kattintás egyszerűen célt tévesztene."""
    height = slider.property("height")
    width = slider.property("width")
    press_pos = slider.mapToScene(QPointF(width / 2, height / 2)).toPoint()
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, press_pos
    )
    far_x = -500.0 if to_left else width + 500.0
    far_pos = slider.mapToScene(QPointF(far_x, height / 2)).toPoint()
    QTest.mouseMove(window, far_pos)
    qt_app.processEvents()
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, far_pos
    )
    qt_app.processEvents()


class TestARadsatSugarCsuszkaSzelsoErtekeiEgerrel:
    def test_bal_szelre_huzva_a_lancban_minusz_egy(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        panel = _open_radsat_panel(window, qt_app)
        slider = _child(panel, f"effectParamSlider{_SUGAR_INDEX}")

        _drag_slider_to_edge(window, qt_app, slider, to_left=True)
        assert slider.property("value") == -1.0

        _click(panel.findChild(QObject, "effectParamApplyButton"))
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "radsat=1,0.500000,0.500000,-1.000000,0.500000;" in ini_text

    def test_jobb_szelre_huzva_a_lancban_egy(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        panel = _open_radsat_panel(window, qt_app)
        slider = _child(panel, f"effectParamSlider{_SUGAR_INDEX}")

        _drag_slider_to_edge(window, qt_app, slider, to_left=False)
        assert slider.property("value") == 1.0

        _click(panel.findChild(QObject, "effectParamApplyButton"))
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "radsat=1,0.500000,0.500000,1.000000,0.500000;" in ini_text
