"""Renderelt elrendezés és geometria az Effekt-térszelvényhez (#6522)."""

# SAJÁT FUNKCIÓ (#6522): a felületi próba az eredeti Picasában nem létező dobozt méri.

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, Q_ARG, QMetaObject, Qt

from tests.support.varakozas import var_feltetelre


@pytest.mark.parametrize("magassag", (935, 940, 945))
def test_a_doboz_a_histogram_felett_marad_es_nem_takarja_a_szerkeszto_sorat(
    qml_app, qt_app, tmp_path, magassag
):
    window, _app_controller, engine = qml_app
    effect_controller = engine.rootContext().contextProperty("effectSliceController")
    effect_controller.setMode("always")
    window.resize(1280, magassag)
    window.show()
    assert var_feltetelre(qt_app, lambda: abs(window.height() - magassag) < 1, 5.0)
    window.setProperty("viewerOpen", True)
    window.setProperty("selectedIndex", 0)

    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    assert QMetaObject.invokeMethod(
        viewer,
        "show",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
    )

    drawer = window.findChild(QObject, "viewerLeftDrawer")
    box = window.findChild(QObject, "viewerEffectSliceBox")
    histogram = window.findChild(QObject, "viewerHistogramBox")
    editor_panel = window.findChild(QObject, "viewerEditorPanel")
    undo_row = window.findChild(QObject, "editorGlobalUndoRow")
    assert all((drawer, box, histogram, editor_panel, undo_row))
    assert var_feltetelre(qt_app, lambda: box.isVisible(), 5.0)
    assert box.property("width") == pytest.approx(238)
    assert box.property("height") == pytest.approx(144)

    box_top_left = box.mapToScene(QPointF(0, 0))
    box_bottom_left = box.mapToScene(QPointF(0, box.property("height")))
    histogram_top_left = histogram.mapToScene(QPointF(0, 0))
    drawer_top_left = drawer.mapToScene(QPointF(0, 0))
    undo_top_left = undo_row.mapToScene(QPointF(0, 0))
    assert box_top_left.x() - drawer_top_left.x() == pytest.approx(20, abs=0.5)
    assert histogram_top_left.x() - drawer_top_left.x() == pytest.approx(20, abs=0.5)
    assert histogram_top_left.y() - box_bottom_left.y() == pytest.approx(4, abs=0.5)
    assert undo_top_left.y() + undo_row.property("height") <= box_top_left.y() + 0.5
    assert editor_panel.property("bottomReserve") == pytest.approx(
        histogram.property("height") + 4 + box.property("height") + 4
    )

    assert var_feltetelre(
        qt_app,
        lambda: window.findChild(QObject, "effectSliceSurface")
        .property("surfaceData")
        .get("kind")
        == "identity",
        3.0,
    )
    image = window.grabWindow()
    assert not image.isNull()
    assert image.save(str(tmp_path / f"effect-slice-{magassag}.png"))


def test_soha_allasban_a_bal_fiok_a_regi_helyen_marad(qml_app, qt_app):
    window, _app_controller, engine = qml_app
    effect_controller = engine.rootContext().contextProperty("effectSliceController")
    effect_controller.setMode("never")
    window.resize(1280, 940)
    window.show()
    window.setProperty("viewerOpen", True)
    window.setProperty("selectedIndex", 0)
    viewer = window.findChild(QObject, "photoViewer")
    assert QMetaObject.invokeMethod(
        viewer, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    box = window.findChild(QObject, "viewerEffectSliceBox")
    histogram = window.findChild(QObject, "viewerHistogramBox")
    editor_panel = window.findChild(QObject, "viewerEditorPanel")
    assert var_feltetelre(qt_app, lambda: histogram.isVisible(), 5.0)

    assert not box.isVisible()
    # a #6477 szerinti eredeti foglalás: csak a hisztogram és az alsó margója
    drawer = window.findChild(QObject, "viewerLeftDrawer")
    drawer_bottom = drawer.mapToScene(QPointF(0, drawer.property("height"))).y()
    histogram_top = histogram.mapToScene(QPointF(0, 0)).y()
    assert editor_panel.property("bottomReserve") == pytest.approx(
        drawer_bottom - histogram_top, abs=0.5
    )

    # szerkesztés közben állásban effektpanel nélkül sem látszik
    effect_controller.setMode("editing")
    qt_app.processEvents()
    assert not box.isVisible()
    effect_controller.setMode("always")
    assert var_feltetelre(qt_app, lambda: box.isVisible(), 3.0)
