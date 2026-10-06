"""#4333: a Fotónéző beállításai valódi kattintással nyitnak és mentenek."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, QSettings, Qt
from PySide6.QtTest import QTest

from picasapy.app.color_management_controller import coerce_color_management_flag
from support.qt_wait import varj_feltetelre


def _gyerek(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _lathato_elem(window, feltetel):
    sor = [window.contentItem().parentItem() or window.contentItem()]
    while sor:
        elem = sor.pop()
        if elem.isVisible() and feltetel(elem):
            return elem
        sor.extend(elem.childItems())
    return None


def _kattintas(window, qt_app, elem):
    assert varj_feltetelre(
        qt_app, lambda: elem.width() > 0 and elem.height() > 0, 3.0
    ), f"{elem.objectName()}: nem kattintható"
    szulo = elem
    while szulo is not None:
        szulo.ensurePolished()
        szulo = szulo.parentItem()
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )
    qt_app.processEvents()


def _dupla_kattintas(window, qt_app, elem):
    assert varj_feltetelre(
        qt_app, lambda: elem.width() > 0 and elem.height() > 0, 3.0
    ), f"{elem.objectName()}: nem kattintható"
    szulo = elem
    while szulo is not None:
        szulo.ensurePolished()
        szulo = szulo.parentItem()
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseDClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )
    qt_app.processEvents()


def _fotonezo_beallitasok_nyitasa(window, qt_app):
    eszkozok = _lathato_elem(
        window,
        lambda elem: "MenuBarItem" in elem.metaObject().className()
        and elem.property("text") == "&Tools",
    )
    assert eszkozok is not None, "az Eszközök menü nem látható"
    _kattintas(window, qt_app, eszkozok)

    foto_nezo_tetel = None

    def _megjelent():
        nonlocal foto_nezo_tetel
        foto_nezo_tetel = _lathato_elem(
            window,
            lambda elem: "MenuItem" in elem.metaObject().className()
            and elem.property("text") == "Configure Photo Viewer...",
        )
        return foto_nezo_tetel is not None

    assert varj_feltetelre(qt_app, _megjelent, 3.0), (
        "a Fotónéző beállítása menütétel nem jelent meg"
    )
    _kattintas(window, qt_app, foto_nezo_tetel)


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_tools_menu_opens_and_saves_photo_viewer_settings(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    _fotonezo_beallitasok_nyitasa(window, qt_app)

    dialog = _gyerek(window, "photoViewerSettingsDialog")
    assert varj_feltetelre(qt_app, lambda: dialog.property("opened"), 3.0), (
        "a Fotónéző beállításai nem nyíltak meg"
    )
    color_management = _gyerek(window, "photoViewerColorManagementCheck")
    assert color_management.property("checked") is False

    _kattintas(color_management.window(), qt_app, color_management)

    assert varj_feltetelre(
        qt_app, lambda: controller.colorManagement is True, 3.0
    ), "a valódi kattintás nem kapcsolta be a színkezelést"
    controller._get_settings().sync()
    from PySide6.QtCore import QSettings

    saved = QSettings(
        controller._get_settings().fileName(), QSettings.Format.IniFormat
    )
    assert coerce_color_management_flag(saved.value("view/colorManagement"))


def test_photo_viewer_settings_component_loads_without_controller(qt_app):
    from pathlib import Path

    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    qml_root = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml"
    dialog_url = qml_root / "PicasaPy/PhotoViewerSettingsDialog.qml"
    engine = QQmlEngine()
    engine.addImportPath(str(qml_root))
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(dialog_url)))
    assert component.isReady(), [error.toString() for error in component.errors()]

    dialog = component.create()
    assert dialog is not None, [error.toString() for error in component.errors()]
    assert dialog.property("viewerController") is None
    assert dialog.property("visible") is False
    dialog.deleteLater()
    engine.deleteLater()
    qt_app.processEvents()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_fullscreen_startup_checkbox_saves_and_leaves_the_library_viewer_windowed(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    assert controller.viewerFullscreenStartup is True
    _fotonezo_beallitasok_nyitasa(window, qt_app)
    dialog = _gyerek(window, "photoViewerSettingsDialog")
    assert varj_feltetelre(qt_app, lambda: dialog.property("opened"), 3.0)

    fullscreen = _gyerek(window, "photoViewerFullscreenStartupCheck")
    assert fullscreen.property("text") == (
        "Fullscreen startup (requires restart of Photo Viewer to take effect)"
    )
    assert fullscreen.property("checked") is True

    _kattintas(fullscreen.window(), qt_app, fullscreen)
    assert varj_feltetelre(
        qt_app, lambda: controller.viewerFullscreenStartup is False, 3.0
    )
    controller._get_settings().sync()
    saved = QSettings(
        controller._get_settings().fileName(), QSettings.Format.IniFormat
    )
    assert int(saved.value("ViewerFullscreenStartup")) == 0
    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert varj_feltetelre(qt_app, lambda: not dialog.property("opened"), 3.0)

    mouse_area = _lathato_elem(
        window, lambda elem: elem.objectName() == "thumbMouseArea"
    )
    assert mouse_area is not None, "a rács első képe nem látható"
    _dupla_kattintas(window, qt_app, mouse_area)
    assert varj_feltetelre(qt_app, lambda: window.property("viewerOpen"), 3.0)
    assert varj_feltetelre(
        qt_app,
        lambda: window.visibility() == window.Visibility.Windowed,
        3.0,
    )

    vissza = _gyerek(window, "viewerBackButton")
    _kattintas(window, qt_app, vissza)
    assert varj_feltetelre(qt_app, lambda: not window.property("viewerOpen"), 3.0)

    _fotonezo_beallitasok_nyitasa(window, qt_app)
    assert varj_feltetelre(qt_app, lambda: dialog.property("opened"), 3.0)
    fullscreen = _gyerek(window, "photoViewerFullscreenStartupCheck")
    assert fullscreen.property("checked") is False
    _kattintas(fullscreen.window(), qt_app, fullscreen)
    assert varj_feltetelre(
        qt_app, lambda: controller.viewerFullscreenStartup is True, 3.0
    )
    controller._get_settings().sync()
    saved.sync()
    assert int(saved.value("ViewerFullscreenStartup")) == 1
    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert varj_feltetelre(qt_app, lambda: not dialog.property("opened"), 3.0)

    mouse_area = _lathato_elem(
        window, lambda elem: elem.objectName() == "thumbMouseArea"
    )
    assert mouse_area is not None, "a rács első képe nem látható"
    _dupla_kattintas(window, qt_app, mouse_area)
    assert varj_feltetelre(qt_app, lambda: window.property("viewerOpen"), 3.0)
    assert varj_feltetelre(
        qt_app,
        # #4432: a beállítás az eredeti ÖNÁLLÓ Fotónézőé (PicasaPhotoViewer.exe);
        # a könyvtár beépített nézője bekapcsolt állapotban sem vált teljes
        # képernyőre — ez működő viselkedés, nem írhatja felül.
        lambda: window.visibility() == window.Visibility.Windowed,
        3.0,
    )
