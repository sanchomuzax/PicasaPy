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


#: A `*_index.db` szerkezete (#2202, spec `pmp-database.md` 8.2):
#:
#:     float32 verzió (1.6)
#:     4 × [ uint32 darabszám, darabszám × uint32 ]
#:
#: A négy tömb sorrendben: **üres · Checksum · Offset · Size**. A
#: sorrendet a Picasa SAJÁT CSV-kiírója adja meg (`0x006b5e00`, fejléc
#: `Size,Offset,Checksum`), az írót a `0x006b7fc0` + `0x0099c1e0` mutatja
#: (`fwrite(&n,4,1,f)`, majd `fwrite(adat,4,n,f)`).
#:
#: ⚠️ A #2195 első változata `20 bájt fejléc + N × 12` alakban olvasta.
#: Ez MEGDŐLT — és némán: a téves és a helyes modell **bitre ugyanazt a
#: fájlméretet** adja (`4 + 4 + 4·n + 4 + 4·n + 4 + 4·n` = `20 + 12n`),
#: ezért a méret-ellenőrzés átment, a verzió is stimmelt, csak az
#: ÉRTÉKEK voltak szemét. A tanulság a kódban marad: az azonos
#: összméret nem igazol mezőfelosztást.
_SLOT_VERZIO_STRUCT = struct.Struct("<f")
_SLOT_DARAB = struct.Struct("<I")
#: A mért verzió minden mintában.
_SLOT_VERZIO = 1.6
#: A `Size` mező alsó **24 bitje** a valódi méret (`0x006b5eea`:
#: `and edx, 0xFFFFFF`); az író 16 MB fölötti blobot el is utasít
#: (`0x006b75f7`).
_MERET_MASZK = 0xFFFFFF


@dataclass(frozen=True)
class SlotIndexEntry:
    """Egy slot a `thumbs_index.db` / `previews_index.db` / … fájlból."""

    slot: int
    #: A teljes útvonalból számolt ellenőrzőösszeg (spec 8.10).
    checksum: int
    #: A blob kezdete az `<név>_0.db` adatfájlban.
    offset: int
    #: A blob hossza. **0 = ÜRES slot** — nincs mögötte adat.
    size: int

    @property
    def ures(self) -> bool:
        """Üres slot: nincs hozzá blob az adatfájlban."""
        return self.size == 0


def read_slot_index(path: Path) -> tuple[SlotIndexEntry, ...]:
    """A `*_index.db` slot-táblája.

    A slot sorszáma UGYANAZ a tér, mint a PMP-oszlopok sorindexe és a
    `thumbindex.db` rekordsorrendje — a bélyegkép tehát a PMP-sorhoz
    ezen keresztül rendelhető.

    Raises:
        ThumbIndexFormatError: rossz verzió, csonka tömb, vagy ha a fájl
            nem fogy el maradék nélkül. Részlegesen NEM olvasunk: az
            néma féladatot adna.
    """
    data = Path(path).read_bytes()
    if len(data) < _SLOT_VERZIO_STRUCT.size:
        raise ThumbIndexFormatError(f"A fejléc túl rövid: {path}")
    (verzio,) = _SLOT_VERZIO_STRUCT.unpack_from(data, 0)
    if abs(verzio - _SLOT_VERZIO) > 1e-6:
        raise ThumbIndexFormatError(
            f"Váratlan verzió ({verzio!r}, várt {_SLOT_VERZIO}): {path}"
        )

    eltolas = _SLOT_VERZIO_STRUCT.size
    tombok: list[tuple[int, ...]] = []
    for sorszam in range(4):
        if eltolas + _SLOT_DARAB.size > len(data):
            raise ThumbIndexFormatError(
                f"Csonka fájl: a(z) {sorszam}. tömb darabszáma sem fér el: {path}"
            )
        (darab,) = _SLOT_DARAB.unpack_from(data, eltolas)
        eltolas += _SLOT_DARAB.size
        veg = eltolas + darab * 4
        if veg > len(data):
            raise ThumbIndexFormatError(
                f"Csonka {sorszam}. tömb ({darab} elem): {path}"
            )
        tombok.append(struct.unpack_from(f"<{darab}I", data, eltolas))
        eltolas = veg

    if eltolas != len(data):
        raise ThumbIndexFormatError(
            f"A fájl nem fogyott el maradék nélkül: {len(data) - eltolas} "
            f"bájt maradt: {path}"
        )

    _ures, ellenorzo, eltolasok, meretek = tombok
    if not (len(ellenorzo) == len(eltolasok) == len(meretek)):
        raise ThumbIndexFormatError(
            f"A három tömb hossza eltér "
            f"({len(ellenorzo)}/{len(eltolasok)}/{len(meretek)}): {path}"
        )
    return tuple(
        SlotIndexEntry(
            slot=i,
            checksum=ellenorzo[i],
            offset=eltolasok[i],
            size=meretek[i] & _MERET_MASZK,
        )
        for i in range(len(ellenorzo))
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
