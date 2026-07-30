"""#333: nyelvválasztó az Eszközök menüben.

A menüpont a vezérlő `language` beállítását tükrözi és állítja — a felület
nyelve ezen keresztül vált, nem a rendszer nyelvétől függ.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt


@pytest.fixture
def menu_items(qml_app):
    window, controller, _engine = qml_app
    english = window.findChild(QObject, "menuLanguageEnglish")
    hungarian = window.findChild(QObject, "menuLanguageHungarian")
    assert english is not None and hungarian is not None
    return window, controller, english, hungarian


class TestLanguageMenu:
    def test_submenu_exists(self, qml_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "menuToolsLanguage") is not None

    def test_english_is_checked_by_default(self, menu_items):
        _window, controller, english, hungarian = menu_items
        assert controller.language == "en"
        assert english.property("checked") is True
        assert hungarian.property("checked") is False

    def test_choosing_hungarian_updates_the_controller(self, menu_items):
        _window, controller, _english, hungarian = menu_items
        QMetaObject.invokeMethod(
            hungarian, "click", Qt.ConnectionType.DirectConnection
        )
        assert controller.language == "hu"

    def test_check_marks_follow_the_setting(self, menu_items):
        _window, controller, english, hungarian = menu_items
        controller.setLanguage("hu")
        assert hungarian.property("checked") is True
        assert english.property("checked") is False
        controller.setLanguage("en")
        assert english.property("checked") is True
        assert hungarian.property("checked") is False
