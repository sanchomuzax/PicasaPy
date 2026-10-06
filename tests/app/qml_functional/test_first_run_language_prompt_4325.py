"""#4325: az első indulási felajánlás valódi egérkattintással válaszolható meg."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QPointF, QSettings, Qt, QTimer, QObject
from PySide6.QtTest import QTest

from picasapy.app import application, language_controller


@pytest.mark.parametrize(
    ("accepted", "expected_language", "height_delta", "button_name"),
    [
        (True, "hu", -5, "firstRunLanguagePromptYesButton"),
        (False, "en", 5, "firstRunLanguagePromptNoButton"),
    ],
)
def test_startup_language_prompt_stores_real_click(
    qt_app,
    tmp_path,
    monkeypatch,
    accepted,
    expected_language,
    height_delta,
    button_name,
):
    monkeypatch.delenv("PICASAPY_LANG", raising=False)
    monkeypatch.setattr(language_controller, "resolve_system_language", lambda: "hu")
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    clicked = []
    prompt_text = []
    click_deadline = time.monotonic() + 3.0

    def click_when_ready():
        candidates = [
            window
            for window in qt_app.topLevelWindows()
            if window.objectName() == "firstRunLanguageDialogWindow"
        ]
        if candidates:
            window = candidates[0]
            button = window.findChild(QObject, button_name)
            message = window.findChild(QObject, "firstRunLanguagePromptMessage")
            if (
                button is not None
                and message is not None
                and button.width() > 0
                and button.height() > 0
            ):
                prompt_text.append(str(message.property("text")))
                window.setHeight(window.height() + height_delta)
                qt_app.processEvents()
                point = button.mapToScene(
                    QPointF(button.width() / 2, button.height() / 2)
                ).toPoint()
                QTest.mouseClick(
                    window,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier,
                    point,
                )
                clicked.append(button_name)
                return
        if time.monotonic() >= click_deadline:
            return
        QTimer.singleShot(25, click_when_ready)

    QTimer.singleShot(0, click_when_ready)
    result = application._startup_language(settings, prompt_timeout_ms=3500)

    assert clicked == [button_name], "a prompt gombjára nem történt valódi kattintás"
    assert prompt_text and "PicasaPy" in prompt_text[0]
    assert result == expected_language
    assert settings.value(language_controller.LANGUAGE_KEY) == expected_language
    assert settings.value(language_controller.PENDING_LANGUAGE_KEY) == expected_language

    def unexpected_prompt(_system_language):
        pytest.fail("az elmentett válasz után újra megjelent a kérdés")

    monkeypatch.setattr(application, "_ask_first_run_language", unexpected_prompt)
    assert application._startup_language(settings) == expected_language
