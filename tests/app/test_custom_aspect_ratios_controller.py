"""#448: `CustomAspectRatiosMixin` — a QSettings-alapú perzisztencia és a
QML-nek adott `customAspectRatios`/`lastCropRatio` property/slotok.

A mixin ÖNÁLLÓAN, egy minimális host-osztályon tesztelt (a
`custom_collections_controller.py` tesztelési mintája, #320) — a valódi
`AppController`-be kötés (`controller.py`, forró fájl) az integrátor
feladata."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings


@pytest.fixture
def host(tmp_path):
    from picasapy.app.custom_aspect_ratios_controller import CustomAspectRatiosMixin

    class _Host(CustomAspectRatiosMixin, QObject):
        def __init__(self, settings):
            super().__init__()
            self._settings = settings

        def _get_settings(self):
            return self._settings

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return _Host(settings)


class TestEmptyState:
    def test_no_custom_ratios_by_default(self, host):
        assert host.customAspectRatios == []

    def test_default_last_crop_ratio_is_manual(self, host):
        assert host.lastCropRatio == "Manual"


class TestAddCustomAspectRatio:
    def test_adds_and_lists(self, host):
        host.addCustomAspectRatio(4, 6, "Small print")
        assert host.customAspectRatios == [
            {"name": "Small print", "width": 4.0, "height": 6.0}
        ]

    def test_blank_name_adds_nothing(self, host):
        host.addCustomAspectRatio(4, 6, "   ")
        assert host.customAspectRatios == []

    def test_zero_dimension_adds_nothing(self, host):
        host.addCustomAspectRatio(0, 6, "X")
        assert host.customAspectRatios == []

    def test_signal_emitted_on_add(self, host):
        events = []
        host.customAspectRatiosChanged.connect(lambda: events.append(True))
        host.addCustomAspectRatio(4, 6, "Small print")
        assert events == [True]

    def test_persisted_across_instances(self, host, tmp_path):
        from picasapy.app.custom_aspect_ratios_controller import (
            CustomAspectRatiosMixin,
        )

        host.addCustomAspectRatio(4, 6, "Small print")

        class _Host2(CustomAspectRatiosMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings = settings

            def _get_settings(self):
                return self._settings

        same_settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        other = _Host2(same_settings)
        assert other.customAspectRatios == [
            {"name": "Small print", "width": 4.0, "height": 6.0}
        ]


class TestDeleteCustomAspectRatio:
    def test_delete_removes_entry(self, host):
        host.addCustomAspectRatio(4, 6, "Small print")
        host.deleteCustomAspectRatio("Small print", 4, 6)
        assert host.customAspectRatios == []

    def test_delete_with_wrong_dimensions_is_noop(self, host):
        host.addCustomAspectRatio(4, 6, "Small print")
        host.deleteCustomAspectRatio("Small print", 9, 9)
        assert host.customAspectRatios == [
            {"name": "Small print", "width": 4.0, "height": 6.0}
        ]


class TestLastCropRatio:
    def test_set_and_get(self, host):
        host.setLastCropRatio("4x6")
        assert host.lastCropRatio == "4x6"

    def test_persisted_across_instances(self, host, tmp_path):
        from picasapy.app.custom_aspect_ratios_controller import (
            CustomAspectRatiosMixin,
        )

        host.setLastCropRatio("16x9")

        class _Host2(CustomAspectRatiosMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings = settings

            def _get_settings(self):
                return self._settings

        same_settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        other = _Host2(same_settings)
        assert other.lastCropRatio == "16x9"

    def test_empty_key_is_ignored(self, host):
        host.setLastCropRatio("4x6")
        host.setLastCropRatio("")
        assert host.lastCropRatio == "4x6"

    def test_signal_emitted_on_change(self, host):
        events = []
        host.lastCropRatioChanged.connect(lambda: events.append(True))
        host.setLastCropRatio("4x6")
        assert events == [True]

    def test_setting_same_value_emits_no_extra_signal(self, host):
        host.setLastCropRatio("4x6")
        events = []
        host.lastCropRatioChanged.connect(lambda: events.append(True))
        host.setLastCropRatio("4x6")
        assert events == []
