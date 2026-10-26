"""#5949: a Filtered B&W panel natív színmezője valódi kattintásra nyílik."""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest

from support.varakozas import var_feltetelre


def _visual_item(root: QObject, object_name: str):
    """QML-vizuális gyerek keresése (a Repeater-delegátum is megtalálható)."""
    if root.objectName() == object_name:
        return root
    if hasattr(root, "childItems"):
        for child in root.childItems():
            found = _visual_item(child, object_name)
            if found is not None:
                return found
    return None


def _as_list(value):
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return list(value)


def _wait(qt_app, predicate, description: str) -> None:
    assert var_feltetelre(qt_app, predicate, 3.0), (
        f"határidőn belül nem teljesült: {description}"
    )


def _click(window, item, qt_app) -> None:
    point = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_filtered_bw_panel_starts_at_native_gray_after_real_tile_click(
    qml_app, qt_app, tmp_path, height_delta
):
    window, _controller, _engine = qml_app
    initial_height = window.height()
    window.setHeight(initial_height + height_delta)
    _wait(
        qt_app,
        lambda: window.height() == initial_height + height_delta,
        "az ablak felvette a paraméterezett magasságot",
    )

    window.setProperty("viewerOpen", True)
    _wait(qt_app, lambda: window.findChild(QObject, "photoViewer") is not None,
          "a valódi néző megnyílt")
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    panel = window.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    panel.setProperty("activeTab", 2)
    _wait(
        qt_app,
        lambda: panel.property("activeTab") == 2
        and (button := _visual_item(panel, "effectAnsel")) is not None
        and button.width() > 0
        and button.height() > 0,
        "a Filtered B&W csempe felépült",
    )

    button = _visual_item(panel, "effectAnsel")
    _click(window, button, qt_app)
    _wait(
        qt_app,
        lambda: panel.property("paramPanelActive") is True,
        "a színparaméteres effektpanel megnyílt kattintásra",
    )
    assert panel.property("paramEffectName") == "ansel"
    assert panel.property("paramEffectParams")[0]["color"] == "#545454"
    assert _as_list(panel.property("paramEffectValues")) == ["#545454"], (
        "az új Filtered B&W panel induló színét felülírta egy másik érték"
    )

    swatches = _visual_item(panel, "effectParamColor0")
    assert swatches is not None and swatches.isVisible()
    assert QColor(swatches.property("currentColor")).name() == "#545454"

    rendered = window.grabWindow()
    assert not rendered.isNull(), "a Filtered B&W panel nem rajzolódott ki"
    # A vizuális fában az első, szöveg nélküli palettacella valóban megjelent.
    white_swatch = _visual_item(swatches, "effectParamColor0Swatch0")
    assert white_swatch is not None and white_swatch.isVisible()
    center = white_swatch.mapToScene(
        QPointF(white_swatch.width() / 2, white_swatch.height() / 2)
    )
    dpr = rendered.devicePixelRatio()
    pixel = rendered.pixelColor(
        math.floor(center.x() * dpr), math.floor(center.y() * dpr)
    )
    assert max(
        abs(pixel.red() - 255), abs(pixel.green() - 255), abs(pixel.blue() - 255)
    ) <= 3, f"a kirajzolt, szöveg nélküli színminta nem fehér: {pixel.name()}"
    assert rendered.save(str(tmp_path / f"filtered-bw-panel-{height_delta}.png"))
