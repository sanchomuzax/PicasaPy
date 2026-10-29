"""#6125 — főablak- és névtelenarc-felületek élő sötétmód-próbája."""

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

import picasapy.app.application as app_module

_KEEP_ALIVE: list = []


def _unnamed_faces_view(engine, window):
    component = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "UnnamedFacesView.qml")
        ),
    )
    _KEEP_ALIVE.append(component)
    view = component.create()
    assert component.errors() == [], component.errors()
    assert view is not None
    view.setParentItem(window.contentItem())
    view.setProperty("width", 700)
    view.setProperty("height", 620)
    _KEEP_ALIVE.append(view)
    return view


def test_dark_theme_main_and_name_field_colors_are_live(qml_app):
    window, controller, engine = qml_app
    theme = engine.singletonInstance("PicasaPy", "Theme")
    assert theme is not None
    controller.setDarkTheme(True)
    assert theme.property("dark") is True

    flat_view_button = window.findChild(QObject, "toolbarFlatViewButton")
    search_clear = window.findChild(QObject, "searchClear")
    scan_bar = window.findChild(QObject, "dupeSearchScanningBar")
    tray_label = window.findChild(QObject, "trayScratchLabel")
    assert flat_view_button is not None
    assert search_clear is not None
    assert scan_bar is not None
    assert tray_label is not None
    assert flat_view_button.property("color") == theme.property("contentPanel")
    assert search_clear.property("color") == theme.property("searchClearBg")
    assert scan_bar.property("color") == theme.property("filterNoticeBg")
    assert tray_label.property("color") == theme.property("trayScratchLabel")

    view = _unnamed_faces_view(engine, window)
    bulk_name = view.findChild(QObject, "unnamedNameField")
    assert bulk_name is not None
    background = bulk_name.property("background")
    assert background is not None
    assert background.property("color") == theme.property("controlBase")
    controller.setDarkTheme(False)
