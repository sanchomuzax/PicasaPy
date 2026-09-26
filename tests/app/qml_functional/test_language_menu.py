"""#333/#3555: nyelvválasztó az Eszközök menüben.

A menüpontok a vezérlő `pendingLanguage`-ét (a KÖVETKEZŐ indításra kért
választást) tükrözik — a futó felület nyelve ezen keresztül nem vált
azonnal: a kattintás megerősítő kérdést nyit (Main.qml `menuLanguageConfirm*`
ConfirmDialog-ja), és csak az „Igen" hívja a `setLanguage`-et."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt


@pytest.fixture
def menu_items(qml_app):
    window, controller, _engine = qml_app
    system = window.findChild(QObject, "menuLanguageSystem")
    english = window.findChild(QObject, "menuLanguageEnglish")
    hungarian = window.findChild(QObject, "menuLanguageHungarian")
    assert system is not None and english is not None and hungarian is not None
    return window, controller, system, english, hungarian


def _trigger(item):
    QMetaObject.invokeMethod(item, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)


def _confirm(window, qt_app, *, yes: bool):
    button_name = "menuLanguageConfirmYesButton" if yes else "menuLanguageConfirmNoButton"
    button = window.findChild(QObject, button_name)
    assert button is not None, "a megerősítő kérdés nem nyílt meg"
    QMetaObject.invokeMethod(button, "clicked", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestLanguageMenu:
    def test_submenu_exists(self, qml_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "menuToolsLanguage") is not None

    def test_english_is_checked_by_default(self, menu_items):
        _window, controller, system, english, hungarian = menu_items
        assert controller.pendingLanguage == "en"
        assert system.property("checked") is False
        assert english.property("checked") is True
        assert hungarian.property("checked") is False

    def test_choosing_hungarian_opens_a_confirmation(self, menu_items, qt_app):
        window, controller, _system, _english, hungarian = menu_items
        _trigger(hungarian)
        qt_app.processEvents()
        assert controller.pendingLanguage == "en", (
            "#3555: a menüpont önmagában nem válthat, csak kérdez"
        )
        confirm = window.findChild(QObject, "menuLanguageConfirmDialog")
        assert confirm is not None and confirm.property("visible") is True

    def test_confirming_updates_the_controller(self, menu_items, qt_app):
        window, controller, _system, _english, hungarian = menu_items
        _trigger(hungarian)
        qt_app.processEvents()
        _confirm(window, qt_app, yes=True)
        assert controller.pendingLanguage == "hu"
        assert controller.language == "en", (
            "#3555: a futó felület nyelve a következő indításig nem vált"
        )

    def test_denying_leaves_the_controller_untouched(self, menu_items, qt_app):
        window, controller, _system, _english, hungarian = menu_items
        _trigger(hungarian)
        qt_app.processEvents()
        _confirm(window, qt_app, yes=False)
        assert controller.pendingLanguage == "en"

    def test_check_marks_follow_the_pending_setting(self, menu_items, qt_app):
        window, controller, system, english, hungarian = menu_items
        _trigger(hungarian)
        qt_app.processEvents()
        _confirm(window, qt_app, yes=True)
        assert hungarian.property("checked") is True
        assert english.property("checked") is False
        assert system.property("checked") is False

        _trigger(english)
        qt_app.processEvents()
        _confirm(window, qt_app, yes=True)
        assert english.property("checked") is True
        assert hungarian.property("checked") is False

    def test_system_entry_label_has_the_locale_suffix(self, menu_items):
        _window, controller, system, _english, _hungarian = menu_items
        assert controller.systemLanguageSuffix in system.property("text")

    def test_choosing_system_opens_a_confirmation_and_applies(self, menu_items, qt_app):
        window, controller, system, _english, _hungarian = menu_items
        _trigger(system)
        qt_app.processEvents()
        _confirm(window, qt_app, yes=True)
        assert controller.pendingLanguage == controller.systemLanguageCode
        assert system.property("checked") is True
