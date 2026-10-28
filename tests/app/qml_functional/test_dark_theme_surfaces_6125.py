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


def test_dark_theme_colors_live_unnamed_face_surfaces(qml_app, qt_app):
    window, controller, engine = qml_app
    theme = engine.singletonInstance("PicasaPy", "Theme")
    assert theme is not None
    controller.setDarkTheme(True)
    view = _unnamed_faces_view(engine, window)

    # A névtelen album fejlécében lévő közös névmező.
    bulk_name = view.findChild(QObject, "unnamedNameField")
    assert bulk_name is not None
    assert _background_color(bulk_name) == theme.property("controlBase")
    assert bulk_name.property("background").property("border").property(
        "color"
    ) == theme.property("inputBorder")

    # A csoportosított rács névmezője és a javaslat-popup kártyája.
    face = {"faceId": 81, "thumbUrl": "", "suggestedName": ""}
    view.setProperty("grouped", True)
    view.setProperty("facesModel", [face])
    view.setProperty("groupsModel", [{"label": "", "faces": [face]}])
    qt_app.processEvents()
    grid_name = view.findChild(QObject, "unnamedFaceNameField_81")
    suggestion_panel = view.findChild(QObject, "unnamedNameSuggestions_81")
    assert grid_name is not None
    assert suggestion_panel is not None
    assert _background_color(grid_name) == theme.property("controlBase")
    assert grid_name.property("background").property("border").property(
        "color"
    ) == theme.property("inputBorder")
    assert suggestion_panel.property("color") == theme.property("controlBase")

    # A Mellőzött emberek albumának szerkeszthető névmezője.
    view.setProperty("mode", "ignored")
    view.setProperty("groupsModel", [{"label": "", "faces": [face]}])
    qt_app.processEvents()
    ignored_name = view.findChild(QObject, "ignoredFaceNameField_81")
    assert ignored_name is not None
    assert _background_color(ignored_name) == theme.property("controlBase")
    assert ignored_name.property("background").property("border").property(
        "color"
    ) == theme.property("inputBorder")

    # A súgóablak is témaszínt kap, bár a tesztben nem kell megnyitni.
    welcome = view.findChild(QObject, "unnamedWelcomeDialog")
    assert welcome is not None
    assert welcome.property("background").property("color") == theme.property(
        "unnamedWelcomeBg"
    )
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

