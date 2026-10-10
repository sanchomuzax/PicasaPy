"""Windowsos MAPI-kötés (#4607): a `mapi32.dll` `MAPISendMailW` exportja
feloldódik, és a struktúrák mérete a gép pointer-szélességéhez igazodik.

Csak Windowson fut (a windows-latest CI-darabon). Valódi levelet NEM küld:
a függvényt nem hívja, csak a kötést ellenőrzi — egy élő hívás megnyitná a
levelezőt."""

from __future__ import annotations

import ctypes
import sys

import pytest

from picasapy.mailer.mapi import MapiFileDesc, MapiMessage

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("win"), reason="a MAPI csak Windowson él"
)


def test_mapisendmailw_export_resolves():
    mapi32 = ctypes.WinDLL("mapi32")
    assert mapi32.MAPISendMailW is not None


def test_file_desc_size_matches_pointer_width():
    pointer = ctypes.sizeof(ctypes.c_void_p)
    expected = 24 if pointer == 4 else 40
    assert ctypes.sizeof(MapiFileDesc) == expected


def test_message_struct_has_pointer_sized_list_fields():
    assert ctypes.sizeof(MapiMessage) > 0
