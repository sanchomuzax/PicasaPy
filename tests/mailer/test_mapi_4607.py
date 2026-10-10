"""`picasapy.mailer.mapi` — a MAPI-üzenet (`MapiMessage`) felépítése (#4607).

Tiszta ctypes-struktúra-építés: a `mapi32.dll`-t NEM hívja, így Linuxon is
fut. A tényleges Windows-os kötést a `test_mapi_windows_4607.py` védi."""

from __future__ import annotations

import ctypes
from pathlib import Path
from unittest.mock import MagicMock, patch

from picasapy.mailer.mapi import (
    MAPI_DIALOG,
    MAPI_LOGON_UI,
    MAPI_TO,
    build_mapi_message,
    send_mapi,
)


def _file_names(payload):
    message = payload.message
    return [
        message.lpFiles[i].lpszPathName for i in range(message.nFileCount)
    ], [message.lpFiles[i].lpszFileName for i in range(message.nFileCount)]


class TestBuildMapiMessage:
    def test_every_attachment_becomes_one_file_desc(self):
        paths = [Path("/tmp/a.jpg"), Path("/tmp/b.jpg")]
        payload = build_mapi_message("Tárgy", "Szöveg", paths)
        assert payload.message.nFileCount == 2
        full, names = _file_names(payload)
        assert full == [str(path) for path in paths]
        assert names == ["a.jpg", "b.jpg"]

    def test_subject_and_body_are_passed_as_wide_text(self):
        payload = build_mapi_message("Képek: ő ű", "Üdv\nSzöveg", [])
        assert payload.message.lpszSubject == "Képek: ő ű"
        assert payload.message.lpszNoteText == "Üdv\nSzöveg"

    def test_empty_subject_and_body_are_null(self):
        payload = build_mapi_message("", "", [])
        assert not payload.message.lpszSubject
        assert not payload.message.lpszNoteText

    def test_no_attachments_means_zero_files(self):
        payload = build_mapi_message("Tárgy", "Szöveg", [])
        assert payload.message.nFileCount == 0

    def test_recipient_is_a_to_recipient(self):
        payload = build_mapi_message(
            "Tárgy", "Szöveg", [], recipient="valaki@example.com"
        )
        recip = payload.message.lpRecips[0]
        assert payload.message.nRecipCount == 1
        assert recip.ulRecipClass == MAPI_TO
        assert recip.lpszName == "valaki@example.com"

    def test_no_recipient_leaves_the_list_empty(self):
        payload = build_mapi_message("Tárgy", "Szöveg", [])
        assert payload.message.nRecipCount == 0

    def test_file_desc_layout_matches_pointer_size(self):
        # a MapiFileDesc két pointert és három ULONG-ot tartalmaz, a
        # pointer-szélesség szerinti kitöltéssel — a 32/64 bites
        # Windows-ra egyaránt igaz, hogy a méret a mutatóhoz igazodik
        from picasapy.mailer.mapi import MapiFileDesc

        pointer = ctypes.sizeof(ctypes.c_void_p)
        assert ctypes.sizeof(MapiFileDesc) == 3 * 4 + (4 if pointer == 8 else 0) + 3 * pointer


class TestPositionAndRecipients:
    def test_attachment_position_is_none(self):
        payload = build_mapi_message("T", "S", [Path("/tmp/a.jpg")])
        assert payload.message.lpFiles[0].nPosition == 0xFFFFFFFF

    def test_recipients_split_on_semicolon_and_comma(self):
        payload = build_mapi_message(
            "T", "S", [], recipient="a@x.hu; b@x.hu, ,c@x.hu;  "
        )
        message = payload.message
        assert message.nRecipCount == 3
        addrs = [message.lpRecips[i].lpszAddress for i in range(3)]
        names = [message.lpRecips[i].lpszName for i in range(3)]
        assert names == ["a@x.hu", "b@x.hu", "c@x.hu"]
        assert addrs == ["SMTP:a@x.hu", "SMTP:b@x.hu", "SMTP:c@x.hu"]
        assert all(message.lpRecips[i].ulRecipClass == MAPI_TO for i in range(3))

    def test_blank_recipient_means_no_recipients(self):
        assert build_mapi_message("T", "S", [], recipient=" ; ,").message.nRecipCount == 0


class TestSendFlags:
    def _run(self, dialog):
        fake = MagicMock(return_value=0)
        dll = MagicMock()
        dll.MAPISendMailW = fake
        payload = build_mapi_message("T", "S", [])
        with patch.object(ctypes, "WinDLL", create=True, return_value=dll):
            send_mapi(payload, dialog=dialog)
        return fake

    def test_logon_ui_always_set(self):
        for dialog in (True, False):
            flags = self._run(dialog).call_args[0][3]
            assert flags & MAPI_LOGON_UI

    def test_dialog_flag_with_dialog(self):
        assert self._run(True).call_args[0][3] == MAPI_LOGON_UI | MAPI_DIALOG
        assert self._run(False).call_args[0][3] == MAPI_LOGON_UI

    def test_argtypes_set(self):
        fake = self._run(True)
        assert fake.restype is not None
        assert len(fake.argtypes) == 5
