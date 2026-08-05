"""#367: `ConfirmSettingsBridge` — a QML-nek adott isSuppressed/setSuppressed
Slot-ok az injektált (teszt-) QSettings fölött."""

import pytest


@pytest.fixture
def settings(tmp_path):
    from PySide6.QtCore import QSettings

    return QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)


@pytest.fixture
def bridge(qt_app, settings):
    from picasapy.app.confirm_settings_bridge import ConfirmSettingsBridge

    return ConfirmSettingsBridge(settings=settings)


class TestConfirmSettingsBridge:
    def test_not_suppressed_by_default(self, bridge):
        assert bridge.isSuppressed("delete") is False

    def test_set_suppressed_then_read_back(self, bridge):
        bridge.setSuppressed("delete", True)
        assert bridge.isSuppressed("delete") is True

    def test_set_suppressed_false_unsets(self, bridge):
        bridge.setSuppressed("delete", True)
        bridge.setSuppressed("delete", False)
        assert bridge.isSuppressed("delete") is False

    def test_default_settings_used_when_none_injected(self, qt_app, monkeypatch, tmp_path):
        # ha nincs injektált settings, a bridge saját QSettings-et hoz
        # létre lustán — ezt egy ideiglenes IniFormat-tal helyettesítjük,
        # hogy ne a rendszer valós PicasaPy-beállításait szennyezze
        from PySide6.QtCore import QSettings

        from picasapy.app.confirm_settings_bridge import ConfirmSettingsBridge

        own_settings = QSettings(str(tmp_path / "own.ini"), QSettings.Format.IniFormat)
        bridge = ConfirmSettingsBridge()
        bridge._settings = own_settings  # ugyanaz a lusta mező, mint AppControllerben
        bridge.setSuppressed("delete", True)
        assert own_settings.value("confirm/delete/remember") in (True, "true")
