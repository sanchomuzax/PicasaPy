"""Windowsos e-mail küldés a MAPI-n át (#4607).

A Windows-ra nincs `xdg-email`, a `mailto:` pedig csatolmányt nem visz. A
Picasa „Use my default email program" (alapértelmezett levelezőprogram)
ága Windowson a MAPI-t jelentette, ezért itt a rendszer MAPI-kliensének
(`mapi32.dll` → `MAPISendMailW`) adjuk át a mellékleteket. A `MAPI_DIALOG`
zászló miatt a levélszerkesztő megnyílik, és a felhasználó küldés előtt
látja a levelet — a küldés nem történik meg csendben.

A struktúrák a `winmapi.h` elrendezését követik. `ctypes`-szel épülnek, ezért
a felépítésük Linuxon is tesztelhető; a `mapi32.dll` csak a `send_mapi`
hívásakor töltődik be, és az csak Windowson fut."""

from __future__ import annotations

import ctypes
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

# A Windows ULONG mindig 32 bites — a `c_ulong` Linuxon 64 bites lenne, és a
# struktúrák mérete eltérne a Windows-os elrendezéstől.
ULONG = ctypes.c_uint32
LPWSTR = ctypes.c_wchar_p

#: A címzett-osztály: „Címzett" (`MAPI_TO`).
MAPI_TO = 1

#: A `MAPISendMailW` zászlója: a levélszerkesztő megnyitása küldés előtt.
MAPI_DIALOG = 0x00000008

#: A `MAPISendMailW` zászlója: szükség esetén bejelentkezési felület.
MAPI_LOGON_UI = 0x00000001

#: A melléklet `nPosition`-je: „nincs pozíció" (a szöveg végén marad).
MAPI_NO_POSITION = 0xFFFFFFFF

#: Sikeres megnyitás (`SUCCESS_SUCCESS`).
MAPI_OK = 0

#: A felhasználó bezárta a levélszerkesztőt — nem hiba, nem jelzendő.
MAPI_USER_ABORT = 1


class MapiRecipDesc(ctypes.Structure):
    """`MapiRecipDescW`: egy címzett."""

    _fields_ = [
        ("ulReserved", ULONG),
        ("ulRecipClass", ULONG),
        ("lpszName", LPWSTR),
        ("lpszAddress", LPWSTR),
        ("ulEIDSize", ULONG),
        ("lpEntryID", ctypes.c_void_p),
    ]


class MapiFileDesc(ctypes.Structure):
    """`MapiFileDescW`: egy melléklet — a teljes útvonal és a csatolt név."""

    _fields_ = [
        ("ulReserved", ULONG),
        ("flFlags", ULONG),
        ("nPosition", ULONG),
        ("lpszPathName", LPWSTR),
        ("lpszFileName", LPWSTR),
        ("lpFileType", ctypes.c_void_p),
    ]


class MapiMessage(ctypes.Structure):
    """`MapiMessageW`: a levél maga."""

    _fields_ = [
        ("ulReserved", ULONG),
        ("lpszSubject", LPWSTR),
        ("lpszNoteText", LPWSTR),
        ("lpszMessageType", LPWSTR),
        ("lpszDateReceived", LPWSTR),
        ("lpszConversationID", LPWSTR),
        ("flFlags", ULONG),
        ("lpOriginator", ctypes.c_void_p),
        ("nRecipCount", ULONG),
        ("lpRecips", ctypes.POINTER(MapiRecipDesc)),
        ("nFileCount", ULONG),
        ("lpFiles", ctypes.POINTER(MapiFileDesc)),
    ]


@dataclass(frozen=True)
class MapiPayload:
    """A kész `MapiMessage` és az élve tartandó pufferei.

    A MAPI a mutatókon át olvas, ezért a széles-karakteres pufferek és a
    tömbök referenciáját a payload tartja; a `message` egyedül nem elég."""

    message: MapiMessage
    keep: tuple


def _wide(text: str, keep: list) -> LPWSTR:
    """Széles-karakteres puffer, amelynek a referenciáját `keep` őrzi."""
    buffer = ctypes.create_unicode_buffer(text)
    keep.append(buffer)
    return ctypes.cast(buffer, LPWSTR)


def build_mapi_message(
    subject: str,
    body: str,
    attachments: Sequence[Path] = (),
    *,
    recipient: str = "",
) -> MapiPayload:
    """A MAPI-levél összeállítása — üres tárgy/szöveg NULL mutató lesz."""
    keep: list = []
    message = MapiMessage()
    if subject:
        message.lpszSubject = _wide(subject, keep)
    if body:
        message.lpszNoteText = _wide(body, keep)

    addresses = [
        part.strip() for part in re.split(r"[;,]", recipient) if part.strip()
    ]
    if addresses:
        recips = (MapiRecipDesc * len(addresses))()
        for index, address in enumerate(addresses):
            recips[index].ulRecipClass = MAPI_TO
            recips[index].lpszName = _wide(address, keep)
            recips[index].lpszAddress = _wide("SMTP:" + address, keep)
        keep.append(recips)
        message.nRecipCount = len(addresses)
        message.lpRecips = ctypes.cast(recips, ctypes.POINTER(MapiRecipDesc))

    files = (MapiFileDesc * len(attachments))()
    for index, path in enumerate(attachments):
        files[index].nPosition = MAPI_NO_POSITION
        files[index].lpszPathName = _wide(str(path), keep)
        files[index].lpszFileName = _wide(path.name, keep)
    keep.append(files)
    message.nFileCount = len(attachments)
    if attachments:
        message.lpFiles = ctypes.cast(files, ctypes.POINTER(MapiFileDesc))

    return MapiPayload(message=message, keep=tuple(keep))


def send_mapi(payload: MapiPayload, *, dialog: bool = True) -> int:
    """`MAPISendMailW` hívása — csak Windowson.

    Visszatérése a MAPI-kód: `MAPI_OK` a sikeres megnyitás,
    `MAPI_USER_ABORT` a bezárt szerkesztő; minden más hiba."""
    mapi32 = ctypes.WinDLL("mapi32")  # type: ignore[attr-defined]
    send = mapi32.MAPISendMailW
    send.argtypes = [
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(MapiMessage),
        ULONG,
        ULONG,
    ]
    send.restype = ULONG
    flags = MAPI_LOGON_UI | (MAPI_DIALOG if dialog else 0)
    return int(send(0, 0, ctypes.byref(payload.message), flags, 0))
