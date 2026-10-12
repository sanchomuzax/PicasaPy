"""Az album „Sort Album By" átrendezése: a kulcsok és az új helyek (#4599).

A kulcsok az eredeti hasonlítójából valók (`docs/specs/album-sorrend.md`
2.4, `0x004efce0` → `0x006b9b50`):

- **Dátum** — a kép metaadat-dátuma (`taken_at`, a felülírással együtt);
  egyenlőségnél a név,
- **Név** — természetes összevetés: a számjegy-sorozat számértékként, az
  ASCII `A–Z` kisbetűsítve, a számjegy-sorozat minden nem-számjegy elé kerül,
- **Méret** — fájlméret,
- **Fordított** — kulcs nélkül, a tárolt sorrendet megfordítja.

Mindhárom kulcs NÖVEKVŐ; a Shift csökkenővé teszi. A rendezés egyszeri
átrendezés: a mód sehol nem tárolódik, csak az eredmény (a helyek).

Tiszta függvények — a lemezt nem érintik.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from .queries import PhotoRecord

SortMode = Literal["date", "name", "size", "reverse"]
SORT_MODES: tuple[str, ...] = ("date", "name", "size", "reverse")

#: A szám-szakasz a nem-számjegy elé kerül (az eredeti `c − 0x100` trükkje).
_DIGITS_RANK = 0
_CHAR_RANK = 1


def natural_name_key(name: str) -> tuple[tuple[int, int], ...]:
    """A név természetes összevetésének kulcsa.

    A számjegy-sorozat számértékként hasonlít, és minden nem-számjegy elé
    kerül; az ASCII `A–Z` kisbetűsítve hasonlít (a nem ASCII karakter
    változatlan kódponttal). A tuple-összevetés az „egyik a másik előtagja"
    esetet is helyesen (a rövidebb elöl) adja.
    """
    key: list[tuple[int, int]] = []
    index = 0
    while index < len(name):
        char = name[index]
        if "0" <= char <= "9":
            end = index
            while end < len(name) and "0" <= name[end] <= "9":
                end += 1
            key.append((_DIGITS_RANK, int(name[index:end])))
            index = end
            continue
        code = ord(char)
        if "A" <= char <= "Z":
            code += 0x20
        key.append((_CHAR_RANK, code))
        index += 1
    return tuple(key)


def _tie_break(photo: PhotoRecord) -> tuple:
    """A teljes rendezés záró kulcsa: a sorrend determinisztikus legyen."""
    return (photo.folder_path, photo.name)


def _sort_key(photo: PhotoRecord, mode: str):
    if mode == "date":
        return (photo.taken_at or "", natural_name_key(photo.name), _tie_break(photo))
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
