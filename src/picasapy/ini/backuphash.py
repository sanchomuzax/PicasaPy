"""A Picasa képszintű, 16 bites `backuphash` írása (#5810)."""

from __future__ import annotations

import struct
from datetime import datetime

from .document import IniDocument

_OLE_DAY_COUNTER_OFFSET = 0xA96C7
_SECONDS_PER_DAY = 86400.0


def backuphash_for_local_datetime(local_datetime: datetime) -> int:
    """Az eredeti Picasa OLE DATE-képletének négy 16 bites szavas XOR-ja.

    A bemenet helyi, naiv dátum-idő. A Picasa `tm` mezői másodperc
    pontosságúak, ezért a mikro/másodpercet nem vesszük figyelembe.
    """
    if local_datetime.tzinfo is not None:
        raise ValueError("helyi, időzóna nélküli datetime szükséges")

    # A Picasa dátumsegédének nap-számlálója az év 1. napjától számol.
    # A Python ordinalhoz adott 365-tel 1899-12-30 nap-számlálója pontosan
    # 693959, amelyből a bináris 0xa96c7 konstans kerül kivonásra.
    day_counter = local_datetime.date().toordinal() + 365
    ole_days = day_counter - _OLE_DAY_COUNTER_OFFSET
    seconds = (
        local_datetime.hour * 3600
        + local_datetime.minute * 60
        + local_datetime.second
    )
    ole_date = float(ole_days) + seconds / _SECONDS_PER_DAY
    words = struct.unpack("<4H", struct.pack("<d", ole_date))
    return words[0] ^ words[1] ^ words[2] ^ words[3]


def with_backuphash(
    document: IniDocument,
    photo_name: str,
    local_datetime: datetime | None = None,
) -> IniDocument:
    """A kép szakaszához hozzáadja/frissíti a decimális `backuphash`-t."""
    when = datetime.now() if local_datetime is None else local_datetime
    value = backuphash_for_local_datetime(when)
    return document.with_value(photo_name, "backuphash", str(value))
