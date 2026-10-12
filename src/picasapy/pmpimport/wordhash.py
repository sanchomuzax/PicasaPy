"""A Picasa `db3/wordhash.dat` albumlistáinak olvasása (#4889).

A `]album:<token>` szavakhoz tartozó rekordindex-sorozat sorrendje a mappa
képeinek kézi sorrendje. A visszaadott rekordindexek a `thumbindex.db`
soraival azonos térben vannak.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

_FEJ = struct.Struct("<fIIII")
_SZAV_REKORD = struct.Struct("<II")
_VERZIO = 1.6
_POOL_MERET = 0x10000
_ALBUM_PREFIX = b"]album:"


class WordHashFormatError(ValueError):
    """Hibás vagy csonka `wordhash.dat` fájl."""


def read_wordhash(
    path: Path, *, expected_entity_count: int | None = None
) -> dict[str, tuple[int, ...]]:
    """Beolvassa a `]album:` szólistákat, az elemek eredeti sorrendjében.

    A specifikáció szerinti teljes fájlt ellenőrzi: verzió, thumbindex-sorok
    száma, 64 KiB-os poolméret, rekordhatárok és zéró maradék.
    """
    path = Path(path)
    data = path.read_bytes()
    if len(data) < _FEJ.size:
        raise WordHashFormatError(f"A fejléc túl rövid: {path}")

    version, entity_count, pool_count, pool_size, last_pool_used = _FEJ.unpack_from(
        data
    )
    if not math.isclose(version, _VERZIO, rel_tol=0.0, abs_tol=1e-6):
        raise WordHashFormatError(
            f"Váratlan verzió ({version!r}, várt {_VERZIO}): {path}"
        )
    if expected_entity_count is not None and entity_count != expected_entity_count:
        raise WordHashFormatError(
            f"Hibás entitásszám ({entity_count}, várt {expected_entity_count}): {path}"
        )
    if pool_count == 0:
        raise WordHashFormatError(f"A szótár pool-száma nulla: {path}")
    if pool_size != _POOL_MERET:
        raise WordHashFormatError(
            f"Hibás poolméret ({pool_size:#x}, várt {_POOL_MERET:#x}): {path}"
        )
    if last_pool_used > pool_size:
        raise WordHashFormatError(
            f"A záró pool foglalt hossza túl nagy ({last_pool_used}): {path}"
        )

    dictionary_start = _FEJ.size
    dictionary_size = pool_count * pool_size
    dictionary_end = dictionary_start + dictionary_size
    if dictionary_end + 4 > len(data):
        raise WordHashFormatError(f"Csonka szótárpool: {path}")
    dictionary = data[dictionary_start:dictionary_end]
    word_count_offset = dictionary_end
    word_count = struct.unpack_from("<I", data, word_count_offset)[0]
    offset = word_count_offset + 4
    if word_count > (len(data) - offset) // _SZAV_REKORD.size:
        raise WordHashFormatError(f"Csonka szótár: a szószám nem fér el: {path}")

    last_pool_start = (pool_count - 1) * pool_size
    used_dictionary_end = last_pool_start + last_pool_used
    album_words: dict[str, tuple[int, ...]] = {}
    for word_number in range(word_count):
        if offset + _SZAV_REKORD.size > len(data):
            raise WordHashFormatError(f"Csonka szórekord (#{word_number}): {path}")
        word_offset, row_count = _SZAV_REKORD.unpack_from(data, offset)
        offset += _SZAV_REKORD.size
        row_bytes = row_count * 4
        if row_bytes > len(data) - offset:
            raise WordHashFormatError(
                f"Csonka rekordlista (#{word_number}, {row_count} sor): {path}"
            )

        pool_index = word_offset // pool_size
        pool_end = min((pool_index + 1) * pool_size, used_dictionary_end)
        if word_offset >= used_dictionary_end or pool_index >= pool_count:
            raise WordHashFormatError(
                f"A szóeltolás kívül esik a foglalt szótáron ({word_offset}): {path}"
            )
        terminator = dictionary.find(b"\x00", word_offset, pool_end)
        if terminator < 0:
            raise WordHashFormatError(
                f"Nincs lezáró nulla a szó végén (#{word_number}): {path}"
            )
        word = dictionary[word_offset:terminator]
        if word.startswith(_ALBUM_PREFIX):
            try:
                album_token = word.decode("ascii")
            except UnicodeDecodeError as exc:
                raise WordHashFormatError(
                    f"Érvénytelen albumtoken-kódolás (#{word_number}): {path}"
                ) from exc
            if album_token in album_words:
                raise WordHashFormatError(
                    f"Ismétlődő albumtoken ({album_token}): {path}"
                )
            rows = struct.unpack_from(f"<{row_count}I", data, offset)
            album_words[album_token] = tuple(rows)
        offset += row_bytes

    if offset != len(data):
        raise WordHashFormatError(
            f"A wordhash.dat fájl végén {len(data) - offset} bájt maradt: {path}"
        )
    return album_words


__all__ = ["WordHashFormatError", "read_wordhash"]
