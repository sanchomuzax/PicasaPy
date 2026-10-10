"""`EmailController` Windows-ága (#4607): a melléklet MAPI-n át csatolódik.

A `_platform` és a `_mapi_send` modulszintű fogantyú: a teszt Linuxon
fut, a MAPI-hívást mockolja, így valódi levelezőt nem nyit meg."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import patch

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication

from picasapy.app import email_controller as email_controller_module
from picasapy.app.email_controller import EmailController


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


def _controller(tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    controller = EmailController(photo_source=lambda: [], settings=settings)
    controller.setUseDefaultClient(True)
    return controller


def _windows(mapi_result):
    """Windows-os környezet: a MAPI-hívás a megadott kóddal tér vissza."""
    return (
        patch.object(email_controller_module, "_platform", return_value="win32"),
        patch.object(
            email_controller_module, "_mapi_send", return_value=mapi_result
        ),
    )


class TestWindowsMapiSend:
    def test_attachments_are_handed_to_mapi(self, qt_app, tmp_path):
        controller = _controller(tmp_path)
        is_win, mapi = _windows(0)
        with is_win, mapi as send, patch.object(
            email_controller_module.QDesktopServices, "openUrl"
        ) as open_url:
            ok = controller.sendWithDefaultClient(
                ["C:/kepek/a.jpg", "C:/kepek/b.jpg"], "Tárgy", "Szöveg", False
            )
        assert ok is True
        payload = send.call_args[0][0]
        assert payload.message.nFileCount == 2
        assert payload.message.lpszSubject == "Tárgy"
        # a mailto-visszaesés csatolmány nélkül nyitna levelet: Windowson
        # ilyenkor sem szabad oda visszaesni
        open_url.assert_not_called()

    def test_recipient_reaches_mapi(self, qt_app, tmp_path):
        controller = _controller(tmp_path)
        controller.setComposeRecipient("valaki@example.com")
        is_win, mapi = _windows(0)
        with is_win, mapi as send:
            controller.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)
        assert send.call_args[0][0].message.nRecipCount == 1

    def test_user_cancelling_the_compose_window_is_silent(self, qt_app, tmp_path):
        controller = _controller(tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        is_win, mapi = _windows(email_controller_module.MAPI_USER_ABORT)
        with is_win, mapi:
            ok = controller.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)
        assert ok is False
        assert events == []

    def test_other_mapi_error_emits_failure(self, qt_app, tmp_path):
        controller = _controller(tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        is_win, mapi = _windows(2)
        with is_win, mapi:
            ok = controller.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)
        assert ok is False
        assert events == [controller.tr("No email program was found.")]


class TestWindowsMapiRobustness:
    def test_mapi_exception_emits_failure(self, qt_app, tmp_path):
        controller = _controller(tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        for error in (OSError("x"), AttributeError("x"), ctypes.ArgumentError("x")):
            with patch.object(
                email_controller_module, "_platform", return_value="win32"
            ), patch.object(
                email_controller_module, "_mapi_send", side_effect=error
            ):
                ok = controller.sendWithDefaultClient(
                    ["C:/a.jpg"], "T", "Sz", False
                )
            assert ok is False
        assert events == [controller.tr("No email program was found.")] * 3

    def test_reentrant_call_is_refused_and_flag_resets(self, qt_app, tmp_path):
        controller = _controller(tmp_path)
        inner = []

        def fake_send(payload):
            inner.append(
                controller._kuldes_mapi("T", "Sz", [Path("C:/b.jpg")], "")
            )
            return 0

        with patch.object(
            email_controller_module, "_platform", return_value="win32"
        ), patch.object(email_controller_module, "_mapi_send", fake_send):
            ok = controller.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)
        assert ok is True
        assert inner == [False]
        # a jelző visszaállt: újabb küldés lefut
        is_win, mapi = _windows(0)
        with is_win, mapi as send:
            assert controller.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)
        assert send.call_count == 1

    def test_flag_resets_after_exception(self, qt_app, tmp_path):
        controller = _controller(tmp_path)
        with patch.object(
            email_controller_module, "_platform", return_value="win32"
        ), patch.object(
            email_controller_module, "_mapi_send", side_effect=OSError("x")
        ):
            controller.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)
        is_win, mapi = _windows(0)
        with is_win, mapi:
            assert controller.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)


def test_old_email_tests_never_reach_real_mapi_on_win32(
    qt_app, tmp_path, monkeypatch
):
    """A conftest-őr: platform nélküli tesztben a _mapi_send tiltott."""
    controller = _controller(tmp_path)
    with pytest.raises(AssertionError):
        email_controller_module._mapi_send(None)
    assert email_controller_module._platform() == "linux"
    del controller
