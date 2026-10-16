"""A Picasa `db3/wordhash.dat` rendezett postinglistáinak olvasása (#4889)."""

from __future__ import annotations

import math
import struct
from pathlib import Path

_HEADER = struct.Struct("<fIIII")
_WORD_RECORD = struct.Struct("<II")
_VERSION = 1.6
_POOL_OFFSET = _HEADER.size
_POOL_SIZE = 0x10000
_WORD_COUNT_OFFSET = _POOL_OFFSET + _POOL_SIZE
_RECORDS_OFFSET = _WORD_COUNT_OFFSET + 4
_ALBUM_PREFIX = b"]album:"


class WordHashFormatError(ValueError):
    """Hibás vagy csonka `wordhash.dat` fájl."""


def read_wordhash(path: Path) -> dict[str, tuple[int, ...]]:
    """Beolvassa a ]album:<token> postinglistákat, az eredeti sorrendben.

    A listaelemek little-endian thumbindex-sorazonosítók. A 0x04 és 0x08
    fejlécmezők jelentése a mért specifikációban ismeretlen, ezért ezeket
    nem egyeztetjük a thumbindex rekordszámával.
    """
    path = Path(path)
    data = path.read_bytes()
    if len(data) < _RECORDS_OFFSET:
        raise WordHashFormatError(f"A fejléc vagy a szótárpool csonka: {path}")

    version, _unknown_04, _unknown_08, pool_size, pool_used = _HEADER.unpack_from(
        data
    )
    if not math.isclose(version, _VERSION, rel_tol=0.0, abs_tol=1e-6):
        raise WordHashFormatError(
            f"Váratlan verzió ({version!r}, várt {_VERSION}): {path}"
        )
    if pool_size != _POOL_SIZE:
        raise WordHashFormatError(
            f"Hibás poolméret ({pool_size:#x}, várt {_POOL_SIZE:#x}): {path}"
        )
    if pool_used > pool_size:
        raise WordHashFormatError(
            f"A foglalt poolhossz túl nagy ({pool_used}): {path}"
        )

    pool = data[_POOL_OFFSET:_WORD_COUNT_OFFSET]
    word_count = struct.unpack_from("<I", data, _WORD_COUNT_OFFSET)[0]
    offset = _RECORDS_OFFSET
    if word_count > (len(data) - offset) // _WORD_RECORD.size:
        raise WordHashFormatError(f"Csonka szótár: a szószám nem fér el: {path}")

    album_lists: dict[str, tuple[int, ...]] = {}
    for word_number in range(word_count):
        if offset + _WORD_RECORD.size > len(data):
            raise WordHashFormatError(f"Csonka szórekord (#{word_number}): {path}")
        word_offset, row_count = _WORD_RECORD.unpack_from(data, offset)
        offset += _WORD_RECORD.size

        if word_offset >= pool_used or (word_offset and pool[word_offset - 1] != 0):
            raise WordHashFormatError(
                f"A szóeltolás nem foglalt sztringkezdetre mutat "
                f"({word_offset}): {path}"
            )
        terminator = pool.find(b"\x00", word_offset, pool_used)
        if terminator < 0:
            raise WordHashFormatError(
                f"Nincs lezáró nulla a szó végén (#{word_number}): {path}"
            )
        word = pool[word_offset:terminator]

        row_bytes = row_count * 4
        if row_bytes > len(data) - offset:
            raise WordHashFormatError(
                f"Csonka rekordlista (#{word_number}, {row_count} sor): {path}"
            )
        if word.startswith(_ALBUM_PREFIX):
            try:
                token = word.decode("ascii")
            except UnicodeDecodeError as exc:
                raise WordHashFormatError(
                    f"Érvénytelen albumtoken-kódolás (#{word_number}): {path}"
                ) from exc
            if token in album_lists:
                raise WordHashFormatError(f"Ismétlődő albumtoken ({token}): {path}")
            rows = struct.unpack_from(f"<{row_count}I", data, offset)
            album_lists[token] = tuple(rows)
        offset += row_bytes

    if offset != len(data):
        raise WordHashFormatError(
            f"A wordhash.dat fájl végén {len(data) - offset} bájt maradt: {path}"
        )
    return album_lists


__all__ = ["WordHashFormatError", "read_wordhash"]
