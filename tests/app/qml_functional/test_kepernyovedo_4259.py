"""Képernyővédő: beállítás, forrásválasztás és kilépés valódi bemenetre (#4259)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional import _fomenu_4420_akciok as fomenu_akciok


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _trigger(root, name):
    QMetaObject.invokeMethod(
        _child(root, name), "triggered", Qt.ConnectionType.DirectConnection
    )


def _click_item(window, item, qt_app):
    """A QML-elem tényleges helyére kattint, a geometriájából számítva."""
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        center.toPoint(),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_bejaro_valodi_megse_gombbal_bezarja_a_kepernyovedo_parbeszedet(
    qml_app, qt_app, height_delta
):
    window, _controller, _engine = qml_app
    celmagassag = window.height() + height_delta
    window.resize(window.width(), celmagassag)
    assert varj_feltetelre(qt_app, lambda: window.height() == celmagassag, 3.0)

    _trigger(window, "menuToolsScreensaver")
    assert varj_feltetelre(
        qt_app,
        lambda: _child(window, "screensaverDialog").property("visible") is True,
        3.0,
    )
    dialog = _child(window, "screensaverDialog")
    megse_gombok = [
        elem
        for elem in fomenu_akciok._parbeszed_gombok(dialog)
        if "Button" in elem.metaObject().className()
        and (
            "cancel" in (elem.objectName() or "").casefold()
            or str(elem.property("text") or "").strip().casefold()
            in {"cancel", "mégse"}
        )
    ]
    assert megse_gombok, "a ScreensaverDialog látható Mégse gombja hiányzik"

    # A valódi termékgomb működését külön választjuk el a bejáró takarításától.
    _click_item(window, megse_gombok[0], qt_app)
    assert varj_feltetelre(
        qt_app,
        lambda: not fomenu_akciok._lathato_dialogusok(window),
        3.0,
    ), "a ScreensaverDialog valódi Mégse gombja nem zárta be a párbeszédet"

    _trigger(window, "menuToolsScreensaver")
    assert varj_feltetelre(
        qt_app,
        lambda: _child(window, "screensaverDialog").property("visible") is True,
        3.0,
    )
    dialog = _child(window, "screensaverDialog")
    megse_gombok = [
        elem
        for elem in fomenu_akciok._parbeszed_gombok(dialog)
        if "Button" in elem.metaObject().className()
        and (
            "cancel" in (elem.objectName() or "").casefold()
            or str(elem.property("text") or "").strip().casefold()
            in {"cancel", "mégse"}
        )
    ]
    assert megse_gombok, "a visszanyitott ScreensaverDialog Mégse gombja hiányzik"

    naplo = []
    fomenu_akciok._zarj_parbeszedeket(window, qt_app, naplo)
    bejaro_bezarta = not fomenu_akciok._lathato_dialogusok(window)
    if not bejaro_bezarta:
        # Bizonyítja, hogy a termék Cancel gombja zár; a piros állítás így
        # kizárólag a bejáró zárási útját nevezi meg.
        _click_item(window, megse_gombok[0], qt_app)
        assert varj_feltetelre(
            qt_app,
            lambda: not fomenu_akciok._lathato_dialogusok(window),
            3.0,
        ), "a valódi Mégse kattintás sem zárta be a párbeszédet"

    assert bejaro_bezarta, (
        "a bejáró nem zárta be a párbeszédet; a valódi Mégse gomb kattintása "
        f"bezárta: {not fomenu_akciok._lathato_dialogusok(window)}; napló: {naplo}"
    )


def _start_preview(window, qt_app):
    _trigger(window, "menuToolsScreensaver")
    qt_app.processEvents()
    dialog = _child(window, "screensaverDialog")
    assert dialog.property("visible") is True
    _click_item(window, _child(window, "screensaverPreviewButton"), qt_app)
    return dialog


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_tools_menu_opens_screensaver_settings(qml_app, qt_app, height_delta):
    window, _controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    _trigger(window, "menuToolsScreensaver")
    qt_app.processEvents()

    dialog = _child(window, "screensaverDialog")
    assert dialog.property("visible") is True
    assert _child(window, "screensaverSourceList") is not None
    assert _child(window, "screensaverEffectBox") is not None
    assert _child(window, "screensaverSecondsSlider") is not None
    assert _child(window, "screensaverCaptionCheck") is not None


def test_screensaver_dialog_builds_without_main_window_controller(qt_app):
    qml_root = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml"
    dialog_url = qml_root / "PicasaPy/ScreensaverDialog.qml"
    engine = QQmlEngine()
    engine.addImportPath(str(qml_root))
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(dialog_url)))
    assert component.isReady(), [error.toString() for error in component.errors()]

    dialog = component.create()
    assert dialog is not None, [error.toString() for error in component.errors()]
    assert dialog.property("saverController") is None
    assert dialog.property("visible") is False
    dialog.deleteLater()
    engine.deleteLater()
    qt_app.processEvents()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_create_menu_adds_selected_pictures_to_screensaver(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()
    assert controller.photos.rowCount() > 0
    window.setProperty("selectedIndex", 0)
    window.setProperty("selectedIndexes", [0])

    _trigger(window, "menuCreateAddScreensaver")
    qt_app.processEvents()

    selected_source = next(
        source for source in controller.screensaverSources
        if source["key"] == "photos:selected"
    )
    assert selected_source["selected"] is True
    controller.setScreensaverSources(["photos:selected"])
    assert controller.prepareScreensaverPreview() == selected_source["count"]


def test_adding_an_existing_picture_reports_no_new_addition(qml_app):
    _window, controller, _engine = qml_app
    path = controller.photos.filePathAt(0)

    assert controller.addScreensaverPhotos([path]) == 1
    assert controller.addScreensaverPhotos([path]) == 0


def test_screensaver_settings_are_saved_in_qsettings(qml_app):
    _window, controller, _engine = qml_app
    lib = Path(controller._roots[0])
    source_key = f"folder:{lib}"

    controller.setScreensaverSources([source_key])
    controller.setScreensaverEffect("kenburns")
    controller.setScreensaverSeconds(7)
    controller.setScreensaverShowCaptions(False)
    controller._settings.sync()

    from PySide6.QtCore import QSettings

    saved = QSettings(
        controller._settings.fileName(), QSettings.Format.IniFormat
    )
    assert saved.value("screensaver/sources") == [source_key]
    assert saved.value("screensaver/effect") == "kenburns"
    assert int(saved.value("screensaver/seconds")) == 7
    assert saved.value("screensaver/showCaptions") is False


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_preview_projects_selected_folder_and_real_click_exits(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()
    lib = Path(controller._roots[0])
    controller.setScreensaverSources([f"folder:{lib}"])

    _start_preview(window, qt_app)

    slideshow = _child(window, "slideshowView")
    assert slideshow.property("visible") is True
    assert slideshow.property("screensaverMode") is True
    assert slideshow.property("photosModel") == controller.screensaverPhotos
    assert controller.screensaverPhotos.rowCount() == 2
    assert varj_feltetelre(
        qt_app, lambda: slideshow.property("screensaverInputArmed"), 3.0
    ), "a vetítésnek rövid indulási védelem után fogadnia kell az egeret"

    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPointF(window.width() / 2, window.height() / 2).toPoint(),
    )
    qt_app.processEvents()
    assert slideshow.property("visible") is False


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_any_key_exits_screensaver_preview(qml_app, qt_app, height_delta):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()
    lib = Path(controller._roots[0])
    controller.setScreensaverSources([f"folder:{lib}"])
    _start_preview(window, qt_app)

    slideshow = _child(window, "slideshowView")
    assert slideshow.property("visible") is True
    assert varj_feltetelre(
        qt_app, lambda: slideshow.property("screensaverInputArmed"), 3.0
    ), "a vetítésnek rövid indulási védelem után fogadnia kell a billentyűt"
    QTest.keyClick(window, Qt.Key.Key_X)
    qt_app.processEvents()
    assert slideshow.property("visible") is False


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_application_shortcut_also_exits_screensaver(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()
    controller.setScreensaverSources([f"folder:{Path(controller._roots[0])}"])
    _start_preview(window, qt_app)
    slideshow = _child(window, "slideshowView")
    assert varj_feltetelre(
        qt_app, lambda: slideshow.property("screensaverInputArmed"), 3.0
    )

    QTest.keyClick(
        window,
        Qt.Key.Key_A,
        Qt.KeyboardModifier.ControlModifier,
    )
    qt_app.processEvents()
    assert slideshow.property("visible") is False


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_mouse_movement_exits_screensaver_preview(qml_app, qt_app, height_delta):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()
    lib = Path(controller._roots[0])
    controller.setScreensaverSources([f"folder:{lib}"])
    _start_preview(window, qt_app)

    slideshow = _child(window, "slideshowView")
    assert varj_feltetelre(
        qt_app, lambda: slideshow.property("screensaverInputArmed"), 3.0
    ), "a vetítésnek rövid indulási védelem után fogadnia kell az egeret"
    QTest.mouseMove(
        window, QPointF(window.width() - 6, window.height() - 6).toPoint()
    )
    qt_app.processEvents()
    assert slideshow.property("visible") is False
