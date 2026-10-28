"""#6125 — az aktív eszköztár-nézetváltó sötét témában is témaszínű."""

from pathlib import Path

from PySide6.QtCore import QObject


def test_active_folder_view_button_uses_dark_surface_color(qml_app):
    window, controller, engine = qml_app
    button = window.findChild(QObject, "toolbarFlatViewButton")
    theme = engine.singletonInstance("PicasaPy", "Theme")
    assert button is not None
    assert theme is not None

    controller.setDarkTheme(True)

    assert button.property("color") == theme.property("contentPanel")


def test_hovered_tag_row_uses_dark_surface_color():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/picasapy/app/qml/PicasaPy/TagsPanel.qml").read_text(
        encoding="utf-8"
    )
    assert 'color: rowHover.hovered ? Theme.contentPanel : "transparent"' in source


def test_unnamed_face_inputs_use_theme_surfaces():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/picasapy/app/qml/PicasaPy/UnnamedFacesView.qml").read_text(
        encoding="utf-8"
    )
    assert source.count("color: Theme.controlBase") == 3
    assert "color: Theme.contentPanel" in source
    assert source.count("border.color: Theme.chromeBorder") >= 4
