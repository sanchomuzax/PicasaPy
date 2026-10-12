"""#4560: a Sixties, Polaroid és Lekerekített szél színmintájának felirata
„Háttérszín” (az eredeti Picasa `_clrsw` táblája szerint), nem „Külső szín”.

A főablak kirajzolt felületét használja: a hatást valódi egérkattintással
nyitja meg, és a nézőterület magasságát ±5 képponttal is megmozgatja.
A magyar feliratot a fordítóval együtt tölti be (`qml_app_email`).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest


def _find_item(root, object_name):
    if root.objectName() == object_name:
        return root
    for child in root.childItems():
        found = _find_item(child, object_name)
        if found is not None:
            return found
    return None


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _click_item(window, item, qt_app):
    """Valódi egérkattintás az elem felépült, aktuális helyén."""
    scene_pos = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=scene_pos.toPoint(),
    )
    qt_app.processEvents()


@pytest.mark.parametrize(
    ("tile", "active_tab", "effekt"),
    (
        ("effectSixties", 3, "sixties"),
        ("effectPolaroid", 4, "polaroid"),
        ("effectRoundedEdges", 5, "roundededges"),
    ),
)
def test_hatter_szin_mintaja_hatterszin_feliratot_kap(
    qml_app_email, qt_app, tile, active_tab, effekt
):
    window, _controller, _engine = qml_app_email
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()

    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("activeTab", active_tab)
    qt_app.processEvents()
    _click_item(window, panel.findChild(QObject, tile), qt_app)
    assert panel.property("paramPanelActive") is True, effekt

    kulcsok = [
        param["key"] for param in _variant(panel.property("paramEffectParams"))
    ]
    assert "outer_color" in kulcsok, f"{effekt}: nincs színválasztó"
    szin_sor = kulcsok.index("outer_color")

    original_height = window.height()
    # A ±5 px ablakmagasság-változásnál is ugyanazt a feliratot kell látni.
    for delta in (5, 0, -5):
        window.setHeight(original_height + delta)
        qt_app.processEvents()
        szin_felirat = _find_item(
            panel, f"effectParamColorLabel{szin_sor}"
        )
        assert szin_felirat is not None and szin_felirat.isVisible(), (
            f"{effekt} (magasság {delta:+d}): nincs látható színfelirat"
        )
        assert szin_felirat.property("text") == "Háttérszín", (
            f"{effekt} (magasság {delta:+d}): {szin_felirat.property('text')!r}"
        )
    window.setHeight(original_height)
    qt_app.processEvents()
