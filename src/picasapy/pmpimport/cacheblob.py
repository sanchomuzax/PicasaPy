"""A Picasa bélyegkép-gyorstárának TARTALMA — a `<név>_0.db` blobjai (#1446).

## Mit nyit meg

A `db3` mappában öt gyorstár él, mindegyik egy **index** + egy **adat**
fájlpárként:

| tár | mit tartalmaz |
|---|---|
| `thumbs` | 144 képpontos bélyegkép (JPEG) |
| `thumbs2` | 72 képpontos bélyegkép (JPEG) |
| `previews` | nagyobb előnézet |
| `bigthumbs` | a legnagyobb gyorstárazott szint |
| `facetemplatesV2` | arcsablon, sloton­ként állandó 1 044 bájt |

Az **indexet** a `thumbindex.read_slot_index` olvassa (a `20 + 12n`
elrendezés, #1444/#2195) — ez a modul a párját teszi hozzá: a slotból a
**bájtokat**. Így a felhasználó meglévő Picasa-gyorstárából importkor azonnal
lehet előnézet, újragenerálás nélkül.

⚠️ **Miért nem `cacheindex.py`** (ahogy a #1446 kérte): az index-olvasó
**már megvan** (`thumbindex.read_slot_index`, a #2195 tesztjeivel). Új modult
írni rá két igazságforrást csinálna ugyanabból a formátumból. Ez a modul
ezért csak a hiányzó felet adja.

## A spec két kimondott fenntartása (`docs/specs/pmp-database.md`)

1. a `previews`/`bigthumbs` vektor **hosszabb** lehet a katalógusnál,
2. a `thumbs_index` **rövidebb** is lehet,

⇒ a slot-index sosem feltételezhető érvényesnek: `i < n` ellenőrzés kell.
Ez a modul ezért `None`-t ad ismeretlen slotra, nem dob.

## A „használt-e a slot" próba a HOSSZ, nem a kulcs

Mérve (#1444): az `albums_index.db` 9 slotjának (109–117) érvényes
tartománya van **nulla kulccsal**. A kulcs képzése nincs visszafejtve —
aki rá épít, előbb mérje le.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from picasapy.pmpimport.thumbindex import (
    SlotIndexEntry,
    ThumbIndexFormatError,
    read_slot_index,
)

#: A megnyitható gyorstárak neve. A `profilephotos` szándékosan nincs itt: a
#: mért mintában a `_0.db` mindössze 4 bájt, index nélkül.
CACHE_NEVEK = ("thumbs", "thumbs2", "previews", "bigthumbs", "facetemplatesV2")

#: Az arcsablon mért, ÁLLANDÓ hossza (#1444) — a hívó ezzel ellenőrizhet.
FACETEMPLATE_HOSSZ = 1044


@dataclass(frozen=True)
class CacheStore:
    """Egy gyorstár-pár: az index slotjai + az adatfájl útja."""

    nev: str
    index_path: Path
    data_path: Path
    slots: tuple[SlotIndexEntry, ...]

    def __len__(self) -> int:
        return len(self.slots)

    def hasznalt(self) -> tuple[int, ...]:
        """A NEM üres slotok sorszáma (a hossz alapján, nem a kulcs)."""
        return tuple(s.slot for s in self.slots if not s.ures)

    def slot(self, index: int) -> SlotIndexEntry | None:
        """A slot leírója, vagy `None`, ha a vektoron kívül esik.

        A `i < n` ellenőrzés a spec fenntartása miatt kell: a vektor a
        katalógusnál hosszabb ÉS rövidebb is lehet.
        """
        if index < 0 or index >= len(self.slots):
            return None
        return self.slots[index]

    def blob(self, index: int) -> bytes | None:
        """A sloton tárolt bájtok, vagy `None`, ha nincs (üres/ismeretlen).

        Raises:
            ThumbIndexFormatError: ha a slot tartománya az adatfájlon kívülre
                mutat. Ez nem „nincs adat", hanem **sérült vagy félreolvasott**
                index — némán rövidebb blobot adni rosszabb lenne, mint dobni.
        """
        bejegyzes = self.slot(index)
        if bejegyzes is None or bejegyzes.ures:
            return None
        meret = self.data_path.stat().st_size
        veg = bejegyzes.offset + bejegyzes.size
        if bejegyzes.offset > meret or veg > meret:
            raise ThumbIndexFormatError(
                f"A {self.nev} {index}. slotja az adatfájlon kívülre mutat "
                f"([{bejegyzes.offset}, {veg}), a fájl {meret} bájt)"
            )
        with self.data_path.open("rb") as fh:
            fh.seek(bejegyzes.offset)
            adat = fh.read(bejegyzes.size)
        if len(adat) != bejegyzes.size:
            raise ThumbIndexFormatError(
                f"A {self.nev} {index}. slotjából {len(adat)} bájt jött a várt "
                f"{bejegyzes.size} helyett"
            )
        return adat


def open_cache_store(db3_dir: Path | str, nev: str) -> CacheStore | None:
    """Egy gyorstár megnyitása a `db3` mappából; `None`, ha a pár nincs meg.

    A `None` szándékos: a telepítésenként változó gyorstár-készlet (a
    `docs/specs/pmp-database.md` két mért telepítése is eltér) nem hiba. Ha
    viszont az index MEGVAN, de olvashatatlan, azt a
    `read_slot_index` dobja — azt nem nyeljük el.
    """
    if nev not in CACHE_NEVEK:
        raise ValueError(f"Ismeretlen gyorstár: {nev!r} (ismertek: {CACHE_NEVEK})")
    mappa = Path(db3_dir)
    index_path = mappa / f"{nev}_index.db"
    data_path = mappa / f"{nev}_0.db"
    if not (index_path.is_file() and data_path.is_file()):
        return None
    return CacheStore(
        nev=nev,
        index_path=index_path,
        data_path=data_path,
        slots=read_slot_index(index_path),
    )


__all__ = [
    "CACHE_NEVEK",
    "FACETEMPLATE_HOSSZ",
    "CacheStore",
    "open_cache_store",
]
