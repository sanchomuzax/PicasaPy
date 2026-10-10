"""`picasapy.mailer.mapi` — a MAPI-üzenet (`MapiMessage`) felépítése (#4607).

Tiszta ctypes-struktúra-építés: a `mapi32.dll`-t NEM hívja, így Linuxon is
fut. A tényleges Windows-os kötést a `test_mapi_windows_4607.py` védi."""

from __future__ import annotations

import ctypes
from pathlib import Path

from picasapy.mailer.mapi import MAPI_TO, build_mapi_message


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
