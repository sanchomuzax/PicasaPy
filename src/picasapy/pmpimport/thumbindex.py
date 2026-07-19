"""thumbindex.db / thumbs_index.db olvasása (#1): a PMP-rekordok és a
fizikai fájlrendszer (abszolút útvonalak) összerendelése.

Formátum keresztvalidálva (`thumbindex.py` mintaprojekt, ld.
`docs/reference-repos-audit.md`): magic + bejegyzésszám fejléc, utána
soronként név + 26 ismeretlen bájt + szülőindex. A leghosszabb PMP-oszlop
hossza mindig megegyezik a thumbindex bejegyzésszámával — ez adja a
logikai táblák sor-számát (sparse oszlopoknál a hiányzó indexek üresek).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

_MAGIC = 0x40466666
_HEADER = struct.Struct("<II")
_UNKNOWN_BYTES = 26
_NO_PARENT = 0xFFFFFFFF
_TERMINATORS = (0x00, 0xFF)


class ThumbIndexFormatError(ValueError):
    """Érvénytelen vagy sérült thumbindex fejléc/bejegyzés."""


@dataclass(frozen=True)
class ThumbIndexEntry:
    index: int
    name: str
    parent_index: int

    @property
    def is_directory(self) -> bool:
        """`parent_index == 0xffffffff`: a bejegyzés maga egy könyvtár."""
        return self.parent_index == _NO_PARENT

    @property
    def is_face_record(self) -> bool:
        """Üres név + érvényes szülőindex = arc-rekord a szülőképhez."""
        return self.name == "" and not self.is_directory


def read_thumb_index(path: Path) -> tuple[ThumbIndexEntry, ...]:
    """A teljes thumbindex beolvasása.

    Raises:
        ThumbIndexFormatError: Érvénytelen magic, hiányzó névterminátor,
            vagy csonka bejegyzés a jelzett bejegyzésszámhoz képest.
    """
    data = Path(path).read_bytes()
    if len(data) < _HEADER.size:
        raise ThumbIndexFormatError(f"A fejléc túl rövid: {path}")
    magic, count = _HEADER.unpack_from(data, 0)
    if magic != _MAGIC:
        raise ThumbIndexFormatError(f"Érvénytelen magic ({magic:#x}): {path}")

    entries = []
    offset = _HEADER.size
    for index in range(count):
        terminator = _find_terminator(data, offset, path)
        name = data[offset:terminator].decode("utf-8", errors="replace")
        offset = terminator + 1 + _UNKNOWN_BYTES
        end = offset + 4
        if end > len(data):
            raise ThumbIndexFormatError(f"Csonka bejegyzés (#{index}): {path}")
        (parent_index,) = struct.unpack_from("<I", data, offset)
        entries.append(
            ThumbIndexEntry(index=index, name=name, parent_index=parent_index)
        )
        offset = end
    return tuple(entries)


def resolve_path(entries: tuple[ThumbIndexEntry, ...], entry: ThumbIndexEntry) -> str:
    """A bejegyzés teljes (Windows-formátumú) útvonala.

    Könyvtár-bejegyzésnél a név már a teljes abszolút útvonal; fájl-
    bejegyzésnél a szülő (könyvtár) neve + a saját (fájl-) név.
    """
    if entry.is_directory:
        return entry.name
    parent = entries[entry.parent_index]
    if parent.name.endswith(("\\", "/")):
        return parent.name + entry.name
    return parent.name + "\\" + entry.name


def _find_terminator(data: bytes, start: int, path: Path) -> int:
    position = start
    length = len(data)
    while position < length and data[position] not in _TERMINATORS:
        position += 1
    if position >= length:
        raise ThumbIndexFormatError(f"Hiányzó névterminátor: {path}")
    return position
