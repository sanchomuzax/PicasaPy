"""#4325: az első, nyelvbeállítás nélküli indulás nyelvválasztása."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app import language_controller


@pytest.fixture
def settings(tmp_path):
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


@pytest.mark.parametrize(
    ("accepted", "expected"),
    [(True, "hu"), (False, "en")],
)
def test_first_run_choice_is_saved_as_current_and_pending(
    settings, monkeypatch, accepted, expected
):
    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "hu")
    asked = []

    result = language_controller.resolve_first_run_language(
        settings, lambda system_language: asked.append(system_language) or accepted
    )

    assert asked == ["hu"]
    assert result == expected
    assert settings.value(language_controller.LANGUAGE_KEY) == expected
    assert settings.value(language_controller.PENDING_LANGUAGE_KEY) == expected


def test_saved_language_suppresses_first_run_question(settings, monkeypatch):
    settings.setValue(language_controller.LANGUAGE_KEY, "en")
    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "hu")

    def unexpected_prompt(_system_language):
        pytest.fail("beállított nyelvnél nem szabad kérdezni")

    assert language_controller.resolve_first_run_language(settings, unexpected_prompt) is None
    assert settings.value(language_controller.LANGUAGE_KEY) == "en"


@pytest.mark.parametrize("system_language", ["en", "eo"])  # eo: nincs a 41 nyelv között (#4313)
def test_english_or_unsupported_system_language_suppresses_question(
    settings, monkeypatch, system_language
):
    monkeypatch.setattr(
        language_controller, "resolve_system_language", lambda: system_language
    )

    def unexpected_prompt(_system_language):
        pytest.fail("nem felismert vagy angol rendszernyelvnél nem szabad kérdezni")

    assert language_controller.resolve_first_run_language(settings, unexpected_prompt) is None
    assert not settings.contains(language_controller.LANGUAGE_KEY)


def test_saved_first_run_choice_prevents_a_second_question(settings, monkeypatch):
    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "hu")
    calls = []

    def ask(code):
        calls.append(code)
        return True

    assert language_controller.resolve_first_run_language(settings, ask) == "hu"
    assert language_controller.resolve_first_run_language(settings, ask) is None
    assert calls == ["hu"]
