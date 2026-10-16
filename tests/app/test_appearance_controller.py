"""A megjelenés-vezérlő (sötét téma, #28) tesztjei.

A kapcsoló perzisztens (QSettings `view/darkTheme`), az alapértelmezés a
világos téma, és hibás/kézzel átírt beállításból sem lehet sötét — a
Picasa-paritás szerint a világos az igazi alapállapot.
"""

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.appearance_controller import DARK_THEME_KEY, coerce_dark_flag


class TestCoerceDarkFlag:
    @pytest.mark.parametrize("value", [True, "true", "1", "TRUE", " true "])
    def test_truthy_values(self, value):
        assert coerce_dark_flag(value) is True

    @pytest.mark.parametrize("value", [None, False, "false", "0", "", "hupak", 3.5])
    def test_falsy_or_invalid_values(self, value):
        assert coerce_dark_flag(value) is False


class TestAppearanceMixin:
    @pytest.fixture
    def controller(self, qt_app, tmp_path):
        """Az AppController teljes felépítése nélkül a mixint önmagában
        példányosítjuk — a keverék csak a `_get_settings()`-re támaszkodik."""
        from PySide6.QtCore import QObject

        from picasapy.app.appearance_controller import AppearanceMixin

        class _Probe(AppearanceMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings = settings
                self._init_appearance()

            def _get_settings(self):
                return self._settings

        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        return _Probe(settings)

    def test_default_is_light(self, controller):
        assert controller.darkTheme is False

    def test_set_dark_persists(self, controller):
        controller.setDarkTheme(True)
        assert controller.darkTheme is True
        assert coerce_dark_flag(controller._get_settings().value(DARK_THEME_KEY))

    def test_toggle_flips_both_ways(self, controller):
        controller.toggleDarkTheme()
        assert controller.darkTheme is True
        controller.toggleDarkTheme()
        assert controller.darkTheme is False

    def test_signal_only_on_real_change(self, controller):
        seen = []
        controller.darkThemeChanged.connect(lambda: seen.append(controller.darkTheme))
        controller.setDarkTheme(False)  # már világos — nincs jelzés
        assert seen == []
        controller.setDarkTheme(True)
        assert seen == [True]

    def test_restored_from_settings(self, qt_app, tmp_path):
        from PySide6.QtCore import QObject

        from picasapy.app.appearance_controller import AppearanceMixin

        class _Probe(AppearanceMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings = settings
                self._init_appearance()

            def _get_settings(self):
                return self._settings

        path = str(tmp_path / "settings.ini")
        first = QSettings(path, QSettings.Format.IniFormat)
        probe = _Probe(first)
        probe.setDarkTheme(True)
        first.sync()

        second = QSettings(path, QSettings.Format.IniFormat)
        assert _Probe(second).darkTheme is True

    def test_broken_setting_falls_back_to_light(self, qt_app, tmp_path):
        from PySide6.QtCore import QObject

        from picasapy.app.appearance_controller import AppearanceMixin

        class _Probe(AppearanceMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings = settings
                self._init_appearance()

            def _get_settings(self):
                return self._settings

        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(DARK_THEME_KEY, "talán")
        assert _Probe(settings).darkTheme is False

    def test_general_ui_settings_default_to_the_picasa_values(self, controller):
        assert controller.uiTransitionsEnabled is True
        assert controller.showTooltipsEnabled is True
        assert controller.singleClickExitEnabled is False

    def test_general_ui_settings_are_saved_and_restored(
        self, qt_app, controller
    ):
        from PySide6.QtCore import QSettings

        controller.setUITransitionsEnabled(False)
        controller.setShowTooltipsEnabled(False)
        settings_path = controller._get_settings().fileName()
        controller._get_settings().sync()

        restored = type(controller)(
            QSettings(settings_path, QSettings.Format.IniFormat)
        )
        assert restored.uiTransitionsEnabled is False
        assert restored.showTooltipsEnabled is False

    def test_single_click_exit_is_saved_and_restored(self, qt_app, controller):
        from PySide6.QtCore import QSettings

        controller.setSingleClickExitEnabled(True)
        settings_path = controller._get_settings().fileName()
        controller._get_settings().sync()

        restored = type(controller)(QSettings(settings_path, QSettings.Format.IniFormat))
        assert restored.singleClickExitEnabled is True

    def test_single_click_exit_emits_only_when_changed(self, controller):
        seen = []
        controller.singleClickExitEnabledChanged.connect(
            lambda: seen.append(controller.singleClickExitEnabled)
        )

        controller.setSingleClickExitEnabled(False)
        assert seen == []
        controller.setSingleClickExitEnabled(True)
        assert seen == [True]
