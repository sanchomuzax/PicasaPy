"""#367: `confirm_settings.py` — a „Ne kérdezze újra" jelölő perzisztens
tára (a `window_geometry.py` tesztjeinek mintájára)."""

import pytest

from picasapy.app.confirm_settings import (
    confirm_setting_key,
    is_confirm_suppressed,
    set_confirm_suppressed,
)


@pytest.fixture
def settings(tmp_path):
    from PySide6.QtCore import QSettings

    return QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)


class TestConfirmSettingKey:
    def test_key_is_namespaced_per_decision(self):
        assert confirm_setting_key("delete") == "confirm/delete/remember"
        assert confirm_setting_key("move") == "confirm/move/remember"


class TestIsConfirmSuppressed:
    def test_fresh_settings_not_suppressed(self, qt_app, settings):
        assert is_confirm_suppressed(settings, "delete") is False

    def test_suppressed_after_remember(self, qt_app, settings):
        set_confirm_suppressed(settings, "delete", True)
        assert is_confirm_suppressed(settings, "delete") is True

    def test_keys_are_independent(self, qt_app, settings):
        set_confirm_suppressed(settings, "delete", True)
        assert is_confirm_suppressed(settings, "move") is False

    def test_unremember_restores_dialog(self, qt_app, settings):
        set_confirm_suppressed(settings, "delete", True)
        set_confirm_suppressed(settings, "delete", False)
        assert is_confirm_suppressed(settings, "delete") is False

    def test_corrupt_value_treated_as_not_suppressed(self, qt_app, settings):
        settings.setValue(confirm_setting_key("delete"), "nem-igaz-hamis")
        assert is_confirm_suppressed(settings, "delete") is False
