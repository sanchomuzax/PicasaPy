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
        lambda: effect_controller.surface_snapshot().get("kind") == "identity",
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

    # #6535 (tulajdonos): szerkesztés közben a szerkesztőpanel minden fülén
    # látszik, effektpanel nélkül is (a Gyakori javítások is effektek)
    effect_controller.setMode("editing")
    assert var_feltetelre(qt_app, lambda: box.isVisible(), 3.0)
    effect_controller.setMode("always")
    assert var_feltetelre(qt_app, lambda: box.isVisible(), 3.0)


@pytest.mark.parametrize("magassag", (800, 940))
def test_a_doboz_sosem_takarja_az_effektpanel_alkalmaz_gombjat(qml_app, qt_app, magassag):
    from tests.app.qml_functional.test_alapertek_felirat_4559 import (
        _child,
        _nyisd_meg_az_effektet,
    )

    window, _app_controller, engine = qml_app
    engine.rootContext().contextProperty("effectSliceController").setMode("editing")
    window.resize(1280, magassag)
    window.show()
    assert var_feltetelre(qt_app, lambda: abs(window.height() - magassag) < 1, 5.0)
    panel = window.findChild(QObject, "viewerEditorPanel")
    _nyisd_meg_az_effektet(window, panel, qt_app, "effectDirTint", "dir_tint")
    for _ in range(20):
        qt_app.processEvents()
    gomb = _child(panel, "effectParamApplyButton")
    box = window.findChild(QObject, "viewerEffectSliceBox")
    gomb_alja = gomb.mapToScene(QPointF(0, gomb.property("height"))).y()
    box_teteje = box.mapToScene(QPointF(0, 0)).y()

    assert (not box.isVisible()) or box_teteje >= gomb_alja
    if magassag == 940:
        # elég magas ablakban a doboz szerkesztés közben meg is jelenik
        assert box.isVisible()


def test_a_finomhangolas_ful_csuszkaja_is_a_melysegtengelyre_kerul(qml_app, qt_app):
    window, _app_controller, engine = qml_app
    effect_controller = engine.rootContext().contextProperty("effectSliceController")
    effect_controller.setMode("editing")
    window.resize(1280, 940)
    window.show()
    window.setProperty("viewerOpen", True)
    window.setProperty("selectedIndex", 0)
    viewer = window.findChild(QObject, "photoViewer")
    assert QMetaObject.invokeMethod(
        viewer, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    panel = window.findChild(QObject, "viewerEditorPanel")
    box = window.findChild(QObject, "viewerEffectSliceBox")
    assert QMetaObject.invokeMethod(
        panel, "selectTab", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 1)
    )
    assert var_feltetelre(qt_app, lambda: box.isVisible(), 3.0)
    window.findChild(QObject, "finetuneTempSlider").setProperty("value", 0.5)
    panel.setProperty("effectSliceDepthIndex", 3)

    assert var_feltetelre(
        qt_app, lambda: effect_controller.property("sliderLabel") == "Color Temperature", 3.0
    )
    assert effect_controller.property("sliderValue") == pytest.approx(0.5)


@pytest.mark.parametrize("ful", (0, 2, 3, 4, 5))
def test_szerkesztes_kozben_minden_effektfulon_latszik(qml_app, qt_app, ful):
    """#6535: a tulajdonos szerint a Gyakori javítások és a rácsos fülök is effektek."""
    window, _app_controller, engine = qml_app
    effect_controller = engine.rootContext().contextProperty("effectSliceController")
    effect_controller.setMode("editing")
    window.resize(1280, 940)
    window.show()
    window.setProperty("viewerOpen", True)
    window.setProperty("selectedIndex", 0)
    viewer = window.findChild(QObject, "photoViewer")
    assert QMetaObject.invokeMethod(
        viewer, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    panel = window.findChild(QObject, "viewerEditorPanel")
    box = window.findChild(QObject, "viewerEffectSliceBox")
    assert QMetaObject.invokeMethod(
        panel, "selectTab", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", ful)
    )
    assert var_feltetelre(qt_app, lambda: box.isVisible(), 3.0), (
        f"a {ful + 1}. effektfülön szerkesztés közben nincs térszelvény"
    )


def _kattints_kozepre(window, item) -> None:
    from PySide6.QtCore import QPoint
    from PySide6.QtTest import QTest

    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(round(pont.x()), round(pont.y())))


def _kiadaskep(window, box, nev: str) -> None:
    """A kiadásképhez a bal fiók alja (a doboz) mentése, csak kérésre."""
    import os

    mappa = os.environ.get("PICASAPY_KIADASKEP_MAPPA")
    if not mappa:
        return
    bal_felso = box.mapToScene(QPointF(-20, -380))
    kep = window.grabWindow()
    kep.copy(
        max(0, int(bal_felso.x())), max(0, int(bal_felso.y())), 280, 380 + int(box.height()) + 10
    ).save(os.path.join(mappa, nev))


def test_jo_napom_van_utan_a_finomhangolas_tonusfeluletet_mutat(qml_app, qt_app):
    """#6536, a tulajdonos lépéssora: Jó napom van, majd a Finomhangolás fül."""
    window, _app_controller, engine = qml_app
    effect_controller = engine.rootContext().contextProperty("effectSliceController")
    effect_controller.setMode("editing")
    window.resize(1280, 940)
    window.show()
    window.setProperty("viewerOpen", True)
    window.setProperty("selectedIndex", 0)
    viewer = window.findChild(QObject, "photoViewer")
    assert QMetaObject.invokeMethod(
        viewer, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    panel = window.findChild(QObject, "viewerEditorPanel")
    box = window.findChild(QObject, "viewerEffectSliceBox")
    assert QMetaObject.invokeMethod(
        panel, "selectTab", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    lucky = window.findChild(QObject, "editToolEnhance")
    assert var_feltetelre(qt_app, lambda: lucky.isVisible(), 3.0)
    _kattints_kozepre(window, lucky)
    assert var_feltetelre(qt_app, lambda: box.isVisible(), 3.0), (
        "a Gyakori javítások fülön nincs térszelvény"
    )
    assert var_feltetelre(
        qt_app, lambda: effect_controller.surface_snapshot().get("kind") == "tone", 5.0
    ), "a Gyakori javítások fülön a lánc (Jó napom van) felülete nem rajzolódott ki"
    assert effect_controller.property("chainLength") >= 1
    qt_app.processEvents()
    _kiadaskep(window, box, "6535-gyakori-javitasok.png")

    assert QMetaObject.invokeMethod(
        panel, "selectTab", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 1)
    )
    assert var_feltetelre(
        qt_app, lambda: effect_controller.property("selectedViewType") == "tone", 3.0
    ), "a Finomhangolás fülön nem a tónusfelület látszik"
    assert var_feltetelre(
        qt_app, lambda: effect_controller.surface_snapshot().get("kind") == "tone", 5.0
    ), "a térszelvény nem tónusfelületet rajzolt"
    sorok = effect_controller.surface_snapshot().get("rows") or []
    ertekek = [v for sor in sorok for v in (sor if isinstance(sor, list) else [])]
    assert ertekek and max(ertekek) - min(ertekek) > 0.1, "a felület lapos lap"
    _kiadaskep(window, box, "6536-finomhangolas.png")
