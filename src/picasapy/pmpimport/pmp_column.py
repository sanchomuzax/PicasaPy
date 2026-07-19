""".pmp oszlopfájl olvasása (#1) — a Picasa központi (PMP) adatbázisa nem
relációs: minden logikai tábla minden oszlopa külön `.pmp` fájl.

Formátum keresztvalidálva (Java `PMPDB.java` ↔ Python `pmpinfo.py`,
ld. `docs/reference-repos-audit.md`): 20 bájtos little-endian fejléc, utána
a nyers rekordok egymás után, szeparátor nélkül. Csak olvasás — a PicasaPy
a PMP-adatbázist sosem írja.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

_MAGIC = 0x3FCCCCCD
_CONST_1332 = 0x1332
_CONST_2 = 0x00000002
_HEADER = struct.Struct("<IHHIHHI")

TYPE_STRING = frozenset({0x0, 0x6})
TYPE_UINT32 = frozenset({0x1, 0x7})
TYPE_DOUBLE = frozenset({0x2})
TYPE_UINT8 = frozenset({0x3})
TYPE_UINT64 = frozenset({0x4})
TYPE_UINT16 = frozenset({0x5})


class PmpFormatError(ValueError):
    """Érvénytelen vagy sérült `.pmp` fejléc/rekord."""


@dataclass(frozen=True)
class PmpColumn:
    """Egy beolvasott oszlop: a mezőtípus + a rekordok sorrendhelyes tuple-je."""

    field_type: int
    values: tuple

    def __len__(self) -> int:
        return len(self.values)


def read_pmp_column(path: Path) -> PmpColumn:
    """Egy `.pmp` fájl teljes beolvasása.

    Raises:
        PmpFormatError: Érvénytelen magic/konstans/mezőtípus-eltérés, vagy
            a rekordadatok csonkák/hiányosak a fejlécben jelzett
            rekordszámhoz képest.
    """
    data = Path(path).read_bytes()
    if len(data) < _HEADER.size:
        raise PmpFormatError(f"A fejléc túl rövid: {path}")
    magic, type1, const_a, const2, type1_repeat, const_b, count = _HEADER.unpack_from(
        data, 0
    )
    if magic != _MAGIC:
        raise PmpFormatError(f"Érvénytelen magic ({magic:#x}): {path}")
    if type1 != type1_repeat:
        raise PmpFormatError(
            f"A mezőtípus két bejegyzése nem egyezik ({type1:#x} != "
            f"{type1_repeat:#x}): {path}"
        )
    if const_a != _CONST_1332 or const_b != _CONST_1332:
        raise PmpFormatError(f"Váratlan konstans a fejlécben: {path}")
    if const2 != _CONST_2:
        raise PmpFormatError(f"Váratlan konstans a fejlécben: {path}")

    values = _read_records(data, _HEADER.size, type1, count, path)
    return PmpColumn(field_type=type1, values=tuple(values))


def _read_records(
    data: bytes, offset: int, field_type: int, count: int, path: Path
) -> list:
    if field_type in TYPE_STRING:
        return _read_strings(data, offset, count, path)
    fmt, size = _FIXED_WIDTH.get(field_type, (None, None))
    if fmt is None:
        raise PmpFormatError(f"Ismeretlen mezőtípus ({field_type:#x}): {path}")
    end = offset + size * count
    if end > len(data):
        raise PmpFormatError(f"Csonka rekordadat ({count} rekord): {path}")
    return list(struct.unpack_from(f"<{count}{fmt}", data, offset))


_FIXED_WIDTH: dict[int, tuple[str, int]] = {}
for _t in TYPE_UINT32:
    _FIXED_WIDTH[_t] = ("I", 4)
for _t in TYPE_DOUBLE:
    _FIXED_WIDTH[_t] = ("d", 8)
for _t in TYPE_UINT8:
    _FIXED_WIDTH[_t] = ("B", 1)
for _t in TYPE_UINT64:
    _FIXED_WIDTH[_t] = ("Q", 8)
for _t in TYPE_UINT16:
    _FIXED_WIDTH[_t] = ("H", 2)


def _read_strings(data: bytes, offset: int, count: int, path: Path) -> list[str]:
    values = []
    for _ in range(count):
        end = data.find(b"\x00", offset)
        if end == -1:
            raise PmpFormatError(f"Hiányzó string-lezáró (0x00): {path}")
        values.append(data[offset:end].decode("utf-8", errors="replace"))
        offset = end + 1
    return values
