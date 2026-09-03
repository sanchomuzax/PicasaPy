"""thumbindex.db / thumbs_index.db olvasása (#1): a PMP-rekordok és a
fizikai fájlrendszer (abszolút útvonalak) összerendelése.

Formátum keresztvalidálva (`thumbindex.py` mintaprojekt, ld.
`docs/reference-repos-audit.md`): magic + bejegyzésszám fejléc, utána
soronként név + 26 ismeretlen bájt + szülőindex. A leghosszabb PMP-oszlop
hossza mindig megegyezik a thumbindex bejegyzésszámával — ez adja a
logikai táblák sor-számát (sparse oszlopoknál a hiányzó indexek üresek).
"""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_MAGIC = 0x40466666
_HEADER = struct.Struct("<II")
#: A név utáni farok: a 26 korábban ISMERETLEN bájt + a szülőindex.
#: A mezőket a #2195 mérte ki (`docs/specs/pmp-database.md` 8.):
#: `uint64` létrehozás- és hozzáférés-FILETIME, `uint32` méret,
#: `uint32` típus, `uint8` piszkos, `uint8` érvényes, `uint32` szülő.
_FAROK = struct.Struct("<QQIIBBI")
_NO_PARENT = 0xFFFFFFFF
_TERMINATORS = (0x00, 0xFF)


class ThumbIndexFormatError(ValueError):
    """Érvénytelen vagy sérült thumbindex fejléc/bejegyzés."""


@dataclass(frozen=True)
class ThumbIndexEntry:
    index: int
    name: str
    parent_index: int
    #: #2195: a korábban ismeretlen 26 bájt kiolvasva. A mezőnevek a
    #: Picasa saját diagnosztikai CSV-fejlécéből valók
    #: (`Name, Creation Time, Access Time, Size, Type, Dirty, Valid`).
    #: FILETIME = 100 ns-os egységek 1601-01-01 óta.
    creation_filetime: int = 0
    access_filetime: int = 0
    size: int = 0
    #: Mérve a tulajdonos katalógusán: 1 és 5 = könyvtár, 2 = fájl;
    #: emellett 0, 6 és 10 is előfordul. A teljes értékkészlet a #2195
    #: szerint hatókörön kívül — az importhoz ennyi elég.
    kind: int = 0
    dirty: int = 0
    valid: int = 0

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
        name = _decode(data[offset:terminator], path)
        offset = terminator + 1
        end = offset + _FAROK.size
        if end > len(data):
            raise ThumbIndexFormatError(f"Csonka bejegyzés (#{index}): {path}")
        (
            creation,
            access,
            size,
            kind,
            dirty,
            valid,
            parent_index,
        ) = _FAROK.unpack_from(data, offset)
        entries.append(
            ThumbIndexEntry(
                index=index,
                name=name,
                parent_index=parent_index,
                creation_filetime=creation,
                access_filetime=access,
                size=size,
                kind=kind,
                dirty=dirty,
                valid=valid,
            )
        )
        offset = end
    return tuple(entries)


#: A `*_index.db` fejléce: `float32` verzió, két nulla `uint32`,
#: `uint32` slotszám, két további nulla `uint32` — összesen 20 bájt.
_SLOT_FEJLEC = struct.Struct("<fIIII")
#: Slotonként `uint64` kulcs + `uint32` érték.
_SLOT_REKORD = struct.Struct("<QI")
#: A mért verzió minden mintában (`docs/specs/pmp-database.md` 8.).
_SLOT_VERZIO = 1.6


@dataclass(frozen=True)
class SlotIndexEntry:
    """Egy slot a `thumbs_index.db` / `previews_index.db` / … fájlból."""

    slot: int
    #: A `q` kulcs. A KÉPZÉSE nyitott kérdés (#2195, spec 8.3–8.4) — az
    #: importhoz nem kell, ezért nyersen adjuk tovább.
    key: int
    value: int


def read_slot_index(path: Path) -> tuple[SlotIndexEntry, ...]:
    """A `*_index.db` slot-táblája.

    A slot-index sorszáma UGYANAZ a tér, mint a PMP-oszlopok sorindexe és
    a `thumbindex.db` rekordsorrendje — a bélyegkép tehát a PMP-sorhoz
    ezen keresztül rendelhető.

    Raises:
        ThumbIndexFormatError: rossz verzió, vagy ha a fájlméret nem
            pontosan `20 + slotszám × 12`. A csonka fájlt NEM olvassuk
            részlegesen: az néma féladatot adna.
    """
    data = Path(path).read_bytes()
    if len(data) < _SLOT_FEJLEC.size:
        raise ThumbIndexFormatError(f"A fejléc túl rövid: {path}")
    verzio, _nulla1, slotszam, _nulla2, _nulla3 = _SLOT_FEJLEC.unpack_from(data, 0)
    if abs(verzio - _SLOT_VERZIO) > 1e-6:
        raise ThumbIndexFormatError(
            f"Váratlan verzió ({verzio!r}, várt {_SLOT_VERZIO}): {path}"
        )
    varhato = _SLOT_FEJLEC.size + slotszam * _SLOT_REKORD.size
    if len(data) != varhato:
        raise ThumbIndexFormatError(
            f"A fájlméret nem egyezik a fejléccel: {len(data)} bájt, "
            f"várt {varhato} ({slotszam} slot × {_SLOT_REKORD.size} + "
            f"{_SLOT_FEJLEC.size}): {path}"
        )
    return tuple(
        SlotIndexEntry(slot=i, key=kulcs, value=ertek)
        for i, (kulcs, ertek) in enumerate(
            _SLOT_REKORD.unpack_from(data, _SLOT_FEJLEC.size + i * _SLOT_REKORD.size)
            for i in range(slotszam)
        )
    )


def resolve_path(entries: tuple[ThumbIndexEntry, ...], entry: ThumbIndexEntry) -> str:
    """A bejegyzés teljes (Windows-formátumú) útvonala.

    Könyvtár-bejegyzésnél a név már a teljes abszolút útvonal; fájl-
    bejegyzésnél a szülő (könyvtár) neve + a saját (fájl-) név.

    Raises:
        ThumbIndexFormatError: Ha a `parent_index` a bejegyzések tömbjén
            kívülre mutat (sérült db3).
    """
    if entry.is_directory:
        return entry.name
    if entry.parent_index >= len(entries):
        raise ThumbIndexFormatError(
            f"Érvénytelen szülőindex ({entry.parent_index}) a(z) "
            f"{entry.index}. bejegyzésnél (csak {len(entries)} bejegyzés van)"
        )
    parent = entries[entry.parent_index]
    if parent.name.endswith(("\\", "/")):
        return parent.name + entry.name
    return parent.name + "\\" + entry.name


def _decode(raw: bytes, path: Path) -> str:
    """UTF-8 dekódolás; nem-UTF-8 fájlnévnél naplózott figyelmeztetéssel
    esik vissza `errors="replace"`-re — a hibás bájtok némán ne vesszenek
    el nyomtalanul."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning(
            "Nem UTF-8 fájlnév a(z) %s thumbindexben — a nem dekódolható "
            "bájtok helyettesítő karakterrel (U+FFFD) kerülnek be: %r",
            path,
            raw,
        )
        return raw.decode("utf-8", errors="replace")


def _find_terminator(data: bytes, start: int, path: Path) -> int:
    position = start
    length = len(data)
    while position < length and data[position] not in _TERMINATORS:
        position += 1
    if position >= length:
        raise ThumbIndexFormatError(f"Hiányzó névterminátor: {path}")
    return position
