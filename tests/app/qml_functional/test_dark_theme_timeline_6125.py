"""#6125 — az Időrend vezérlői követik az alkalmazás sötét témáját."""

from PySide6.QtCore import QObject


def test_timeline_controls_use_dark_theme_tokens(qml_app):
    window, controller, engine = qml_app
    timeline = window.findChild(QObject, "timelineView")
    assert timeline is not None
    date_label = timeline.findChild(QObject, "timelineFirstDate")
    close_button = timeline.findChild(QObject, "timelineCloseButton")
    assert date_label is not None
    assert close_button is not None
    button_background = close_button.property("background")
    assert button_background is not None
    theme = engine.singletonInstance("PicasaPy", "Theme")
    assert theme is not None

    controller.setDarkTheme(True)

    assert date_label.property("color") == theme.property("ink")
    assert button_background.property("color") == theme.property("buttonBg")
