"""#4325: az első, nyelvbeállítás nélküli indulás nyelvválasztása."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app import language_controller


def test_first_run_prompt_uses_the_original_picasa_copy():
    qml_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "picasapy"
        / "app"
        / "qml"
        / "PicasaPy"
        / "FirstRunLanguageDialog.qml"
    )
    qml = qml_path.read_text(encoding="utf-8")

    assert 'Picasa is now available in your system\'s native language.' in qml
    assert 'Would you like to switch Picasa from English to this language?' in qml
    assert 'title: qsTr("Confirm")' in qml
    assert 'text: qsTr("Yes")' in qml
    assert 'text: qsTr("No")' in qml
    assert "PicasaPy is now available" not in qml


@pytest.fixture
def settings(tmp_path):
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


@pytest.fixture
def windows_nt():
    """A felajánlás platformtól független; a név a régi tesztek olvashatóságát őrzi."""


@pytest.mark.parametrize(
    ("accepted", "expected_language", "expected_pending"),
    [(True, "de", "system"), (False, "en", "en")],
)
def test_first_run_choice_is_saved_as_current_and_pending(
    settings, monkeypatch, windows_nt, accepted, expected_language, expected_pending
):
    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "de")
    asked = []

    result = language_controller.resolve_first_run_language(
        settings, lambda system_language: asked.append(system_language) or accepted
    )

    assert asked == ["de"]
    assert result == expected_language
    assert settings.value(language_controller.LANGUAGE_KEY) == expected_language
    assert settings.value(language_controller.PENDING_LANGUAGE_KEY) == expected_pending


@pytest.mark.parametrize(
    "system_language",
    ["es", "fr", "it", "de", "ja", "zh-CN", "zh-TW", "ko", "ru", "pt", "nl", "fa"],
)
def test_first_run_prompt_accepts_the_original_recognized_languages(
    settings, monkeypatch, windows_nt, system_language
):
    monkeypatch.setattr(
        language_controller, "resolve_system_language", lambda: system_language
    )
    asked = []

    assert language_controller.resolve_first_run_language(
        settings, lambda code: asked.append(code) or False
    ) == "en"
    assert asked == [system_language]
    assert settings.value(language_controller.LANGUAGE_KEY) == "en"
    assert settings.value(language_controller.PENDING_LANGUAGE_KEY) == "en"


@pytest.mark.parametrize("system_language", ["hu", "fil"])
def test_first_run_prompt_also_offers_picasapy_only_catalogues(
    settings, monkeypatch, windows_nt, system_language
):
    monkeypatch.setattr(
        language_controller, "resolve_system_language", lambda: system_language
    )
    asked = []

    assert language_controller.resolve_first_run_language(
        settings, lambda code: asked.append(code) or True
    ) == system_language
    assert asked == [system_language]
    assert settings.value(language_controller.LANGUAGE_KEY) == system_language
    assert settings.value(language_controller.PENDING_LANGUAGE_KEY) == "system"


def test_saved_language_suppresses_first_run_question(settings, monkeypatch):
    settings.setValue(language_controller.LANGUAGE_KEY, "en")
    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "hu")

    def unexpected_prompt(_system_language):
        pytest.fail("beállított nyelvnél nem szabad kérdezni")

    assert language_controller.resolve_first_run_language(settings, unexpected_prompt) is None
    assert settings.value(language_controller.LANGUAGE_KEY) == "en"


@pytest.mark.parametrize("system_language", ["en", "enUK", "eo"])
def test_english_or_unsupported_system_language_suppresses_question(
    settings, monkeypatch, windows_nt, system_language
):
    monkeypatch.setattr(
        language_controller, "resolve_system_language", lambda: system_language
    )

    def unexpected_prompt(_system_language):
        pytest.fail("nem felismert vagy angol rendszernyelvnél nem szabad kérdezni")

    assert language_controller.resolve_first_run_language(settings, unexpected_prompt) is None
    assert not settings.contains(language_controller.LANGUAGE_KEY)


def test_saved_first_run_choice_prevents_a_second_question(settings, monkeypatch, windows_nt):
    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "hu")
    calls = []

    def ask(code):
        calls.append(code)
        return True

    assert language_controller.resolve_first_run_language(settings, ask) == "hu"
    assert language_controller.resolve_first_run_language(settings, ask) is None
    assert calls == ["hu"]


def test_accepted_system_choice_tracks_the_system_language_on_later_startup(
    settings, monkeypatch, windows_nt
):
    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "hu")
    assert language_controller.resolve_first_run_language(settings, lambda _code: True) == "hu"
    assert settings.value(language_controller.PENDING_LANGUAGE_KEY) == "system"

    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "fr")
    assert language_controller.resolve_startup_language(settings) == "fr"
    assert settings.value(language_controller.LANGUAGE_KEY) == "fr"
    assert settings.value(language_controller.PENDING_LANGUAGE_KEY) == "system"


def test_linux_also_offers_the_first_run_language_prompt(settings, monkeypatch):
    # PicasaPy-eltérés: az eredeti csak Windowson futott, a PicasaPy platformtól függetlenül felajánl.
    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "de")

    assert language_controller.resolve_first_run_language(settings, lambda _l: True) == "de"
    assert settings.value(language_controller.LANGUAGE_KEY) == "de"
