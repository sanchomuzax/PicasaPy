"""Bináris fixtúra-építők a PMP/thumbindex tesztekhez.

A formátum a keresztvalidált spec szerint készül
(docs/reference-repos-audit.md, docs/specs/pmp-database.md) — a tesztek
szintetikus, bitre pontos fájlokat építenek vele.
"""

from __future__ import annotations

import struct
from collections.abc import Iterable, Sequence

PMP_MAGIC = 0x3FCCCCCD
THUMBINDEX_MAGIC = 0x40466666

_NUMERIC_FORMATS = {
    0x1: "<I",
    0x2: "<d",
    0x3: "<B",
    0x4: "<Q",
    0x5: "<H",
    0x7: "<I",
}


def build_pmp(
    field_type: int,
    values: Sequence,
    *,
    magic: int = PMP_MAGIC,
    type2: int | None = None,
    count: int | None = None,
) -> bytes:
    """PMP oszlopfájl bájtjai: 20 bájtos fejléc + rekordok szeparátor nélkül.

    A `magic`/`type2`/`count` felülírható hibás fejlécek előállításához.
    """
    if type2 is None:
        type2 = field_type
    if count is None:
        count = len(values)
    header = struct.pack(
        "<IHHIHHI", magic, field_type, 0x1332, 0x00000002, type2, 0x1332, count
    )
    if field_type in (0x0, 0x6):
        body = b"".join(str(v).encode("utf-8") + b"\x00" for v in values)
    else:
        fmt = _NUMERIC_FORMATS[field_type]
        body = b"".join(struct.pack(fmt, v) for v in values)
    return header + body


def build_thumbindex(
    entries: Iterable[tuple[str, int | None]],
    *,
    magic: int = THUMBINDEX_MAGIC,
    terminator: bytes = b"\x00",
) -> bytes:
    """thumbindex.db bájtjai: fejléc + (név, 26 kitöltő bájt, szülőindex)."""
    entry_list = list(entries)
    out = [struct.pack("<II", magic, len(entry_list))]
    for name, parent in entry_list:
        parent_value = 0xFFFFFFFF if parent is None else parent
        out.append(name.encode("utf-8") + terminator)
        out.append(b"\x00" * 26)
        out.append(struct.pack("<I", parent_value))
    return b"".join(out)
