"""thumbindex.db olvasó: PMP-rekordindex ↔ fájlrendszer-útvonal megfeleltetés.

Spec: docs/reference-repos-audit.md — fejléc (magic + bejegyzésszám), majd
bejegyzésenként null- vagy 0xff-terminált név, 26 ismeretlen bájt és uint32
szülőindex. A bejegyzés sorszáma azonos az imagedata sorindexével (1:1,
valódi db3-on igazolva: docs/specs/pmp-database.md).
"""

from __future__ import annotations

import enum
import struct
from dataclasses import dataclass
from pathlib import Path

from .pmp import PmpFormatError

THUMBINDEX_MAGIC = 0x40466666
_NO_PARENT = 0xFFFFFFFF
_TERMINATORS = (0x00, 0xFF)
_UNKNOWN_TAIL = 26
_PARENT = struct.Struct("<I")


class EntryKind(enum.Enum):
    """A thumbindex-bejegyzés szerepe."""

    FOLDER = "folder"  # név = abszolút mappaútvonal, nincs szülő
    FILE = "file"  # név = fájlnév, szülő = mappa-bejegyzés
    FACE = "face"  # üres név, érvényes szülő (arc-rekord a szülőképhez)
    DELETED = "deleted"  # üres név, nincs szülő


@dataclass(frozen=True)
class ThumbIndexEntry:
    """Egy bejegyzés: név + szülőindex (None = nincs szülő)."""

    name: str
    parent: int | None

    @property
    def kind(self) -> EntryKind:
        if self.name:
            return EntryKind.FOLDER if self.parent is None else EntryKind.FILE
        return EntryKind.DELETED if self.parent is None else EntryKind.FACE


@dataclass(frozen=True)
class ThumbIndex:
    """A teljes index; a bejegyzés-sorszám a PMP-táblák sorindexe."""

    entries: tuple[ThumbIndexEntry, ...]

    def path_of(self, index: int) -> str | None:
        """A bejegyzés eredeti (Windows-os) útvonala; töröltnél None.

        Arc-bejegyzésnél a szülőkép útvonalát adja vissza.
        """
        entry = self.entries[index]
        if entry.kind is EntryKind.DELETED:
            return None
        if entry.kind is EntryKind.FACE:
            return self.path_of(entry.parent)  # type: ignore[arg-type]
        if entry.parent is None:
            return entry.name
        parent_path = self.entries[entry.parent].name
        return parent_path + entry.name


def parse_thumbindex(data: bytes) -> ThumbIndex:
    """thumbindex.db bájtjainak dekódolása, indexhatár-ellenőrzéssel."""
    if len(data) < 8:
        raise PmpFormatError("thumbindex: csonka fejléc")
    magic, count = struct.unpack_from("<II", data)
    if magic != THUMBINDEX_MAGIC:
        raise PmpFormatError(f"thumbindex: hibás magic: {magic:#010x}")
    entries: list[ThumbIndexEntry] = []
    offset = 8
    for i in range(count):
        name, offset = _read_name(data, offset, i)
        offset += _UNKNOWN_TAIL
        if offset + _PARENT.size > len(data):
            raise PmpFormatError(f"thumbindex: csonka bejegyzés ({i}. sorszám)")
        (raw_parent,) = _PARENT.unpack_from(data, offset)
        offset += _PARENT.size
        parent = None if raw_parent == _NO_PARENT else raw_parent
        if parent is not None and parent >= count:
            raise PmpFormatError(
                f"thumbindex: szülőindex a tartományon kívül ({i}. sorszám: {parent})"
            )
        entries.append(ThumbIndexEntry(name=name, parent=parent))
    return ThumbIndex(entries=tuple(entries))


def read_thumbindex(path: Path) -> ThumbIndex:
    """thumbindex.db beolvasása fájlból."""
    return parse_thumbindex(path.read_bytes())


def _read_name(data: bytes, offset: int, index: int) -> tuple[str, int]:
    end = offset
    while end < len(data) and data[end] not in _TERMINATORS:
        end += 1
    if end >= len(data):
        raise PmpFormatError(f"thumbindex: lezáratlan név ({index}. sorszám)")
    return data[offset:end].decode("utf-8"), end + 1
