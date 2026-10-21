"""Az album „Sort Album By" átrendezése: a kulcsok és az új helyek (#4599).

A kulcsok az eredeti hasonlítójából valók (`docs/specs/album-sorrend.md`
2.4, `0x004efce0` → `0x006b9b50`):

- **Dátum** — a kép metaadat-dátuma (`taken_at`, a felülírással együtt); ennek
  hiányában a BEFAGYASZTOTT fájlidő (`photo_date.datum_kulcs`, a mappa-rendezés
  közös kulcsa); egyenlőségnél a név,
- **Név**: természetes összevetés UTF-8 bájtokon: a számjegy-sorozat 32 bites
  előjel nélküli számként körbefordul, az ASCII `A-Z` kisbetűsödik, a többi
  bájt kulcsa az előjeles bájtérték mínusz `0x100`,
- **Méret** — fájlméret,
- **Fordított** — kulcs nélkül, a tárolt sorrendet megfordítja.

Mindhárom kulcs NÖVEKVŐ; a Shift csökkenővé teszi. A rendezés egyszeri
átrendezés: a mód sehol nem tárolódik, csak az eredmény (a helyek).

Tiszta függvények — a lemezt nem érintik.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from .photo_date import datum_kulcs
from .queries import PhotoRecord

SortMode = Literal["date", "name", "size", "reverse"]
SORT_MODES: tuple[str, ...] = ("date", "name", "size", "reverse")


def natural_name_key(name: str) -> tuple[int, ...]:
    """A név természetes összevetésének kulcsa.

    Az eredeti Picasa kódútjának megfelelően UTF-8 bájtokat hasonlít: a
    számjegy-sorozat értéke előjel nélküli 32 biten körbefordul, az ASCII
    `A-Z` kisbetűsödik, a többi bájt kulcsa pedig az előjeles bájtérték mínusz
    `0x100` (32 bites előjel nélküli alakban). A tuple-összevetés a közös
    előtag utáni folytatást és a rövidebb név előresorolását is megőrzi.
    """
    key: list[int] = []
    encoded = name.encode("utf-8")
    index = 0
    while index < len(encoded):
        byte = encoded[index]
        if 0x30 <= byte <= 0x39:
            number = 0
            while index < len(encoded) and 0x30 <= encoded[index] <= 0x39:
                number = (number * 10 + encoded[index] - 0x30) & 0xFFFFFFFF
                index += 1
            key.append(number)
            continue
        if 0x41 <= byte <= 0x5A:
            byte += 0x20
        signed_byte = byte if byte < 0x80 else byte - 0x100
        key.append((signed_byte - 0x100) & 0xFFFFFFFF)
        index += 1
    return tuple(key)


def _tie_break(photo: PhotoRecord) -> tuple:
    """A teljes rendezés záró kulcsa: a sorrend determinisztikus legyen."""
    return (photo.folder_path, photo.name)


def _sort_key(photo: PhotoRecord, mode: str):
    if mode == "date":
        return (datum_kulcs(photo), natural_name_key(photo.name), _tie_break(photo))
    if mode == "name":
        return (natural_name_key(photo.name), _tie_break(photo))
    if mode == "size":
        return (photo.size, _tie_break(photo))
    raise ValueError(f"ismeretlen albumrendezési mód: {mode!r}")


def sorted_album(
    photos: Sequence[PhotoRecord], mode: str, *, descending: bool = False
) -> list[PhotoRecord]:
    """Az album képei az új sorrendben.

    `photos`: a TÁROLT sorrend (az `album_photos` kimenete). A „reverse" mód
    ezt fordítja meg (a Shift-nek itt nincs jelentése: az eredeti kezelő
    is 0-t ad át neki); a másik három a kulcs szerint rendez, `descending`
    esetén csökkenően.
    """
    if mode == "reverse":
        return list(reversed(photos))
    ordered = sorted(photos, key=lambda photo: _sort_key(photo, mode))
    if descending:
        ordered.reverse()
    return ordered


def new_places(ordered: Sequence[PhotoRecord]) -> dict[tuple[str, str], float]:
    """A rendezett lista helyei: `1.0 … n`, (mappa útvonala, fájlnév) kulccsal."""
    return {
        (photo.folder_path, photo.name): float(position)
        for position, photo in enumerate(ordered, start=1)
    }
