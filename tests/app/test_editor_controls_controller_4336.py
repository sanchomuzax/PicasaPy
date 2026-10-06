"""A Nézet ▸ Show Edit Controls beállításának tárolása (#4336)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.app.editor_controls_controller import (
    EDITOR_CONTROLS_KEY,
    EditorControlsMixin,
)


@pytest.fixture
def controller(qt_app, tmp_path):
    class _Probe(EditorControlsMixin, QObject):
        def __init__(self, settings):
            super().__init__()
            self._settings = settings
            self._init_editor_controls()

        def _get_settings(self):
            return self._settings

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return _Probe(settings)


def test_alapbol_latszik_es_a_kapcsolo_beallitast_ment(controller):
    assert controller.editorControlsVisible is True

    controller.setEditorControlsVisible(False)

    assert controller.editorControlsVisible is False
    assert controller._get_settings().value(EDITOR_CONTROLS_KEY) == "false"
    controller.setEditorControlsVisible(True)
    assert controller.editorControlsVisible is True


def test_uj_vezerlopeldany_visszaallitja_a_mentett_allapot(qt_app, tmp_path):
    class _Probe(EditorControlsMixin, QObject):
        def __init__(self, settings):
            super().__init__()
            self._settings = settings
            self._init_editor_controls()

        def _get_settings(self):
            return self._settings

    path = str(tmp_path / "settings.ini")
    first_settings = QSettings(path, QSettings.Format.IniFormat)
    first = _Probe(first_settings)
    first.setEditorControlsVisible(False)
    first_settings.sync()

    second_settings = QSettings(path, QSettings.Format.IniFormat)
    assert _Probe(second_settings).editorControlsVisible is False


def test_a_jelzes_csak_valodi_allapotvaltaskor_jon(controller):
    seen = []
    controller.editorControlsVisibleChanged.connect(
        lambda: seen.append(controller.editorControlsVisible)
    )

    controller.setEditorControlsVisible(True)
    assert seen == []

    controller.setEditorControlsVisible(False)
    assert seen == [False]


def test_hibas_beallitasnal_lathato_marad(qt_app, tmp_path):
    class _Probe(EditorControlsMixin, QObject):
        def __init__(self, settings):
            super().__init__()
            self._settings = settings
            self._init_editor_controls()

        def _get_settings(self):
            return self._settings

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(EDITOR_CONTROLS_KEY, "talán")

    assert _Probe(settings).editorControlsVisible is True
