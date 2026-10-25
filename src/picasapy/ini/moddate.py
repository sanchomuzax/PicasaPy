"""A képfájl mtime-jának Picasa-kompatibilis `moddate` alakja."""

from __future__ import annotations


_UNIX_TO_FILETIME_TICKS = 116_444_736_000_000_000


def moddate_from_timestamp_ns(timestamp_ns: int) -> str:
    """Unix-időt alakít 16 kisbetűs hexajegyű, kis-endián FILETIME-má.

    A `moddate` 100 ns-os FILETIME-tárolója az 1601-01-01 UTC kezdőponttól indul;
    a fájlrendszer `st_mtime_ns` értéke 1970-01-01 UTC-től számol.
    """
    filetime = timestamp_ns // 100 + _UNIX_TO_FILETIME_TICKS
    return filetime.to_bytes(8, byteorder="little", signed=False).hex()
