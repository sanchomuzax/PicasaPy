"""`EmailController` Windows-ága (#4607): a melléklet MAPI-n át csatolódik.

A `_is_windows` és a `_mapi_send` modulszintű fogantyú: a teszt Linuxon
fut, a MAPI-hívást mockolja, így valódi levelezőt nem nyit meg."""

from __future__ import annotations

import os

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
