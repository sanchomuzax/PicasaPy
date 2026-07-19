"""PMP oszlopfájl-olvasó (Picasa db3, oszlop-alapú bináris formátum).

Spec: docs/specs/pmp-database.md és docs/reference-repos-audit.md —
20 bájtos little-endian fejléc (magic, mezőtípus kétszer, rekordszám),
utána a rekordok szeparátor nélkül. A db3-at CSAK olvassuk.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

PMP_MAGIC = 0x3FCCCCCD
_HEADER = struct.Struct("<IHHIHHI")
_STRING_TYPES = frozenset({0x0, 0x6})
_NUMERIC_STRUCTS = {
    0x1: struct.Struct("<I"),
    0x2: struct.Struct("<d"),
    0x3: struct.Struct("<B"),
    0x4: struct.Struct("<Q"),
    0x5: struct.Struct("<H"),
    0x7: struct.Struct("<I"),
}
_OLE_EPOCH = datetime(1899, 12, 30)


class PmpFormatError(ValueError):
    """Sérült vagy nem PMP formátumú bemenet."""


@dataclass(frozen=True)
class PmpColumn:
    """Egy logikai tábla egyetlen oszlopa (pl. imagedata.rotate)."""

    name: str
    field_type: int
    values: tuple


def parse_pmp(data: bytes, *, name: str) -> PmpColumn:
    """PMP oszlopfájl bájtjainak dekódolása."""
    if len(data) < _HEADER.size:
        raise PmpFormatError(f"{name}: csonka fejléc ({len(data)} bájt)")
    magic, type1, c1, c2, type2, c3, count = _HEADER.unpack_from(data)
    if magic != PMP_MAGIC:
        raise PmpFormatError(f"{name}: hibás magic: {magic:#010x}")
    if type1 != type2:
        raise PmpFormatError(f"{name}: mezőtípus-eltérés a fejlécben ({type1} != {type2})")
    if (c1, c3) != (0x1332, 0x1332) or c2 != 0x00000002:
        raise PmpFormatError(f"{name}: hibás fejléc-konstansok")
    body = data[_HEADER.size :]
    if type1 in _STRING_TYPES:
        values = _parse_strings(body, count, name)
    elif type1 in _NUMERIC_STRUCTS:
        values = _parse_numbers(body, count, _NUMERIC_STRUCTS[type1], name)
    else:
        raise PmpFormatError(f"{name}: ismeretlen mezőtípus: {type1:#x}")
    return PmpColumn(name=name, field_type=type1, values=values)


def read_pmp(path: Path) -> PmpColumn:
    """Oszlopfájl beolvasása; az oszlopnév a fájlnév `tábla_` utáni része."""
    name = path.stem.split("_", 1)[-1]
    try:
        return parse_pmp(path.read_bytes(), name=name)
    except PmpFormatError as exc:
        raise PmpFormatError(f"{path.name}: {exc}") from exc


def decode_ole_date(value: float) -> datetime:
    """OLE variant time: napok száma 1899-12-30-tól (törtnap = napszak)."""
    return _OLE_EPOCH + timedelta(days=value)


def _parse_strings(body: bytes, count: int, name: str) -> tuple[str, ...]:
    values: list[str] = []
    offset = 0
    for _ in range(count):
        end = body.find(b"\x00", offset)
        if end < 0:
            raise PmpFormatError(
                f"{name}: csonka string-oszlop ({len(values)}/{count} rekord)"
            )
        values.append(body[offset:end].decode("utf-8"))
        offset = end + 1
    return tuple(values)


def _parse_numbers(
    body: bytes, count: int, fmt: struct.Struct, name: str
) -> tuple:
    if len(body) < count * fmt.size:
        raise PmpFormatError(
            f"{name}: csonka numerikus oszlop ({len(body)} bájt, {count} rekord kellene)"
        )
    return tuple(fmt.unpack_from(body, i * fmt.size)[0] for i in range(count))
