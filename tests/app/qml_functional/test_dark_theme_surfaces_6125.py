"""#6125 — a nem fényképre rajzolt felületek a sötét témát követik."""

from pathlib import Path

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


def _background_color(control):
    background = control.property("background")
    assert background is not None
    return background.property("color")


def test_dark_theme_colors_live_unnamed_face_surfaces(qml_app):
    window, controller, engine = qml_app
    theme = engine.singletonInstance("PicasaPy", "Theme")
    assert theme is not None
    controller.setDarkTheme(True)
    view = _unnamed_faces_view(engine, window)

    # A névtelen album fejlécében lévő közös névmező.
    bulk_name = view.findChild(QObject, "unnamedNameField")
    assert bulk_name is not None
    assert _background_color(bulk_name) == theme.property("controlBase")

    controller.setDarkTheme(False)


def test_hovered_tag_row_uses_dark_surface_color():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/picasapy/app/qml/PicasaPy/TagsPanel.qml").read_text(
        encoding="utf-8"
    )
    assert 'color: rowHover.hovered ? Theme.contentPanel : "transparent"' in source


def test_unnamed_face_components_use_theme_surfaces():
    root = Path(__file__).resolve().parents[3]
    qml = root / "src/picasapy/app/qml/PicasaPy"
    for name in (
        "UnnamedFacesView.qml",
        "UnnamedFacesViewGrid.qml",
        "UnnamedFacesViewIgnoredGroups.qml",
    ):
        source = (qml / name).read_text(encoding="utf-8")
        assert 'color: Theme.controlBase' in source, name
        assert 'border.color: Theme.inputBorder' in source, name
